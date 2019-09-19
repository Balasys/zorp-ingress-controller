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
        tlsspec = {}
        if ingress.spec.tls is not None:
            for tls in ingress.spec.tls:
                for host in tls.hosts:
                    if host not in tlsspec:
                        tlsspec[host] = tls.secret_name
        spec["tls"] = tlsspec
        if ingress.spec.backend is not None:
            backend_service = ingress.spec.backend.service_name
            backend_port = ingress.spec.backend.service_port
            spec["default"] = {"service": backend_service, "port": backend_port}
            services.append(backend_service)
        spec["services"] = services
        annotations = ingress.metadata.annotations
        if "zorp.ingress.kubernetes.io/conf" in annotations:
            spec["annotations"] = annotations["zorp.ingress.kubernetes.io/conf"]
        return spec

    def _merge_ingress_spec(self, ingresses, ingress):
        if "default" not in ingresses and "default" in ingress:
            ingresses["default"] = ingress["default"]
        if "annotation" not in ingresses and "annotation" in ingress:
            ingresses["annotation"] = ingress["annotation"]
        ingresses["services"].extend(ingress["services"])
        for host in ingress["tls"]:
            if host not in ingresses["tls"]:
                ingresses["tls"][host] = ingress["tls"][host]
        rules = ingress["rules"]
        for host in rules.keys():
            if host in ingresses["rules"]:
                for path in rules[host]:
                    if path not in ingresses["rules"][host]:
                        ingresses["rules"][host][path] = rules[host][path]
            else:
                ingresses["rules"][host] = ingress["rules"][host]

    def get_relevant_ingresses(self):
        ingresses = {'rules' : {}, 'services': [], 'tls': {}}
        ingress_list = self._get_ingresses()
        for ingress in ingress_list.items:
            annotations = ingress.metadata.annotations
            if "kubernetes.io/ingress.class" in annotations:
                if annotations["kubernetes.io/ingress.class"] == self.ingress_class:
                    ingress = self._get_ingress_spec(ingress)
                    self._merge_ingress_spec(ingresses, ingress)
                else:
                    self._logger.info("Ignoring ingress that belongs to a different controller class; ingress='%s', class='%s'" % (self._getName(ingress), annotations["kubernetes.io/ingress.class"]))
            else:
                ingress = self._get_ingress_spec(ingress)
                self._merge_ingress_spec(ingresses, ingress)
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

    def get_relevant_services(self, ingress):
        services = {}
        for service in self._get_services().items:
            if service.metadata.name in ingress["services"]:
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
        tcp_endpoints = {}
        udp_endpoints = {}
        for endpoint in self._get_endpoints().items:
            if endpoint.metadata.name in services.keys():
                for subset in endpoint.subsets:
                    for address in subset.addresses:
                        for port in subset.ports:
                            name = endpoint.metadata.name
                            if port.protocol == "TCP":
                                endpoints = tcp_endpoints
                            else:
                                endpoints = udp_endpoints
                            if port.port in endpoints:
                                if name in endpoints[port.port]:
                                    endpoints[port.port][name].append(address.ip)
                                else:
                                    endpoints[port.port][name] = [address.ip, ]
                            else:
                                endpoints[port.port] = { name : [address.ip, ]}
        return {"TCP": tcp_endpoints, "UDP": udp_endpoints}

    def get_endpoints_from_annotation(self, annotation):
        relevant_ports = []
        for rule in annotation:
            if "ports" in rule:
                relevant_ports.extend(annotation["ports"])

        tcp_endpoints = {}
        udp_endpoints = {}
        for endpoint in self._get_endpoints().items:
            for subset in endpoint.subsets:
                for address in subset.addresses:
                    for port in subset.ports:
                        if port.port in relevant_ports
                            name = endpoint.metadata.name
                            if port.protocol == "TCP":
                                endpoints = tcp_endpoints
                            else:
                                endpoints = udp_endpoints
                            if port.port in endpoints:
                                if name in endpoints[port.port]:
                                    endpoints[port.port][name].append(address.ip)
                                else:
                                    endpoints[port.port][name] = [address.ip, ]
                            else:
                                endpoints[port.port] = { name : [address.ip, ]}
        return {"TCP": tcp_endpoints, "UDP": udp_endpoints}

    def _get_secret(self, namespace=None, name='tls-secret'):
        if namespace is None:
            namespace = self.namespace
        try:
            secret = self._api.read_namespaced_secret(name, namespace)
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

    def read_named_tls_secret(self, namespace, name):
        secret = self._get_secret(namespace, name)

        if secret is None:
            raise KubernetesBackendKeyNotFoundError

        if secret.data is None or ("tls.key" not in secret.data or "tls.crt" not in secret.data):
            raise KubernetesBackendKeyNotFoundError
        cert = base64.b64decode(secret.data["tls.crt"])
        key = base64.b64decode(secret.data["tls.key"])
        return {"tls.crt": cert, "tls.key": key}

    def get_relevant_secrets(self, ingress):
        secrets = {}
        for secretname in ingress["tls"].values():
            secret = self.read_named_tls_secret(self.namespace, secretname)
            secrets[secretname] = secret
        return secrets

    def list_secrets(self):
        secret = self._get_secret()
        if secret is None:
            return []
        return base64.b64decode(secret.data.keys())

    def get_secrets_from_annotation(self, annotation):
        secrets = {}
        for rule in annotation:
            if "encryption_cert" in rule and "encryption_key" in rule:
                secret = self.read_named_tls_secret(self.namespace, rule["encryption_cert"])
                secrets[rule["encryption_cert"]] = secret
        return secrets
