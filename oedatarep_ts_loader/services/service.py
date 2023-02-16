# service.py
from invenio_records_resources.services import Service


class SwaggerUIService(Service):

    def click(self, identity):
        self.require_permission(identity, "click")

        return
