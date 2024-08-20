# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.


"""Time Series unplushed records."""

from opensearch_dsl.query import Q
from invenio_search.api import RecordsSearch


class TSRecordsSearch(RecordsSearch):
    """Search class for records that are not published on TSDSystem yet."""

    class Meta:
        """Default index and filter for frontpage search."""

        index = "rdmrecords-records"
        default_filter = Q(
            "query_string",
            query=("custom_fields.ingv\:ts_resources.ts_published:false"),
        )
