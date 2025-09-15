import sys

def debug_log(*args):
    print(f"[{sys._getframe(2).f_code.co_name} -> {sys._getframe(1).f_code.co_name}] ", *args)