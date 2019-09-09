import argparse
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from .kubernetes_backend import KubernetesBackend


class ZorpConfig():
    def __init__(self, namespace='default', ingress_class='zorp', ingresses=None, services=None, endpoints=None, secrets=None):
        self.ingresses = ingresses
        self.services = services
        self.endpoints = endpoints
        self.secrets = secrets
        self.k8s = KubernetesBackend(namespace, ingress_class)

    def generate_config(self):
        f = open("/tmp/k8s-config", "w")
        f.write(str(self.ingresses)+"\n")
        f.write(str(self.services)+"\n")
        f.write(str(self.endpoints)+"\n")
        f.write(str(self.secrets)+"\n")
        f.close()

    def load_k8s_config(self):
        self.ingresses = self.k8s.get_relevant_ingresses()
        self.services = self.k8s.get_relevant_services(self.ingresses)
        self.endpoints = self.k8s.get_relevant_endpoints(self.services)
        #self.secrets= {}
        #for secret_name in self.k8s.list_secrets():
        #    self.secrets[secret_name] = self.k8s.get_secret(secretname)

def process_k8s_changes(namespace, ingress_class):
    zorpConfig = ZorpConfig(namespace, ingress_class)
    zorpConfig.load_k8s_config()
    zorpConfig.generate_config()
    return

if __name__ == '__main__':

    _logger = logging.getLogger('flask.app')
    _logger.setLevel(logging.getLevelName('INFO'))
    _logger.info("Initializing Zorp Ingress Controller")
    parser = argparse.ArgumentParser(description='Kubernetes Ingress Controller based on Zorp')
    parser.add_argument('--namespace', dest='namespace', default='default',
                    help='the namespace to watch for ingresses')
    parser.add_argument('--ingress.class', dest='ingress_class', default='zorp',
                    help='ingress class types to watch in a multi-ingress environment')

    args = parser.parse_args()

    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 300
    }

    scheduler = BlockingScheduler(job_defaults=job_defaults)
    scheduler.add_job(lambda: process_k8s_changes(args.namespace, args.ingress_class) , 'interval', seconds=5, jitter=5)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
