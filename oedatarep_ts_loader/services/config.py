# config.py
from invenio_records_resources.services import ServiceConfig

from oedatarep_ts_loader.services.permissions import SwaggerUIPermissionPolicy


class SwaggerUIServiceConfig(ServiceConfig):
    permission_policy_cls = SwaggerUIPermissionPolicy
