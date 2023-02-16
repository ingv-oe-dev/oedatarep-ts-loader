from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AuthenticatedUser


class SwaggerUIPermissionPolicy(RecordPermissionPolicy):
    can_click = [AuthenticatedUser()]
