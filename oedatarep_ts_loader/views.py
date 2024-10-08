# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

"""OEDataRep module to load Time Series on TSDSystem"""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from flask import Blueprint, render_template

blueprint = Blueprint(
    'oedatarep_ts_loader',
    __name__,
    template_folder='templates',
    static_folder='static',
)
