#
# Copyright (c) 2015 NDPMedia, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import six

from heat.common.i18n import _
from heat.engine import attributes
from heat.engine import properties
from heat.engine import resource
from heat.openstack.common import log as logging

LOG = logging.getLogger(__name__)

KUBERNETES_INSTALLED = False
# conditionally import so tests can work without having the dependency
# satisfied
try:
    import kubernetes
    from kubernetes import KubernetesError
    KUBERNETES_INSTALLED = True
except ImportError:
    kubernetes = None


class KubernetesReplicationController(resource.Resource):

    PROPERTIES = (
        KUBERNETES_ENDPOINT, DEFINITION_LOCATION,NAME, APIVERSION, NAMESPACE,
    ) = (
        'kubernetes_endpoint', 'definition_location', 'name',
        'apiversion', 'namespace',
    )

    #ATTRIBUTES = (
        #INFO, NETWORK_INFO, NETWORK_IP, NETWORK_GATEWAY,
        #NETWORK_TCP_PORTS, NETWORK_UDP_PORTS, LOGS, LOGS_HEAD,
        #LOGS_TAIL,
    #) = (
        #'info', 'network_info', 'network_ip', 'network_gateway',
        #'network_tcp_ports', 'network_udp_ports', 'logs', 'logs_head',
        #'logs_tail',
    #)

    properties_schema = {
        KUBERNETES_ENDPOINT: properties.Schema(
            properties.Schema.STRING,
            _('Kubernetes daemon endpoint (by default the local kubernetes daemon '
              'will be used).'),
            default='127.0.0.1:8080'
        ),
        DEFINITION_LOCATION: properties.Schema(
            properties.Schema.STRING,
            _('Location where the defintion of ReplicationController is located.'),
            default=''
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the container.'),
        ),
        APIVERSION: properties.Schema(
            properties.Schema.STRING,
            _('API Version of Kubernetes, by default is v1beta3.'),
            default='v1beta3'
        ),
        NAMESPACE: properties.Schema(
            properties.Schema.STRING,
            _('Namespace of current ReplicationController, default is default.'),
            default='default'
        ),
    }

    #attributes_schema = {
        #LOGS: attributes.Schema(
            #_('Container logs.')
        #),
        #LOGS_HEAD: attributes.Schema(
            #_('Container first logs line.')
        #),
        #LOGS_TAIL: attributes.Schema(
            #_('Container last logs line.')
        #),
    #}

    def __init__(self, name, definition, stack):
        self.labels = {}
        super(KubernetesReplicationController, self).__init__(name, definition, stack)

    def get_client(self):
        client = None
        if KUBERNETES_INSTALLED:
            base_url = ('http://%s/api/%s' %
                        (self.properties.get(self.KUBERNETES_ENDPOINT),
                         self.properties.get(self.APIVERSION)))
            client = kubernetes.Api(base_url=base_url)
        return client

    def _resolve_attribute(self, name):
        if not self.resource_id:
            return
        #if name == 'logs':
            #client = self.get_client()
            #logs = client.logs(self.resource_id)
            #return logs
        #if name == 'logs_head':
            #client = self.get_client()
            #logs = client.logs(self.resource_id)
            #return logs.split('\n')[0]
        #if name == 'logs_tail':
            #client = self.get_client()
            #logs = client.logs(self.resource_id)
            #return logs.split('\n').pop()

    def _read_definition(self, path):
        file_obj = open(path)
        content = None
        try:
            content = file_obj.read()
        finally:
            file_obj.close()
            return content

    def _is_pod_running(self, pod):
        return pod.Status.Phase == "Running"

    def handle_create(self):
        client = self.get_client()
        content = self._read_definition(self.properties[self.DEFINITION_LOCATION])
        result = client.CreateReplicationController(content, self.properties[self.NAMESPACE])
        rc_name = result.Name
        self.labels = result.Labels
        self.resource_id_set(rc_name)
        return rc_name

    def check_create_complete(self, rc_name):
        client = self.get_client()
        #get the replicationcontroller by given name
        rc = client.GetReplicationController(name=rc_name, namespace=self.properties[self.NAMESPACE])
        #check whether the current state equals with desired state
        if rc.DesiredState > rc.CurrentState:
            return False
        #get all pods which are labeled by the given rc first
        pod_list = client.GetPods(namespace=self.properties[self.NAMESPACE], selector=rc.Labels.get('name'))
        if len(pod_list.Items) < rc.DesiredState:
            return False
        for pod in pod_list.Items:
            if not self._is_pod_running(pod):
                return False
        # The boolean is specified here
        return True

    def handle_delete(self):
        if self.resource_id is None:
            return
        client = self.get_client()
        #resize replicationcontroller to 0 first
        try:
            client.ResizeReplicationController(name=self.resource_id, replicas=0,
                                               namespace=self.properties[self.NAMESPACE])
        except KubernetesError, e:
            LOG.warn(_("handle_delete: ResizeReplicationController got error with message <%s>"
                       "will retry again later" % e.message))
        return self.resource_id

    def check_delete_complete(self, rc_name):
        if rc_name is None:
            return True
        #check if the current rc still has any pod
        client = self.get_client()
        rc = client.GetReplicationController(name=rc_name, namespace=self.properties[self.NAMESPACE])
        if not rc:
            return True
        pod_list = client.GetPods(namespace=self.properties[self.NAMESPACE], selector=rc.Labels.get('name'))
        if pod_list.Items and len(pod_list.Items):
            try:
                client.ResizeReplicationController(name=rc_name, replicas=0,
                                                   namespace=self.properties[self.NAMESPACE])
            except KubernetesError, e:
                LOG.warn(_("check_delete_complete:ResizeReplicationController got error with message <%s>"
                           "will retry again later" % e.message))
            return False
        #delete rc if no pods anymore
        client.DeleteReplicationController(name=rc_name, namespace=self.properties[self.NAMESPACE])
        return True

def resource_mapping():
    return {
        'GoogleInc::Kubernetes::ReplicationController': KubernetesReplicationController,
    }


def available_resource_mapping():
    if KUBERNETES_INSTALLED:
        return resource_mapping()
    else:
        LOG.warn(_("Kubernetes plug-in loaded, but kubernetes lib not installed."))
        return {}
