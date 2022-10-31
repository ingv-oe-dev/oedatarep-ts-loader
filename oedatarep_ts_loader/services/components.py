# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

from io import StringIO
from flask import current_app

import csv
import json
import copy
import requests


class TSDSystem:
    """TSDSystem class."""

    def __init__(self):
        """Class Contructor."""
        self._endpoint = current_app.config.get("TSD_API_URL")
        self._token = current_app.config.get("TSD_API_AUTH_TOKEN")

    def create_ts(self, ts_resource, recid):
        ts_header_new = self.__sanitize_header(ts_resource, recid)
        response = self.__post(
            {"Authorization": self._token}, ts_header_new
        )
        return response.json()["data"]["id"]

    def load_ts(self, ts_guid, ts_csv, recid):
        current_app.logger.info("Record (id:%s) - TS_Guid: %s", recid, ts_guid)
        response = self.__post(
            {"Authorization": self._token},
            self.__make_json(ts_guid, ts_csv),
            resource=f"/{ts_guid}/values"
        )
        return (response.json()["error"], ts_guid)

    def __sanitize_header(self, ts_resource, recid):
        new_header = copy.deepcopy(ts_resource["header"])
        new_header["name"] = ts_resource["name"].lower() + "_" + \
            str(recid).replace("-", "")
        new_header["schema"] = "oedatarep"
        for c in new_header["columns"]:
            c["name"] = c["name"].lower()
        return new_header

    def __post(self, headers, payload, resource=""):
        try:
            rsp = requests.post(
                f"{self._endpoint}/timeseries{resource}",
                json=payload,
                headers=headers,
                verify=False
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
        delimiter = self.__extract_delimiter(csvFile)
        # create a dictionary
        data = {
            'insert': 'ignore',
            'id': ts_id
        }
        csvReader = csv.reader(StringIO(csvFile), delimiter=delimiter)
        data['columns'] = next(csvReader)
        if data['columns'] is not None:
            for c in data['columns']:
                c.lower()
            data['data'] = []
            for row in csvReader:
                for i, x in enumerate(row):
                    if len(x) < 1:
                        row[i] = None
                data['data'].append(row)

        return data

    def __extract_delimiter(self, file):
        sniffer = csv.Sniffer()
        sniffer.preferred = [',', ';', '|']
        dialect = sniffer.sniff(file)
        return dialect.delimiter


class OEDataRep:
    """OEDataRep class."""

    def __init__(self):
        """Class Contructor."""
        self._records_endpoint = current_app.config.get(
            "OEDATAREP_RECORDS_URL")
        self._token = current_app.config.get("OEDATAREP_API_AUTH_TOKEN")

    def get_record_data(self, recid):
        """ Returns record metadata. """
        result = self.__get(
            f"{self._records_endpoint}/{recid}",
        )
        return result.json()

    def get_record_files(self, files_url):
        """ Returns record files. """
        result = self.__get(
            files_url,
        )
        return result.json()

    def get_record_file_content(self, content_url, json=True):
        """ Returns record files content. """
        result = self.__get(
            content_url,
        )

        return result.json() if json else result.text

    def update_record_metadata(self, recid, metadata):
        try:
            resp = requests.post(
                f"{self._records_endpoint}/{recid}/draft",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    'Content-Type': 'application/json'
                },
                verify=False
            )
            resp = requests.put(
                f"{self._records_endpoint}/{recid}/draft",
                data=json.dumps(metadata),
                headers={
                    "Authorization": f"Bearer {self._token}",
                    'Content-Type': 'application/json'
                },
                verify=False
            )
            resp = requests.post(
                f"{self._records_endpoint}/{recid}/draft/actions/publish",
                headers={
                    "Authorization": f"Bearer {self._token}",
                    'Content-Type': 'application/json'
                },
                verify=False
            )
            resp.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

    def __get(self, url, headers=None, verify=False):
        """ Performs rest API calls. """
        result = requests.get(url, headers=headers, verify=verify)
        result.raise_for_status()
        return result
