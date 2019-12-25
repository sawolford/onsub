from os import chdir, getcwd
from os.path import realpath

class PushdContext:
    cwd = None
    owd = None
    def __init__(self, dirname): self.cwd = realpath(dirname)
    def __enter__(self):
        self.owd = getcwd()
        try: chdir(self.cwd)
        except FileNotFoundError: return None
        return self
    def __exit__(self, type, value, tb): chdir(self.owd)
    pass

def pushd(dirname): return PushdContext(dirname)
