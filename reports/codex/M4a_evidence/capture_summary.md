# M4a 15例捕获证据摘要

- 内核 SHA-256：`26abf3ee24dc28ead32b97f6500490cf6087ee20ffc3712412dddd8f6d5a5606`
- 15例各3步；每例独立复制 exe+bb+db 两次到本树沙箱，原始CSV没有删列、改值或去重。
- 120个新夹具文件，共 1,436,984 字节；6类CSV+两个原始输入/例。
- 检测观测量是步初静态几何，不把上一拍位移或首次求解zsto2冒充本步确定的首入方向。
- d0/h1/h5/f1/f0/w0均由每步detparams实测；legacy w0依赖GetSystemMetrics，本次不声称固定屏幕跨机重现。

|case|三步contacts|步1重复主参考组数|contacts首步o3/o4差异格|df18首步o3/o4差异格|df22首步跳过o4更新差异格|
|---|---|---:|---:|---:|---:|
|52|54,54,54|0|93|93|8|
|12|54,54,54|0|94|94|69|
|50|2,2,2|0|4|4|4|
|51|54,54,54|0|90|90|84|
|03|40,40,40|0|78|78|78|
|05|10,10,10|0|19|19|14|
|06|10,10,10|0|20|20|14|
|09|58,58,58|0|94|94|96|
|10|74,74,74|0|95|95|99|
|v01|156,156,156|3|95|95|0|
|v01/v01a|154,154,154|2|95|95|6|
|v02|88,88,88|2|94|90|8|
|v02/v02a|88,88,88|2|96|92|90|
|F038|2,2,2|0|4|4|0|
|S038|2,2,2|0|4|4|0|

## 新发现的原始数据事实

- `df22` 首步 `o4` 有570格双跑差异；每格满足 `mtype==1 or m0_new==0`。`D:/b-DDA/df/df.c:3994` 跳过 `:4030` 的唯一重算，`:4072-4075` 无条件导出。只排除该精确列/步/分支的状态残值，检测对账不消费；其余非既知初始残值的CSV单元格全部相同。逐格保留 first/repeat 值于 manifest。
- v01系、v02系首步共9组主参考重复（9条额外记录）；p1/p2/p3相同而m4/m5/m6不同。后两步无规范键重复，原始记录完整保留。全量见 `legacy_duplicate_primary_references.json`。

## 可复跑核验

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/m4_capture_family.py --verify-only
python -X utf8 -m pytest -q tests/test_fixture_provenance.py tests/test_provenance_inputs.py --basetemp reports/codex/M4a_evidence/tmp/fixtures_verified -p no:cacheprovider
```

捕获核验：`{"cases": 15, "steps": 45, "fixture_bytes": 1436984, "status": "verified"}`。
溯源门：`188 passed in 0.22s`。
旧读取器唯一性断言在4个v系夹具报红是原始重复揭露，未改raw fixture或canonical_key；由主任务按精确主参考重复类别看护，不将现状冒称全套绿。
