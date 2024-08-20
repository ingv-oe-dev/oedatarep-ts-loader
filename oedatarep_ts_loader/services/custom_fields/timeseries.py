from invenio_records_resources.services.custom_fields import BaseListCF
from marshmallow import fields, validate
from marshmallow_utils.fields import SanitizedUnicode


class TimeseriesCF(BaseListCF):
    """Experiments with title and program."""

    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(
            name,
            field_cls=fields.Nested,
            field_args=dict(
                nested=dict(
                    description=SanitizedUnicode(),
                    guid=SanitizedUnicode(),
                    header=fields.Dict(),
                    name=SanitizedUnicode(),
                    preview=fields.Dict(),
                    ts_published=fields.Boolean(required=True),
                    tsdws_url=SanitizedUnicode(validate=_valid_url(
                        'Not a valid URL.')),
                )
            ),
            multiple=True,
            **kwargs
        )

    @property
    def mapping(self):
        """Return the mapping."""
        return {
            "properties": {
                "ts_published": {"type": "boolean"},
            }
        }


def _valid_url(error_msg):
    """Returns a URL validation rule with custom error message."""
    return validate.URL(error=error_msg)
