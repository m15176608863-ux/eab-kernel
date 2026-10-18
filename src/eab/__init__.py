"""eab-kernel: entrance-block contact kernel and cross-engine contact record contract."""

from .contact_record import (  # noqa: F401
    ContactRecord,
    CoverType,
    Feature,
    Mode,
    validate,
    records_to_json,
    records_from_json,
)

__all__ = [
    "ContactRecord", "CoverType", "Feature", "Mode",
    "validate", "records_to_json", "records_from_json",
]
