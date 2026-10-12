from pathlib import Path
p=Path('src/eab/kernel2d/g0.py')
with p.open(encoding='utf-8',newline='') as f:s=f.read()
marker='\ndef sample_translations'
s=s.replace(marker,'''\ndef _minimum_witness_distance(covs):
    """No nonfinite candidate can hide behind a finite minimum."""
    distances = []
    for c in covs:
        if c.point_a is None or c.point_b is None:
            continue
        distance = math.hypot(c.point_a[0]-c.point_b[0], c.point_a[1]-c.point_b[1])
        if not math.isfinite(distance):
            return math.inf
        distances.append(distance)
    return min(distances, default=math.inf)

''' + marker)
old='''min((math.hypot(c.point_a[0] - c.point_b[0], c.point_a[1] - c.point_b[1])
                   for c in covs if c.point_a is not None and c.point_b is not None), default=inf)'''
assert s.count(old)==2
s=s.replace(old,'_minimum_witness_distance(covs)')
with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
# Scaled atan2 may discard a negligible cosine, but must reject an unrepresentable
# nonzero angle; do not reject a representable pi/2 because its cosine is tiny.
p=Path('src/eab/kernel2d/geom.py')
with p.open(encoding='utf-8',newline='') as f:s=f.read()
s=s.replace('''    return atan2(_display_fraction(determinant/scale), _display_fraction(scalar/scale))''','''    angle = atan2(float(determinant/scale), float(scalar/scale))
    if determinant and angle == 0:
        raise ArithmeticError("nonzero turn angle below binary64 output range")
    return angle''')
with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
