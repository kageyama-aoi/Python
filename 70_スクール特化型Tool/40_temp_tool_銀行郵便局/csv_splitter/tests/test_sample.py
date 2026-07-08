import pytest

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("ゼロ除算")
    return a / b

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
        
def test_divide_message():
    with pytest.raises(ZeroDivisionError) as e:
        divide(10,0)
    assert "ゼロ除算" in str(e.value)