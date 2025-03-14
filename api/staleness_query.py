from sqlalchemy.orm.exc import NoResultFound

from app.common import inventory_config
from app.logging import get_logger
from app.models import Staleness

logger = get_logger(__name__)


def get_staleness_obj(org_id):
    try:
        staleness = Staleness.query.filter(Staleness.org_id == org_id).one()
        logger.info("Using custom account staleness")
        staleness = _build_serialized_acc_staleness_obj(staleness)
    except NoResultFound:
        logger.debug(f"No data found for user {org_id}, using system default values")
        staleness = _build_staleness_sys_default(org_id)
        return staleness

    return staleness


def get_sys_default_staleness(config=None):
    return _build_staleness_sys_default("000000", config)


def get_sys_default_staleness_api(identity, config=None):
    org_id = identity.org_id or "00000"
    return _build_staleness_sys_default(org_id, config)


def _build_staleness_sys_default(org_id, config=None):
    if not config:
        config = inventory_config()

    return AttrDict(
        {
            "id": "system_default",
            "org_id": org_id,
            "conventional_time_to_stale": config.conventional_time_to_stale_seconds,
            "conventional_time_to_stale_warning": config.conventional_time_to_stale_warning_seconds,
            "conventional_time_to_delete": config.conventional_time_to_delete_seconds,
            "immutable_time_to_stale": config.immutable_time_to_stale_seconds,
            "immutable_time_to_stale_warning": config.immutable_time_to_stale_warning_seconds,
            "immutable_time_to_delete": config.immutable_time_to_delete_seconds,
            "created_on": None,
            "modified_on": None,
        }
    )


# This is required because we do not keep a ORM object that is attached to a session
# leaving in the global scope. Before this serialization,
# it was causing sqlalchemy.orm.exc.DetachedInstanceError
def _build_serialized_acc_staleness_obj(staleness):
    return AttrDict(
        {
            "id": str(staleness.id),
            "org_id": staleness.org_id,
            "conventional_time_to_stale": staleness.conventional_time_to_stale,
            "conventional_time_to_stale_warning": staleness.conventional_time_to_stale_warning,
            "conventional_time_to_delete": staleness.conventional_time_to_delete,
            "immutable_time_to_stale": staleness.immutable_time_to_stale,
            "immutable_time_to_stale_warning": staleness.immutable_time_to_stale_warning,
            "immutable_time_to_delete": staleness.immutable_time_to_delete,
            "created_on": staleness.created_on,
            "modified_on": staleness.modified_on,
        }
    )


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self
