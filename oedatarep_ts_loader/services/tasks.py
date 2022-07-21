# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

from celery import shared_task
from .search import TSRecordsSearch
@shared_task
def register_ts():
	records = TSRecordsSearch().execute()
	ids = []
	for record in records:
		ids.append(record.id)
		# TODO: BOotstrap TS loader workflow
		# TSResource().bootstrap_instance()
	return " ".join(ids)

class TSResource():
	def __init__(self, url=None, token=None):
		pass

	def bootstrap_instance(self):
		pass
