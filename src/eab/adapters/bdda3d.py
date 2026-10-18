"""bdda3d L5 source-code mappings.

Original mode codes remain in raw_mode; unverified modes are not promoted.
"""
from ..contact_record import CoverType, Mode


BDDA3D_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.BONDED}

BDDA3D_COVER: dict[str, CoverType] = {"np": CoverType.VF, "ee": CoverType.EE}
