#!/usr/bin/env python3
import os, sys
import subprocess as sp

def mycheck_output(cmd, stderr=sp.STDOUT):
    try:
        out = sp.check_output(cmd, shell=True, stderr=stderr).decode()
        ec = 0
        pass
    except sp.CalledProcessError as exc:
        out = exc.output.strip().decode()
        ec = exc.returncode
        pass
    return ec, out

def outcount(cmd):
    ec, out = mycheck_output(cmd, stderr=sp.DEVNULL)
    return out.count("\n")

def hgcheck(verbose, debug, path, noexec, *rest):
    if noexec: return 0, "[noexec] hgcheck"
    if not os.path.exists(".hg"): return 0, "[not an hg clone]"
    nheads = outcount("hg heads -q .")
    nparents = outcount("hg parents -q")
    if nheads == 2 and nparents == 2: return 1, 'onsub --chdir {path} --workers 1 --depth 1 {{continue}}'.format(path=path)
    elif nheads == 2 and nparents == 1: return 2, 'onsub --chdir {path} --workers 1 --depth 1 {{finish}}'.format(path=path)
    nst = outcount("hg st -q")
    if nst > 0: return 3, 'onsub --chdir {path} --workers 1 --depth 1 {{write}}'.format(path=path)
    if len(rest) and rest[0] == "--local": return 0, "[no local mods]"
    nout = outcount("hg out -q")
    nin = outcount("hg in -q")
    if nout > 0 and nin == 0: return 4, 'onsub --chdir {path} --workers 1 --depth 1 {{put}}'.format(path=path)
    if nin > 0 and nout == 0: return 5, 'onsub --chdir {path} --workers 1 --depth 1 {{get}}'.format(path=path)
    if nin > 0 and nout > 0: return 6, 'onsub --chdir {path} --workers 1 --depth 1 {{mix}}'.format(path=path)
    return 0, "[no local mods, no repository changes]"

def myhgcheck(*args): return hgcheck(5, False, os.getcwd(), False, *args)

if __name__ == "__main__":
    ec, out = myhgcheck(sys.argv)
    print(out)
    sys.exit(ec)
    pass
