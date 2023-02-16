# config.py
from flask_resources import JSONSerializer, ResourceConfig, ResponseHandler


class SwaggerUIConfig(ResourceConfig):

    response_handlers = {
        # Define JSON serializer for "application/json"
        "application/json": ResponseHandler(JSONSerializer())
    }

    # Blueprint configuration
    blueprint_name = "querybuilder"
    url_prefix = "/querybuilder"
    routes = {
        "querybuilder": "/", # relative to url_prefix
    }