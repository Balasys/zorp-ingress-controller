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

    def __init__(self, namespace, ingress_class):

        # The Borg Singleton
        self.__dict__ = self.__shared_state
        self.namespace = namespace
        self.ingress_class = ingress_class

        if not self._api or not self._ext_api:
            self._logger = logging.getLogger('flask.app')

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


    def get_ingresses(self):
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
        ingress_list = self.get_ingresses()
        for ingress in ingress_list:
            annotation = ingress.metadata.annotation
            if "kubernetes.io/ingress.class" in annotation:
                if annotation["kubernetes.io/ingress.class"] == self.ingress_class:
                    ingresses.append(ingress)
                else:
                    self._logger.info("Ignoring ingress that belongs to a different controller class; ingress='%s', class='%s'" % (ingress.name, annotation["kubernetes.io/ingress.class"]))
            else:
                ingresses.append(ingress)
        return ingresses

    def _is_secret_initialized(self):
        try:
            self._get_secret()
        except KubernetesBackendError:
            return False

        return True

    def _init_secret(self):
        secret = client.V1Secret()
        secret.api_version = 'v1'
        secret.metadata = client.V1ObjectMeta()
        secret.metadata.name = 'micado.networksecret'

        try:
            api_response = self._api.create_namespaced_secret('default', secret)
        except Exception as error:
            self._logger.error('Failed to initialize K8S Secret.')
            self._logger.info(error)

            raise KubernetesBackendError()

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

    def _put_secret(self, secret):
        try:
            self._api.replace_namespaced_secret('micado.networksecret', 'default', secret)
        except Exception as error:
            self._logger.error('Failed to update K8S Secret.')
            self._logger.info(error)

            raise KubernetesBackendError()

    def create_secret(self, name, value):
        secret = self._get_secret()

        secret.data[name] = base64.b64encode(value.encode('UTF-8')).decode('ASCII')

        self._put_secret(secret)

    def read_secret(self, name):
        secret = self._get_secret()

        if name not in secret.data:
            raise KubernetesBackendKeyNotFoundError

        return base64.b64decode(secret.data[name])

    def list_secrets(self):
        secret = self._get_secret()

        return secret.data.keys()

    def update_secret(self, name, value):
        secret = self._get_secret()

        if name not in secret.data:
            raise KubernetesBackendKeyNotFoundError

        secret.data[name] = base64.b64encode(value.encode('UTF-8')).decode('ASCII')

        self._put_secret(secret)

    def delete_secret(self, name):
        secret = self._get_secret()

        try:
            del secret.data[name]
        except KeyError:
            pass

        self._put_secret(secret)
