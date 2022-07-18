# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

"""OEDataRep module to load Time Series on TSDSystem"""

from .ext import OEDataRepTsLoader
from .version import __version__

__all__ = ('__version__', 'OEDataRepTsLoader')
