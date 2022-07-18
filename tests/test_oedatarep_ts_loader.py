# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 INGV Osservatorio Etneo.
#
# OEDataRep Time Series Loader is free software; you can redistribute it
# and/or modify it under the terms of the MIT License; see LICENSE file for
# more details.

"""Module tests."""

from flask import Flask

from oedatarep_ts_loader import OEDataRepTsLoader


def test_version():
    """Test version import."""
    from oedatarep_ts_loader import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = OEDataRepTsLoader(app)
    assert 'oedatarep-ts-loader' in app.extensions

    app = Flask('testapp')
    ext = OEDataRepTsLoader()
    assert 'oedatarep-ts-loader' not in app.extensions
    ext.init_app(app)
    assert 'oedatarep-ts-loader' in app.extensions


def test_view(base_client):
    """Test view."""
    res = base_client.get("/")
    assert res.status_code == 200
    assert 'Welcome to OEDataRep Time Series Loader' in str(res.data)
