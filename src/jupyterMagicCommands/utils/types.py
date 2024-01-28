from typing import Optional, TypeVar

T = TypeVar('T')

def nn(s: Optional[T]) -> T:
    assert s is not None
    return s