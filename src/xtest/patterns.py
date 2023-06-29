import threading


class ThraedSafeSingletonPattern(type):
    __instances = {}
    __thread_lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            with cls.__thread_lock:
                cls.__instances[cls] = super(ThraedSafeSingletonPattern, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]
