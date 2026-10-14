"""Independent regression of equality finding, plus its original mutation."""
from fractions import Fraction
from pathlib import Path
import json
import os
import sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[4]
temporary=Path(__file__).resolve().parent.parent/'tmp'/'review_probe_r4'
temporary.mkdir(exist_ok=True)
os.environ['TMP']=os.environ['TEMP']=str(temporary)
sys.path.insert(0,str(root/'src'))
from eab.kernel2d.motion import QuadraticTime
value=QuadraticTime(Fraction(1,4))
result={"time_equals_string":value=='1/4',
        "hashes_equal":hash(value)==hash('1/4'),
        "set_size":len({value,'1/4'}),
        "time_equals_fraction":value==Fraction(1,4),
        "numeric_hashes_equal":hash(value)==hash(Fraction(1,4))}
assert not result['time_equals_string'] and result['set_size']==2
assert result['time_equals_fraction'] and result['numeric_hashes_equal']
count=0
for q,others in ((Fraction(0),(0,False,0.0)),(Fraction(1),(1,True,1.0)),
                 (Fraction(1,4),(0.25,Fraction(1,4))),
                 (Fraction(0.1),(0.1,Fraction(0.1)))):
    exact=QuadraticTime(q)
    for other in others:
        assert exact==other and other==exact
        assert hash(exact)==hash(other) and len({exact,other})==1
        assert {exact:'number'}[other]=='number'
        count+=1
assert QuadraticTime(Fraction(1,10))!=0.1
unsupported=('1/4',b'1/4',None,object(),float('nan'),float('inf'),-float('inf'))
for other in unsupported:
    assert value!=other and other!=value
    for left,right in ((value,other),(other,value)):
        try:
            left < right
        except TypeError:
            pass
        else:
            raise AssertionError('unsupported ordering accepted')
for boolean in (True,False):
    try:
        QuadraticTime(boolean)
    except ValueError:
        pass
    else:
        raise AssertionError('constructor accepted bool')
def equality_guard():
    assert value!='1/4', 'parseable text must not be numeric equality'
original=QuadraticTime.__eq__
def original_defect(self,other):
    if not isinstance(other,QuadraticTime):
        try:
            other=QuadraticTime(Fraction(other))
        except (TypeError,ValueError,OverflowError):
            return False
    return (self.rational,self.b,self.c,self.branch)==(other.rational,other.b,other.c,other.branch)
equality_guard()
try:
    QuadraticTime.__eq__=original_defect
    try:
        equality_guard()
    except AssertionError as error:
        assert str(error)=='parseable text must not be numeric equality'
        result['original_defect_red_expected_assertion']=str(error)
    else:
        raise AssertionError('original equality defect escaped regression guard')
finally:
    QuadraticTime.__eq__=original
equality_guard()
result.update(complete=True,supported_numeric_equalities=count,
              unsupported_comparison_types=len(unsupported),constructor_bool_rejections=2,
              corrected_kernel_regression_passed=True)
Path(__file__).with_name('equality_probe.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
