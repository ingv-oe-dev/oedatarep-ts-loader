# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

"""OEDataRep module to load Time Series on TSDSystem"""

from flask_babelex import gettext as _

from oedatarep_ts_loader.resources.config import SwaggerUIConfig
from oedatarep_ts_loader.resources.resource import SwaggerUIResource
from oedatarep_ts_loader.services.config import SwaggerUIServiceConfig
from oedatarep_ts_loader.services.service import SwaggerUIService

from . import config
from .services.tasks import logger


class OEDataRepTsLoader(object):
    """OEDataRep Time Series Loader extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        # TODO: This is an example of translation string with comment. Please
        # remove it.
        # NOTE: This is a note to a translator.
        _('A translation string')
        if app:
            self.init_app(app)

        service = SwaggerUIService(SwaggerUIServiceConfig)
        resource = SwaggerUIResource(SwaggerUIConfig(), service)
        app.register_blueprint(resource.as_blueprint())

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.config.setdefault('OEDATAREP_TS_LOGGER_HANDLERS', app.debug)
        if app.config['OEDATAREP_TS_LOGGER_HANDLERS']:
            for handler in app.logger.handlers:
                logger.addHandler(handler)
        app.extensions['oedatarep-ts-loader'] = self

    def init_config(self, app):
        """Initialize configuration."""
        # Use theme's base template if theme is installed
        if 'BASE_TEMPLATE' in app.config:
            app.config.setdefault(
                'OEDATAREP_TIME_SERIES_LOADER_BASE_TEMPLATE',
                app.config['BASE_TEMPLATE'],
            )
        for k in dir(config):
            if k.startswith('OEDATAREP_TIME_SERIES_LOADER_'):
                app.config.setdefault(k, getattr(config, k))
