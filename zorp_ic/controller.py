import argparse
from apscheduler.schedulers.blocking import BlockingScheduler
from .kubernetes_backend import KubernetesBackend

def process_k8s_changes(namespace, ingress_class):
    k8s = KubernetesBackend(namespace, ingress_class)
    k8s.get_ingresses()
    return

if __name__ == '__main__':

    namespace = ''
    ingress_class = ''
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
    scheduler.add_job(lambda: process_k8s_changes(namespace, ingress_class) , 'interval', seconds=5, jitter=5)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
