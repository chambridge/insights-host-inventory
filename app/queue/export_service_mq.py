from marshmallow import Schema
from marshmallow import ValidationError
from marshmallow import fields

from app.common import inventory_config
from app.logging import get_logger
from app.queue import metrics
from app.queue.export_service import create_export
from app.queue.host_mq import HBIMessageConsumerBase
from app.queue.mq_common import common_message_parser

logger = get_logger(__name__)

CONSUMER_POLL_TIMEOUT_SECONDS = 1
EXPORT_EVENT_SOURCE = "urn:redhat:source:console:app:export-service"
EXPORT_SERVICE_APPLICATION = "urn:redhat:application:inventory"


class ExportResourceRequest(Schema):
    application = fields.Str(required=True)
    export_request_uuid = fields.UUID(required=True)
    filters = fields.Dict()
    format = fields.Str(required=True)
    resource = fields.Str(required=True)
    uuid = fields.Str(required=True)
    x_rh_identity = fields.Str(required=True, data_key="x-rh-identity")


class ExportDataSchema(Schema):
    resource_request = fields.Nested(ExportResourceRequest)


class ExportEventSchema(Schema):
    id = fields.UUID(required=True)
    schema = fields.Str(data_key="$schema")
    source = fields.Str(required=True)
    subject = fields.Str(required=True)
    specversion = fields.Str(required=True)
    type = fields.Str(required=True)
    time = fields.DateTime(required=True)
    redhatorgid = fields.Str(required=True)
    dataschema = fields.Str(required=True)
    data = fields.Nested(ExportDataSchema, required=True)


class ExportServiceConsumer(HBIMessageConsumerBase):
    @metrics.export_service_message_handler_time.time()
    def handle_message(self, message):
        validated_msg = parse_export_service_message(message)
        message_handled = False
        try:
            if (
                validated_msg["source"] == EXPORT_EVENT_SOURCE
                and validated_msg["data"]["resource_request"]["application"] == EXPORT_SERVICE_APPLICATION
            ):
                logger.info("Found host-inventory application export message")
                logger.debug("parsed_message: %s", validated_msg)
                base64_x_rh_identity = validated_msg["data"]["resource_request"]["x_rh_identity"]

                if create_export(validated_msg, base64_x_rh_identity, inventory_config()):
                    metrics.export_service_message_handler_success.inc()
                    message_handled = True
                else:
                    metrics.export_service_message_handler_failure.inc()
                    message_handled = False
            else:
                logger.debug("Found export message not related to host-inventory")
                message_handled = False
        except Exception as e:
            logger.error(e)
            metrics.export_service_message_handler_failure.inc()
            message_handled = False

        return message_handled


@metrics.export_service_message_parsing_time.time()
def parse_export_service_message(message):
    parsed_message = common_message_parser(message)
    try:
        parsed_export_msg = ExportEventSchema().load(parsed_message)
        return parsed_export_msg
    except ValidationError as e:
        logger.error(
            "Input validation error while parsing export event message:%s", e, extra={"operation": parsed_message}
        )  # logger.error is used to avoid printing out the same traceback twice

        metrics.export_service_message_parsing_failure.labels("invalid").inc()
        raise
    except Exception:
        logger.exception("Error parsing export event message", extra={"operation": parsed_message})

        metrics.export_service_message_parsing_failure.labels("error").inc()
        raise
