"""bdda3d L5 source-code mappings.

Original mode codes remain in raw_mode; unverified modes are not promoted.
"""
from ..contact_record import CoverType, Mode


# 各引擎状态码 → 统一词汇。原始码另存 raw_mode，映射不可逆时靠 raw 还原。
# bdda3d 3 = 键合；不同于 b-DDA 的第二参考闭合及 tf.cpp 的受拉态。
BDDA3D_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.BONDED}

# bdda3d etype
BDDA3D_COVER: dict[str, CoverType] = {"np": CoverType.VF, "ee": CoverType.EE}
