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

    def _getName(self, object):
        name = object.metadata.name
        namespace = object.metadata.namespace
        return "%s/%s" % (name, namespace)

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

    def _get_ingress_spec(self, ingress):
        services = []
        rules = {}
        for rule in ingress.spec.rules:
            paths = {}
            for path in rule.http.paths:
                paths[path.path] = {"service": path.backend.service_name, "port": path.backend.service_port}
                services.append(path.backend.service_name)
            rules[rule.host] = paths
        spec = {"rules": rules}
        if ingress.spec.backend is not None:
            backend_service = ingress.spec.backend.service_name
            backend_port = ingress.spec.backend.service_port
            spec["default"] = {"service": backend_service, "port": backend_port}
            services.append(backend_service)
        spec["services"] = services
        annotations = ingress.metadata.annotations
        if "balasys.hu/zorp-ingress-conf" in annotations:
            spec["annotations"] = annotations["balasys.hu/zorp-ingress-conf"]
        return spec

    def get_relevant_ingresses(self):
        ingresses = {}
        ingress_list = self._get_ingresses()
        for ingress in ingress_list.items:
            annotations = ingress.metadata.annotations
            if "kubernetes.io/ingress.class" in annotations:
                if annotations["kubernetes.io/ingress.class"] == self.ingress_class:
                    ingresses[ingress.metadata.name] = self._get_ingress_spec(ingress)
                else:
                    self._logger.info("Ignoring ingress that belongs to a different controller class; ingress='%s', class='%s'" % (self._getName(ingress), annotations["kubernetes.io/ingress.class"]))
            else:
                ingresses[ingress.metadata.name] = self._get_ingress_spec(ingress)
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
        for ingress in ingresses.values():
            relevant_services.extend(ingress["services"])
        services = {}
        for service in self._get_services().items:
            if service.metadata.name in relevant_services:
                ports = {}
                for port in service.spec.ports:
                    ports[port.protocol] = { port.port: port.target_port }
                services[service.metadata.name] = ports
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
        endpoints = {}
        for endpoint in self._get_endpoints().items:
            if endpoint.metadata.name in services.keys():
                for subset in endpoint.subsets:
                    for address in subset.addresses:
                        for port in subset.ports:
                            name = endpoint.metadata.name
                            if name in endpoints:
                                if port.protocol in endpoints[name]:
                                    endpoints[name][port.protocol].append("%s:%d" % (address.ip, port.port))
                                else:
                                    endpoints[name][port.protocol] = ["%s:%d" % (address.ip, port.port), ]
                            else:
                                endpoints[name] = { port.protocol : ["%s:%d" % (address.ip, port.port), ]}
        return endpoints

    def _get_secret(self):
        try:
            secret = self._api.read_namespaced_secret(self.namespace, 'tls-secret')
        except client.rest.ApiException as api_exception:
            if api_exception.status == 404:
                self._logger.error("Failed to fetch secret; namespace='%s', secret='%s'" % (self.namespace, "tls-secret"))
                return None
            else:
                self._logger.error('Failed to read K8S Secret.')
                self._logger.info(error)
                raise KubernetesBackendError()
        except Exception as error:
            self._logger.error('Failed to read K8S Secret.')
            self._logger.info(error)
            raise KubernetesBackendError()

        if secret.data is None:
            secret.data = {}

        return secret

    def read_secret(self, name):
        secret = self._get_secret()

        if secret is None:
            raise KubernetesBackendKeyNotFoundError
        if name not in secret.data:
            raise KubernetesBackendKeyNotFoundError

        return base64.b64decode(secret.data[name])

    def list_secrets(self):
        secret = self._get_secret()
        if secret is None:
            return []
        return base64.b64decode(secret.data.keys())
