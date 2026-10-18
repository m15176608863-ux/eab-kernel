"""tf L5 source-code mappings.

Original mode codes remain in raw_mode; unverified modes are not promoted. Codes 4/5/6 remain UNVERIFIED; no equivalence to sliding/locked is established (docs/sibling_observations.md).
"""
from ..contact_record import CoverType, Mode


TF_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.TENSION,
                            4: Mode.UNVERIFIED, 5: Mode.UNVERIFIED, 6: Mode.UNVERIFIED}

TF_COVER: dict[int, CoverType] = {0: CoverType.NN, 1: CoverType.NE, 2: CoverType.VF, 3: CoverType.EE}
