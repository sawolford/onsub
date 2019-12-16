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

def st(out): return "{out}\n".format(out=out) if len(out) else ""

def gitcheck(verbose, debug, path, noexec, *rest):
    if noexec: return 0, "[noexec] gitcheck"
    if not os.path.exists(".git"): return 0, "[not a git clone]"
    nst = outcount("git status --short")
    if len(rest) and rest[0] == "--local":
        if nst > 0: return 1, 'onsub --chdir {path} --workers 1 --depth 1 {{write}}'.format(path=path)
        return 0, "[no local mods]"
    outcount("git fetch")
    nin = outcount("git log --pretty=oneline ..origin/master")
    nout = outcount("git log --pretty=oneline origin/master..")
    if nout > 0 and nin == 0:
        if nst > 0: write = 'onsub --chdir {path} --workers 1 --depth 1 {{write}}'.format(path=path)
        else: write = ""
        return 2, st(write) + 'onsub --chdir {path} --workers 1 --depth 1 {{put}}'.format(path=path)
    if nin > 0 and nout == 0:
        if nst > 0: return 3, 'onsub --chdir {path} --workers 1 --depth 1 {{wcget}}'.format(path=path)
        else: return 4, 'onsub --chdir {path} --workers 1 --depth 1 {{get}}'.format(path=path)
    if nout > 0 and nin > 0:
        if nst > 0: return 5, 'onsub --chdir {path} --workers 1 --depth 1 {{wcinout}}'.format(path=path)
        return 6, 'onsub --chdir {path} --workers 1 --depth 1 {{inout}}'.format(path=path)
    if nst > 0: return 7, 'onsub --chdir {path} --workers 1 --depth 1 {{write}}'.format(path=path)
    return 0, "[no local mods, no repository changes]"

def mygitcheck(args): return gitcheck(5, False, os.getcwd(), False, *args)

if __name__ == "__main__":
    ec, out = mygitcheck(sys.argv[1:])
    print(out)
    sys.exit(ec)
    pass
