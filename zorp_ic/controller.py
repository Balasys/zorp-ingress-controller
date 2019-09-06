from apscheduler.schedulers.blocking import BlockingScheduler

from .kubernetes_backend import KubernetesBackend


def process_scaling_changes():
    pass


def process_routing_changes():
    pass


if __name__ == '__main__':
    job_defaults = {
        'coalesce': True,
        'max_instances': 1,
        'misfire_grace_time': 300
    }

    scheduler = BlockingScheduler(job_defaults=job_defaults)
    scheduler.add_job(process_scaling_changes, 'interval', minutes=1, jitter=15)
    scheduler.add_job(process_routing_changes, 'interval', minutes=1, jitter=15)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
