# resource.py
import datetime

import jwt
from flask import g, session
from flask_resources import Resource, response_handler, route

from oedatarep_ts_loader.services.components import TSDSystem


class SwaggerUIResource(Resource):
    def __init__(self, config, service):
        super().__init__(config)
        self.service = service

    def create_url_rules(self):
        # Get the named routes from the config
        routes = self.config.routes
        # Define the URL rules:
        return [
            route("POST", routes["querybuilder"], self.click),
        ]

    # Decorate the view
    @response_handler()
    def click(self):
        self.service.click(g.identity)
        token = session.get("tsdToken")
        if token is None or self.token_expired(token):
            (token, error) = self.new_token()
            session["tsdToken"] = token
            if error is not None:
                return error['error'], error['statusCode']

        return token, 200

    def new_token(self):
        tsd_system = TSDSystem()
        rsp = tsd_system.generate_token()
        if rsp["error"] is None:
            token = rsp["token"]
            return (token, None)
        else:
            return (None, rsp)

    def token_expired(self, token):
        decoded_data = jwt.decode(jwt=token,
                                  options={"verify_signature": False},
                                  algorithms=["HS256"])

        now = datetime.datetime.now()
        exp = datetime.datetime.fromtimestamp(decoded_data["exp"])
        return now >= exp
