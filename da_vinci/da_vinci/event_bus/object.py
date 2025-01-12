import logging

logging.warning('DEPRECATED: da_vinci.event_bus.object is deprecated and will be removed in a future release. Use da_vinci.core.immutable_object instead.')


from da_vinci.core.immutable_object import (
    InvalidObjectSchemaError,
    MissingAttributeError,
    ObjectBody,
    ObjectBodySchema,
    ObjectBodyAttribute,
    ObjectBodyUnknownAttribute,
    ObjectBodyValidationResults,
    SchemaAttributeType,
    SchemaAttribute,
    UnknownAttributeSchema,
) 