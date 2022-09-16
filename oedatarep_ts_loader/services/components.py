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

    def create_ts(self, ts_header, recid):
        ts_header_new = copy.deepcopy(ts_header)
        ts_header_new["name"] = ts_header_new["name"] + "_" + \
            str(recid).replace("-", "")
        response = self.__post(
            {"Authorization": self._token},
            ts_header_new
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
                f"{self._endpoint}/timeseries{resource}",
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
                for i, x in enumerate(row):
                    if len(x) < 1:
                        row[i] = None
                data['data'].append(row)

        return data


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
            f"{self._records_endpoint}/{recid}/draft",
            {"Authorization": f"Bearer {self._token}"}
        )
        return result.json()

    def get_record_files(self, files_url):
        """ Returns record files. """
        result = self.__get(
            files_url,
            {"Authorization": f"Bearer {self._token}"}
        )
        return result.json()

    def get_record_file_content(self, content_url, json=True):
        """ Returns record files content. """
        result = self.__get(
            content_url,
            {"Authorization": f"Bearer {self._token}"}
        )

        return result.json() if json else result.text

    def update_record_metadata(self, recid, metadata):
        try:
            resp = requests.put(
                f"{self._records_endpoint}/{recid}/draft",
                data=json.dumps(metadata),
                headers={
                    "Authorization": f"Bearer {self._token}",
                    'Content-Type': 'application/json'
                },
                verify=False
            )
            resp.raise_for_status()

        except requests.exceptions.RequestException as err:
            raise SystemExit(err)

        else:
            # logger.info(
            #     "Update_record_metadata return code: %s", resp.status_code
            # )
            # TODO: check and fix errors
            print(resp.json())

    def __get(self, url, headers):
        """ Performs rest API calls. """
        # try:
        result = requests.get(url, headers=headers, verify=False)
        result.raise_for_status()
        # except requests.HTTPError as http_err:
        #     logger.warning(f'HTTP error occurred: {http_err}')
        # except Exception as err:
        #     logger.warning(f'Other error occurred: {err}')
        return result
