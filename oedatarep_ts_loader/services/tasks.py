# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

from celery import shared_task
from flask import current_app
from oedatarep_ts_loader.services.components.datarep import OEDataRep
from oedatarep_ts_loader.services.components.tsd_system import TSDSystem
from oedatarep_ts_loader.services.search import TSRecordsSearch


@shared_task
def register_ts():
    """ Task that starts time series pubblication on TSDSystem. """
    records = TSRecordsSearch().execute()
    ids = []

    for record in records:
        if bool(record.metadata.ts_resources):
            ids.append(record.id)
            execute_register_ts.delay(record.id)

    return " ".join(ids)


@shared_task(ignore_result=True)
def execute_register_ts(recid):
    """ Task that actual publish time series on TSDSystem. """
    guids = []
    oedatarep = OEDataRep()
    tsd_system = TSDSystem()
    current_record = oedatarep.get_record_data(recid)
    if bool(current_record["links"]) and \
            bool(current_record["links"]["files"]):
        files_url = current_record["links"]["files"]
        record_files = oedatarep.get_record_files(files_url)
        files_to_upload = __filter_ts_files(record_files)
        for entry in files_to_upload:
            ts_csv = oedatarep.get_record_file_content(
                entry[0]["content_link"],
                json=False
            )
            header_content = oedatarep.get_record_file_content(
                entry[1]["content_link"]
            )
            ts_guid = tsd_system.create_ts(header_content, recid)
            (error, guid) = tsd_system.load_ts(ts_guid, ts_csv, recid)
            
            if error is None:
                guids.append(dict({
                    "guid": guid,
                    "chart_props": header_content,
                    "ts_published": True
                }))

                current_record["metadata"]["ts_resources"] = guids
                oedatarep.update_record_metadata(recid, current_record)
    return (recid, guids)


def __parse_record_files(record_files):
    res = []

    try:
        for r in record_files["entries"]:
            current_app.logger.debug("Entry: %s", r)
            if r["status"] == "completed":
                res.append(dict({
                    "key": r["key"],
                    "content_link": r["links"]["content"],
                    "size": r["size"],
                    "mimetype": r["mimetype"],
                }))
    except Exception as err:
        raise (err)
    finally:
        if len(res) > 0:
            current_app.logger.debug("GOT record_files: %s", res)

    return res


def __filter_ts_files(record_files):
    """ Returns a list with each element a .csv & .json pair. """
    res = []
    files = __parse_record_files(record_files)
    try:
        data_entries = [d for d in files if d['mimetype'] in 'text/csv']
        header_entries = [h for h in files if h['mimetype'] in
                          'application/json']

        # current_app.logger.info("TS_Data_Array: %s", data_entries)
        # current_app.logger.info("TS_Header_Array: %s", header_entries)
    except ValueError as err:
        raise (err)

    for d_entry in data_entries:
        # current_app.logger.info("TS_Entry: %s", d_entry)
        for h_entry in header_entries:
            # current_app.logger.info("Header_Entry: %s", h_entry)
            try:
                if h_entry['key'] in d_entry["key"].replace(".csv",
                                                            "_header.json"):
                    res.append([
                        d_entry,
                        [h_entry for h_entry in header_entries
                            if h_entry['key'] in d_entry["key"].replace(
                                ".csv", "_header.json")].pop()]
                    )
            except ValueError as err:
                raise (err)

    if len(data_entries) > 0 and len(header_entries) > 0:
        current_app.logger.info("Instance data(s) to Upload: %s", res)
    else:
        current_app.logger.debug("Instance data: %s \n Intance header: %s",
                                 data_entries, header_entries)

    return res
