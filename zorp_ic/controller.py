from apscheduler.schedulers.blocking import BlockingScheduler
import argparse
from copy import deepcopy
from jinja2 import Environment, PackageLoader
import logging
import os
import os.path
import shutil
import subprocess
import sys

from .kubernetes_backend import KubernetesBackend


class ZorpConfigGenerator(object):
    def __init__(self, templatedir):
        super(ZorpConfigGenerator, self).__init__()
        self.env = Environment(
            loader=PackageLoader('zorp_ic', 'templates'),
            trim_blocks=True,
            lstrip_blocks=True,
            extensions=['jinja2.ext.do']
        )

    def renderTemplate(self, template, data, conf={'dst': '/etc/zorp/policy.py', 'mode': 644, 'owner': 'zorp', 'group': 'zorp'}):
        mode = int(str(conf.get('mode', '644')), 8)
        owner = conf.get('owner', None)
        group = conf.get('group', None)
        try:
            t = self.env.get_template(template)
        except IOError as e:
            sys.exit("Error opening template file: %s" % e)
        confdir = os.path.dirname(conf['dst'])
        if not os.path.exists(confdir):
            try:
                Path(confdir).mkdir(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH, parents=True)
            except (IOError, FileExistsError, OSError) as e:
                sys.exit("Error creating %s: %s" % (confdir, e))
            if owner or group:
                shutil.chown(confdir, user=owner, group=group)
        try:
            rendered = t.render(conf=data, env=os.environ)
        except BaseException as e:
            sys.exit("Error rendering template: %s" % e)
        try:
            with open(conf['dst'], 'w') as outfile:
                outfile.write(rendered)
        except IOError as e:
            sys.exit("Error writing to destination file: %s" % e)
        os.chmod(conf['dst'], mode)
        if owner or group:
            shutil.chown(conf['dst'], user=owner, group=group)

class ZorpConfig(object):

    config = {}

    def __init__(self, namespace='default', ingress_class='zorp', behaviour='basic', ingress=None, services=None, endpoints=None, secrets=None):
        self.config["ingress"] = ingress
        self.config["services"] = services
        self.config["endpoints"] = endpoints
        self.config["secrets"] = secrets
        self.behaviour = behaviour

        self._logger = logging.getLogger('flask.app')
        self._logger.setLevel(logging.getLevelName('INFO'))
        self.k8s = KubernetesBackend(namespace, ingress_class)

        self.has_default_cert = os.path.isfile('/etc/zorp/tls.key')

    def generate_self_signed_cert(self):
        self._logger.error("Generating self-signed certificate for default TLS service")
        res = subprocess.Popen(['openssl', 'req', '-new', '-newkey', 'rsa:4096', '-days', '3650', '-sha256', '-nodes', '-x509', '-subj', '/CN=Ingress Default Certificate', '-keyout', '/etc/zorp/tls.key', '-out', '/etc/zorp/tls.pem'])
        output, error_ = res.communicate()
        if (error_):
            logger.error(error_)
        else:
            self.has_default_cert = True

    def generate_config(self):
        if len(self.secrets) == 0 and self.has_default_cert is False and self.behaviour == 'basic':
            self.generate_self_signed_cert()
        policyPy = ZorpConfigGenerator("templates/")
        policyPy.renderTemplate("basic-policy.py.j2", self.config)
        f = open("/tmp/k8s-config", "w")
        f.write(str(self.config)+"\n")
        f.close()

    def reload_zorp(self):
        self._logger.info("Configuration changed, reloading Zorp")
        res = subprocess.Popen(['/usr/sbin/zorpctl', 'reload'], stdout=subprocess.PIPE)
        output, error_ = res.communicate()
        if (error_):
            logger.error(error_)

    def load_k8s_config(self):
        oldconfig = deepcopy(self.config)
        self.config["ingress"] = self.k8s.get_relevant_ingresses()
        self.config["services"] = self.k8s.get_relevant_services(self.config["ingress"])
        self.config["endpoints"] = self.k8s.get_relevant_endpoints(self.config["services"])
        self.secrets= {}
        for secret_name in self.k8s.list_secrets():
            self.secrets[secret_name] = self.k8s.get_secret(secretname)
        if oldconfig != self.config:
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
