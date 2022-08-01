# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.
from flask import current_app

import requests


class OEDataRep:
    """OEDataRep class."""

    def __init__(self):
        """Class Contructor."""
        self._records_endpoint = current_app.config.get(
            "OEDATAREP_RECORDS_URL")
        self._token = current_app.config.get("OEDATAREP_API_AUTH_TOKEN")

    def get_record_data(self, recid):
        """ Get record metadata """
        result = self.__get(f"{self._records_endpoint}/{recid}/draft",
                            {"Authorization": f"Bearer {self._token}"})
        # if response.status_code != 200 or \
        #         not bool(response.json()) or \
        #         type(response.json()) is not dict:
        #     raise
        return result.json()

    def get_record_files(self, files_url):
        """ Returns record files. """
        result = self.__get(files_url,
                            {"Authorization": f"Bearer {self._token}"})
        return result.json()

    def __get(self, url, headers):
        """ Performs rest API calls. """
        try:
            result = requests.get(url, headers=headers, verify=False)
            result.raise_for_status()
        except requests.exceptions.HTTPError:
            current_app.logger.exception("In connecting to OEDataRep REST APi")
            raise
        return result
