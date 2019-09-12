from apscheduler.schedulers.blocking import BlockingScheduler
import argparse
import logging
import os.path
import subprocess
from .kubernetes_backend import KubernetesBackend


class ZorpConfig():

    def __init__(self, namespace='default', ingress_class='zorp', behaviour='basic', ingresses=None, services=None, endpoints=None, secrets=None):
        self.ingresses = ingresses
        self.services = services
        self.endpoints = endpoints
        self.secrets = secrets
        self.behaviour = behaviour

        self._logger = logging.getLogger('flask.app')
        self._logger.setLevel(logging.getLevelName('INFO'))
        self.k8s = KubernetesBackend(namespace, ingress_class)

        self.has_default_cert = os.path.isfile('/etc/zorp/default-tls.key')

    def generate_self_signed_cert(self):
        self._logger.info("Generating self-signed certificate for default TLS service")
        res = subprocess.Popen(['openssl', 'req', '-new', '-newkey', 'rsa:4096', '-days', '3650', '-sha256', '-nodes', '-x509', '-subj', '/CN=Ingress Default Certificate', '-keyout' '/etc/zorp/default-tls.key', '-out', '/etc/zorp/default-tls.cert'])
        output, error_ = res.communicate()
        if (error_):
            logger.error(error_)

    def generate_config(self):
        if len(self.secrets) == 0 and self.has_default_cert is False and self.behaviour == 'basic':
            self.generate_self_signed_cert()
        f = open("/tmp/k8s-config", "w")
        f.write(str(self.ingresses)+"\n")
        f.write(str(self.services)+"\n")
        f.write(str(self.endpoints)+"\n")
        f.write(str(self.secrets)+"\n")
        f.close()

    def reload_zorp(self):
        res = subprocess.Popen(['/usr/sbin/zorpctl', 'reload'], stdout=subprocess.PIPE)
        output, error_ = res.communicate()
        if (error_):
            logger.error(error_)

    def load_k8s_config(self):
        oldconfig = {'ingresses': self.ingresses, 'services': self.services, 'endpoints': self.endpoints, 'secrets': self.secrets}
        self.ingresses = self.k8s.get_relevant_ingresses()
        self.services = self.k8s.get_relevant_services(self.ingresses)
        self.endpoints = self.k8s.get_relevant_endpoints(self.services)
        self.secrets= {}
        for secret_name in self.k8s.list_secrets():
            self.secrets[secret_name] = self.k8s.get_secret(secretname)
        if (oldconfig['ingresses'] != self.ingresses or oldconfig['services'] != self.services or
                oldconfig['endpoints'] != self.endpoints or oldconfig['secrets'] != self.secrets):
           self.generate_config()
           self.reload_zorp()

def process_k8s_changes(zorpConfig):
    zorpConfig.load_k8s_config()
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Kubernetes Ingress Controller based on Zorp')
    parser.add_argument('--namespace', dest='namespace', default='default',
                    help='the namespace to watch for ingresses')
    parser.add_argument('--ingress.class', dest='ingress_class', default='zorp',
                    help='ingress class types to watch in a multi-ingress environment')
    parser.add_argument('--behaviour', dest='behaviour', default='basic', choices=['basic', 'tosca'],
                    help='chooses if the controller should generate Zorp configuration based on k8s objects or TOSCA syntax annotation')

    args = parser.parse_args()

    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 300
    }

    zorpConfig = ZorpConfig(args.namespace, args.ingress_class, args.behaviour)

    scheduler = BlockingScheduler(job_defaults=job_defaults)
    scheduler.add_job(lambda: process_k8s_changes(zorpConfig), 'interval', seconds=5, jitter=5)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
