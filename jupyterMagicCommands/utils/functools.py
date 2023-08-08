from functools import wraps

class Suppress:
    def __init__(self, *exception_classes):
        self._exception_classes = exception_classes
        self.exception = None
        self.traceback = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.exception = exc_val
        self.traceback = exc_tb
        return exc_type is not None and issubclass(exc_type, self._exception_classes)

def suppress(*suppress_args, **suppress_kwargs):
    def suppress_level1_wrapper(func):
        @wraps(func)
        def suppress_innermost_wrapper(*args, **kwargs):
            with Suppress(*suppress_args, **suppress_kwargs) as sp:
                ret =  func(*args, **kwargs)
                return ret
            print("Run into error: ", sp.exception)
        return suppress_innermost_wrapper
    return suppress_level1_wrapper