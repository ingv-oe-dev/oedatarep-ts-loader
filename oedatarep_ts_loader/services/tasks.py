# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

import json
import logging
import urllib

from celery import shared_task
from flask import current_app

from ..errors import (
    TSLoaderException,
    RecordMissingFiles,
    HeaderFileMissing,
    TSDataFileMissing)
from .components import OEDataRep
from .components import TSDSystem
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

                if not ts_resource["name"] in ts_files.keys():
                    raise RecordMissingFiles(ts_resource["name"])

                ts_csv = oedatarep.get_record_file_content(
                    ts_files[str(ts_resource["name"])]["content_link"],
                    json=False
                )
                ts_guid = tsd_system.create_ts(ts_resource, recid)
                (error, guid) = tsd_system.load_ts(ts_guid, ts_csv, recid)

                if error is None:
                    values_query = __build_query(guid, ts_resource["preview"])
                    ts_resources.append(dict({
                        "guid": guid,
                        "name": ts_resource["name"],
                        "tsdws_url": (
                            f"{tsd_system._endpoint}/timeseries/values"
                            f"?request={values_query}"
                        ),
                        "ts_published": True,
                        "header": ts_resource["header"],
                        "preview": ts_resource["preview"],
                        "description": ts_resource["description"],
                        "additional_info": ts_resource["additional_info"],
                    }))
                else:
                    ts_resources.append(ts_resource)
            else:
                ts_resources.append(ts_resource)

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
            logger.debug("Parsed record_files: %s", res)
        else:
            raise RecordMissingFiles()
    return res


def __filter_ts_files(record_files):
    """ Returns a dict with each element a .csv """
    files = __parse_record_files(record_files)
    data_entries = {}

    try:
        for f in files:
            if f['mimetype'] in 'text/csv':
                data_entries[f['key'].replace(".csv", "")] = f

    except ValueError as err:
        raise (err)
    else:
        return data_entries


def __build_query(guid, preview_metadata):
    preview_metadata["id"] = guid
    q = json.dumps(preview_metadata)
    return urllib.parse.quote_plus(q)
