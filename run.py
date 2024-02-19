#!/usr/bin/env python
import os

import connexion
from connexion.apps.flask import FlaskApi
from connexion.resolver import RestyResolver
from prance import _TranslatingParser as TranslatingParser

from app import create_app
from app import process_system_profile_spec
from app import SPECIFICATION_FILE
from app.config import Config
from app.custom_validator import build_validator_map
from app.environment import RuntimeEnvironment

app = connexion.FlaskApp(__name__)

application = create_app(RuntimeEnvironment.SERVER, app)
app_config = Config(RuntimeEnvironment.SERVER)

with application.app_context():
    parser = TranslatingParser(SPECIFICATION_FILE)
    parser.parse()

    sp_spec, unindexed_fields = process_system_profile_spec()
    spec = connexion.spec.OpenAPISpecification(parser.specification)
    for api_url in app_config.api_urls:
        if api_url:
            app.add_api(
                parser.specification,
                arguments={"title": "Inventory API"},
                resolver=RestyResolver("api"),
                resolver_error=404,
                validate_responses=True,
                strict_validation=True,
                base_path=api_url,
                validator_map=build_validator_map(system_profile_spec=sp_spec, unindexed_fields=unindexed_fields),
            )
            api = FlaskApi(
                spec,
                arguments={"title": "Inventory API"},
                resolver=RestyResolver("api"),
                resolver_error=404,
                validate_responses=True,
                strict_validation=True,
                base_path=api_url,
                validator_map=build_validator_map(system_profile_spec=sp_spec, unindexed_fields=unindexed_fields),
            )
            application.register_blueprint(api.blueprint)

    application = app.app

print("url_map: %s", application.url_map)


if __name__ == "__main__":
    listen_port = int(os.getenv("LISTEN_PORT", 8080))
    app.run(host="0.0.0.0", port=listen_port, debug=True)
