# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.
import json
import logging
from flask import current_app
import requests
from oedatarep_ts_loader.errors import TSLoaderException


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
