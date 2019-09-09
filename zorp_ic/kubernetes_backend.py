import logging
import base64
from kubernetes import client, config


class KubernetesBackendError(Exception):
    pass


class KubernetesBackendKeyNotFoundError(Exception):
    pass


class KubernetesBackend:
    # The Borg Singleton
    __shared_state = {}

    _api = None

    def __init__(self, namespace='default', ingress_class='zorp'):

        # The Borg Singleton
        self.__dict__ = self.__shared_state
        self.namespace = namespace
        self.ingress_class = ingress_class

        if not self._api or not self._ext_api:
            self._logger = logging.getLogger('flask.app')
            self._logger.setLevel(logging.getLevelName('INFO'))
            self._logger.info('Initializing Kubernetes Client.')

            config.load_incluster_config()

            self._api = client.CoreV1Api()
            self._ext_api = client.ExtensionsV1beta1Api()

            if self._is_secret_initialized():
                self._logger.info('K8S Secret already initalized.')
            else:
                self._logger.info('Initializing K8S Secret.')

                self._init_secret()

                self._logger.info('K8S Secret initalized.')

    def get_ingress_annotations(self):
        ingress = self._ext_api.read_namespaced_ingress("name", self.namespace)
        annotations = ingress.metadata.annotations
        # spec = ingress.spec

        policy = dict()
        policy['conf'] = annotations['zorpingress']

        return policy

    def get_service_network_config(self):
        pass


    def _get_ingresses(self):
        try:
            api_response = self._ext_api.list_ingress_for_all_namespaces()
        except Exception as error:
            self._logger.error('Failed to list K8S Ingresses.')
            self._logger.info(error)

            raise KubernetesBackendError()

        if api_response.items is None:
            api_response.items = {}

        return api_response

    def get_relevant_ingresses(self):
        ingresses = []
        ingress_list = self._get_ingresses()
        for ingress in ingress_list.items:
            annotations = ingress.metadata.annotations
            if "kubernetes.io/ingress.class" in annotations:
                if annotations["kubernetes.io/ingress.class"] == self.ingress_class:
                    ingresses.append(ingress)
                else:
                    self._logger.info("Ignoring ingress that belongs to a different controller class; ingress='%s', class='%s'" % (ingress.metadata.name, annotations["kubernetes.io/ingress.class"]))
            else:
                ingresses.append(ingress)
        return ingresses

    def _get_services(self):
        try:
            api_response = self._api.list_service_for_all_namespaces()
        except Exception as error:
            self._logger.error('Failed to list K8S Services.')
            self._logger.info(error)

            raise KubernetesBackendError()

        if api_response.items is None:
            api_response.items = {}

        return api_response

    def get_relevant_services(self, ingresses):
        relevant_services = []
        for ingress in ingresses:
            if ingress.spec.backend is not None:
                relevant_services.append(ingress.spec.backend.service_name)
            for rule in ingress.spec.rules:
                for path in rule.http.paths:
                    relevant_services.append(path.backend.service_name)
        services = []
        for service in self._get_services().items:
            if service.metadata.name in relevant_services:
                services.append(service)
        return services

    def _get_endpoints(self):
        try:
            api_response = self._api.list_endpoints_for_all_namespaces()
        except Exception as error:
            self._logger.error('Failed to list K8S Endpoints.')
            self._logger.info(error)

            raise KubernetesBackendError()

        if api_response.items is None:
            api_response.items = {}

        return api_response

    def get_relevant_endpoints(self, services):
        relevant_services = []
        for service in services:
            relevant_services.append(service.metadata.name)
        endpoints = {}
        for endpoint in self._get_endpoints().items:
            if endpoint.metadta.name in relevant_services:
                for subset in endpoint.subsets:
                    for address in subset.addresses:
                        for port in subset.ports:
                            if endpoint.metadata.name in endpoints:
                                if port.protocol in endpoints[endpoint.metadata.name]:
                                    endpoints[endpoint.metadata.name][port.protocol].append("%s:%s" % (address.ip, address.port))
                                else:
                                    endpoints[endpoint.metadata.name][port.protocol] = ["%s:%s" % (address.ip, address.port, ]
                            else:
                                endpoints[endpoint.metadata.name] = { port.protocol : ["%s:%s" % (address.ip, address.port, ]}
        return set(endpoints)

    def _is_secret_initialized(self):
        try:
            self._get_secret()
        except KubernetesBackendError:
            return False

        return True

    def _get_secret(self):
        try:
            secret = self._api.read_namespaced_secret('micado.networksecret', 'default')
        except Exception as error:
            self._logger.error('Failed to read K8S Secret.')
            self._logger.info(error)

            raise KubernetesBackendError()

        if secret.data is None:
            secret.data = {}

        return secret

    def read_secret(self, name):
        secret = self._get_secret()

        if name not in secret.data:
            raise KubernetesBackendKeyNotFoundError

        return base64.b64decode(secret.data[name])

    def list_secrets(self):
        secret = self._get_secret()

        return secret.data.keys()
