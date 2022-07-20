from celery import shared_task

@shared_task
def register_ts():
	# TODO:
	import time
	time.sleep(10)
	TSResource().bootstrap_instance()
	return

class TSResource():
	def __init__(self, url=None, token=None):
		pass

	def bootstrap_instance(self):
		pass