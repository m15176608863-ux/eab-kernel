"""tf L5 source-code mappings.

Original mode codes remain in raw_mode; unverified modes are not promoted. Codes 4/5/6 remain UNVERIFIED; no equivalence to sliding/locked is established (docs/sibling_observations.md).
"""
from ..contact_record import CoverType, Mode


# 各引擎状态码 → 统一词汇。原始码另存 raw_mode，映射不可逆时靠 raw 还原。
# tf.cpp 注释（tf.cpp:306-313）：0 open 1 friction 2 s-spring 3 t-tension 4 2f-friction 5 2f-lock 6 top-lock
# 4/5/6 此前折进 SLIDING/LOCKED，但 docs/sibling_observations.md 没有为这几个码记下任何 tf.cpp 行号引文
# （"2f"/"top" 的语义、它们在开闭迭代里是否等价于滑动/锁定，都没人核实过）——审查盲区 5。
# 所以标 UNVERIFIED，不替 tf.cpp 断言；raw_mode 保留原始码。入库夹具只出现 1、2（tests/test_tf_reader.py）。
TF_MODE: dict[int, Mode] = {0: Mode.OPEN, 1: Mode.SLIDING, 2: Mode.LOCKED, 3: Mode.TENSION,
                            4: Mode.UNVERIFIED, 5: Mode.UNVERIFIED, 6: Mode.UNVERIFIED}

# tf.cpp c[i][2] / m[j][2]：0 n-n 1 n-e 2 n-p 3 e-e（tf.cpp:297-300, 329-336）
TF_COVER: dict[int, CoverType] = {0: CoverType.NN, 1: CoverType.NE, 2: CoverType.VF, 3: CoverType.EE}
