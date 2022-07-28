# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

from celery import shared_task
from flask import current_app
from .search import TSRecordsSearch
from .ts_resource import TSResource

@shared_task
def register_ts():
	records = TSRecordsSearch().execute()
	ids = []

	for record in records:
		if record.metadata.ts_resources:
			ids.append(record.id)
			execute_register_ts.delay(record.id)

	return " ".join(ids)

@shared_task(ignore_result=True)
def execute_register_ts(id):
	conf = current_app.config
	ts_object = TSResource(conf.get("OEDATAREP_API_RECORDS_URL"))
	ts_object.bootstrap_instance(id)

	record_data = ts_object.get_record_data()
	ts_object.set_instance_metadata(record_data)
	ts_object.set_instance_links(record_data)

	try:
		current_app.logger.debug("Instance _file_link: %s", ts_object._file_link)

		if ts_object._file_link != "":
			if ts_object.get_record_files():
				if ts_object.filter_ts_files():
					tsd_token = ts_object.get_tsd_auth_token()

					for entry in ts_object.ts_files_to_upload:
						ts_guid = ""
						header_data = ts_object.get_ts_header_file(entry[1]["content_link"], tsd_token)

						if bool(header_data):
							header_data["name"] = header_data["name"]+"_"+str(id).replace("-","")
							ts_guid = ts_object.post_ts_header_on_tsd(header_data, tsd_token)

							current_app.logger.debug("Record (id:%s) - TS_Guid: %s", id, ts_guid)

							# if bool(ts_guid):
							# 	ts_object.put_ts_guid_on_record_metadata(ts_guid)
						else:
							current_app.logger.info("Record (id:%s) - has no TS_Header", id)

						ts_data = ts_object.get_ts_data_file(entry[0]["content_link"], ts_guid, tsd_token)
						# ts_data = ts_object.get_ts_data_file(entry[0]["content_link"], tsd_token)

						if bool(ts_data):
							current_app.logger.debug("Record (id:%s) - TS_Data: %s", id, bool(ts_data))
							ts_object.post_ts_data_on_tsd(ts_data, tsd_token)

							if bool(ts_guid):
								ts_object.put_ts_guid_on_record_metadata(ts_guid)
						else:
							current_app.logger.info("Record (id:%s) - has no TS_data", id)
				else:
					current_app.logger.info("Record (id:%s) - does not have a valid TS pair files(csv,json)", id)
			else:
				current_app.logger.info("Record (id:%s) - has no files", id)
		else:
			current_app.logger.info("Record (id:%s) - has no links resource to files", id)

	except Exception as e:
		current_app.logger.exception(e)
		raise e

	return "Time series for Record: %s was successfully published on TSDSystem.", id
