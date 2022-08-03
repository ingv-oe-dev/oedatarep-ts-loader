# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.
import csv
from io import StringIO
from flask import current_app
import requests


class TSDSystem:
    """TSDSystem class."""

    def __init__(self):
        """Class Contructor."""
        self._tsd_endpoint = current_app.config.get("TSD_API_URL")
        self._token = current_app.config.get("TSD_API_AUTH_TOKEN")

    def create_ts(self, ts_header, recid):
        ts_header["name"] = ts_header["name"] + "_" + \
            str(recid).replace("-", "")
        response = self.__post(
            {"Authorization": self._token},
            ts_header
        )
        return response.json()["data"]["id"]

    def load_ts(self, ts_guid, ts_csv, recid):
        current_app.logger.info("Record (id:%s) - TS_Guid: %s", recid, ts_guid)
        response = self.__post(
            {"Authorization": self._token},
            self.__make_json(ts_guid, ts_csv),
            resource="/values"
        )
        return (response.json()["error"], ts_guid)

    def __post(self, headers, payload, resource=""):
        try:
            rsp = requests.post(
                f"{self._tsd_endpoint}/timeseries{resource}",
                json=payload,
                headers=headers,
            )
            rsp.raise_for_status()
        except requests.HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')
        except Exception as err:
            # raise SystemExit(err)
            print(f'Other error occurred: {err}')
        return rsp

    def __make_json(self, ts_id, csvFile):
        """Convert a CSV to JSON."""
        # create a dictionary
        data = {
            'insert': 'ignore',
            'id': ts_id
        }
        csvReader = csv.reader(StringIO(csvFile), delimiter=',')
        data['columns'] = next(csvReader)
        if data['columns'] is not None:
            data['data'] = []
            for row in csvReader:
                data['data'].append(row)

        return data
