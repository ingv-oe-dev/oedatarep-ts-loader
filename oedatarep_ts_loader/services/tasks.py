# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

import logging

from celery import shared_task
from flask import current_app

from ..errors import (
    TSLoaderException, 
    RecordMissingFiles, 
    HeaderFileMissing, 
    TSDataFileMissing)
from .components.datarep import OEDataRep
from .components.tsd_system import TSDSystem
from .search import TSRecordsSearch

logger = logging.getLogger("oedatarep-ts-loader")

@shared_task()
def register_ts():
    """ Task that starts time series pubblication on TSDSystem. """
    records = TSRecordsSearch().execute()
    ids = []

    for record in records:
        if bool(record.metadata.ts_resources):
            ids.append(record.id)
            execute_register_ts.delay(record.id)

    return " ".join(ids)


@shared_task()
def execute_register_ts(recid):
    """ Task that actual publish time series on TSDSystem. """
    ts_resources = []
    oedatarep = OEDataRep()
    tsd_system = TSDSystem()
    try:
        current_record = oedatarep.get_record_data(recid)
        record_files = oedatarep.get_record_files(
                    current_record["links"]["files"]
        )
        ts_files = __filter_ts_files(record_files)
        for ts_resource in current_record["metadata"]["ts_resources"]:
            if not ts_resource["ts_published"]:
                ts_csv = oedatarep.get_record_file_content(
                    ts_files[str(ts_resource["name"])]["csv"]["content_link"],
                    json=False
                )
                header_content = oedatarep.get_record_file_content(
                    ts_files[ts_resource["name"]]["header"]["content_link"]
                )
                ts_guid = tsd_system.create_ts(header_content, recid)
                (error, guid) = tsd_system.load_ts(ts_guid, ts_csv, recid)

                if error is None:
                    ts_resources.append(dict({
                        "guid": guid,
                        "chart_props": header_content,
                        "ts_published": True,
                        "name": header_content["name"],
                        "chart_url": f"{tsd_system._endpoint}/query"
                    }))
            else:
                ts_resources.append(ts_resource)
            print(ts_resource)
        current_record["metadata"]["ts_resources"] = ts_resources
        oedatarep.update_record_metadata(recid, current_record)
        
    except (RecordMissingFiles, TSDataFileMissing, HeaderFileMissing) as ts_ex:
        logger.warning("Record id: %s - %s", recid, ts_ex.message)
    except (TSLoaderException, Exception) as ex:
        raise ex

    return (recid, ts_resources)

def __parse_record_files(record_files):
    res = []

    try:
        for r in record_files["entries"]:
            # current_app.logger.debug("Entry: %s", r)
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
        else:
            raise RecordMissingFiles()
    return res

def __check_ts_files_pair(files):
    data_entries = {}
    header_entries = {}

    try:
        for f in files:
            if f['mimetype'] in 'text/csv':
                data_entries[f['key'].replace(".csv", "")] = f
            elif f['mimetype'] in 'application/json':
                header_entries[f['key'].replace("_header.json", "")] = f

        if len(data_entries.keys()) < len(header_entries.keys()):
            raise TSDataFileMissing()
        elif len(data_entries.keys()) > len(header_entries.keys()):
            raise HeaderFileMissing()

    except ValueError as err:
        raise (err)
    
    else:
        return (data_entries, header_entries)

def __filter_ts_files(record_files):
    """ Returns a list with each element a .csv & .json pair. """
    res = {}
    files = __parse_record_files(record_files)
    data_entries = {}
    header_entries = {}

    (data_entries, header_entries) = __check_ts_files_pair(files)

    for dk in data_entries.keys():
        res[dk] = dict({
            "csv": data_entries[dk],
            "header": header_entries[dk]
        })

    return res
