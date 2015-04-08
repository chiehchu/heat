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
        KUBERNETES_ENDPOINT, DEFINITION_LOCATION, HOSTNAME, USER, MEMORY, PORT_SPECS,
        PRIVILEGED, TTY, OPEN_STDIN, STDIN_ONCE, ENV, CMD, DNS,
        IMAGE, VOLUMES, VOLUMES_FROM, PORT_BINDINGS, LINKS, NAME, APIVERSION, NAMESPACE,
    ) = (
        'kubernetes_endpoint', 'definition_location', 'hostname', 'user', 'memory', 'port_specs',
        'privileged', 'tty', 'open_stdin', 'stdin_once', 'env', 'cmd', 'dns',
        'image', 'volumes', 'volumes_from', 'port_bindings', 'links', 'name',
        'apiversion', 'namespace',
    )

    ATTRIBUTES = (
        INFO, NETWORK_INFO, NETWORK_IP, NETWORK_GATEWAY,
        NETWORK_TCP_PORTS, NETWORK_UDP_PORTS, LOGS, LOGS_HEAD,
        LOGS_TAIL,
    ) = (
        'info', 'network_info', 'network_ip', 'network_gateway',
        'network_tcp_ports', 'network_udp_ports', 'logs', 'logs_head',
        'logs_tail',
    )

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
        HOSTNAME: properties.Schema(
            properties.Schema.STRING,
            _('Hostname of the container.'),
            default=''
        ),
        USER: properties.Schema(
            properties.Schema.STRING,
            _('Username or UID.'),
            default=''
        ),
        MEMORY: properties.Schema(
            properties.Schema.INTEGER,
            _('Memory limit (Bytes).'),
            default=0
        ),
        PORT_SPECS: properties.Schema(
            properties.Schema.LIST,
            _('TCP/UDP ports mapping.'),
            default=None
        ),
        PORT_BINDINGS: properties.Schema(
            properties.Schema.MAP,
            _('TCP/UDP ports bindings.'),
        ),
        LINKS: properties.Schema(
            properties.Schema.MAP,
            _('Links to other containers.'),
        ),
        NAME: properties.Schema(
            properties.Schema.STRING,
            _('Name of the container.'),
        ),
        PRIVILEGED: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Enable extended privileges.'),
            default=False
        ),
        TTY: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Allocate a pseudo-tty.'),
            default=False
        ),
        OPEN_STDIN: properties.Schema(
            properties.Schema.BOOLEAN,
            _('Open stdin.'),
            default=False
        ),
        STDIN_ONCE: properties.Schema(
            properties.Schema.BOOLEAN,
            _('If true, close stdin after the 1 attached client disconnects.'),
            default=False
        ),
        ENV: properties.Schema(
            properties.Schema.LIST,
            _('Set environment variables.'),
        ),
        CMD: properties.Schema(
            properties.Schema.LIST,
            _('Command to run after spawning the container.'),
            default=[]
        ),
        DNS: properties.Schema(
            properties.Schema.LIST,
            _('Set custom dns servers.'),
        ),
        IMAGE: properties.Schema(
            properties.Schema.STRING,
            _('Image name.')
        ),
        VOLUMES: properties.Schema(
            properties.Schema.MAP,
            _('Create a bind mount.'),
            default={}
        ),
        VOLUMES_FROM: properties.Schema(
            properties.Schema.LIST,
            _('Mount all specified volumes.'),
            default=''
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

    attributes_schema = {
        INFO: attributes.Schema(
            _('Container info.')
        ),
        NETWORK_INFO: attributes.Schema(
            _('Container network info.')
        ),
        NETWORK_IP: attributes.Schema(
            _('Container ip address.')
        ),
        NETWORK_GATEWAY: attributes.Schema(
            _('Container ip gateway.')
        ),
        NETWORK_TCP_PORTS: attributes.Schema(
            _('Container TCP ports.')
        ),
        NETWORK_UDP_PORTS: attributes.Schema(
            _('Container UDP ports.')
        ),
        LOGS: attributes.Schema(
            _('Container logs.')
        ),
        LOGS_HEAD: attributes.Schema(
            _('Container first logs line.')
        ),
        LOGS_TAIL: attributes.Schema(
            _('Container last logs line.')
        ),
    }

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

    #def _parse_networkinfo_ports(self, networkinfo):
        #tcp = []
        #udp = []
        #for port, info in six.iteritems(networkinfo['Ports']):
            #p = port.split('/')
            #if not info or len(p) != 2 or 'HostPort' not in info[0]:
                #continue
            #port = info[0]['HostPort']
            #if p[1] == 'tcp':
                #tcp.append(port)
            #elif p[1] == 'udp':
                #udp.append(port)
        #return (','.join(tcp), ','.join(udp))

    #def _container_networkinfo(self, client, resource_id):
        #info = client.inspect_container(self.resource_id)
        #networkinfo = info['NetworkSettings']
        #ports = self._parse_networkinfo_ports(networkinfo)
        #networkinfo['TcpPorts'] = ports[0]
        #networkinfo['UdpPorts'] = ports[1]
        #return networkinfo

    def _resolve_attribute(self, name):
        if not self.resource_id:
            return
        #if name == 'info':
            #client = self.get_client()
            #return client.inspect_container(self.resource_id)
        #if name == 'network_info':
            #client = self.get_client()
            #networkinfo = self._container_networkinfo(client, self.resource_id)
            #return networkinfo
        #if name == 'network_ip':
            #client = self.get_client()
            #networkinfo = self._container_networkinfo(client, self.resource_id)
            #return networkinfo['IPAddress']
        #if name == 'network_gateway':
            #client = self.get_client()
            #networkinfo = self._container_networkinfo(client, self.resource_id)
            #return networkinfo['Gateway']
        #if name == 'network_tcp_ports':
            #client = self.get_client()
            #networkinfo = self._container_networkinfo(client, self.resource_id)
            #return networkinfo['TcpPorts']
        #if name == 'network_udp_ports':
            #client = self.get_client()
            #networkinfo = self._container_networkinfo(client, self.resource_id)
            #return networkinfo['UdpPorts']
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

    #def handle_suspend(self):
        #if not self.resource_id:
            #return
        #client = self.get_client()
        #client.stop(self.resource_id)
        #return self.resource_id

    #def check_suspend_complete(self, rc_name):
        #status = self._get_container_status(rc_name)
        #return (not status['Running'])

    #def handle_resume(self):
        #if not self.resource_id:
            #return
        #client = self.get_client()
        #client.start(self.resource_id)
        #return self.resource_id

    #def check_resume_complete(self, rc_name):
        #status = self._get_container_status(rc_name)
        #return status['Running']


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
