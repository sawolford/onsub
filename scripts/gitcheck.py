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

def gitcheck(verbose, debug, path, noexec, *rest):
    if noexec: return 0, "[noexec] gitcheck"
    if not os.path.exists(".git"): return 0, "[not a git clone]"
    nst = outcount("git status --short")
    nsh = outcount("git stash list --pretty=oneline")
    prefix = 'onsub --chdir {path} --depth 1 --comment "wc={nst},sh={nsh}"'.format(path=path, nst=nst, nsh=nsh)
    if len(rest) and rest[0] == "--local":
        if nst > 0: return 1, '{prefix} {{put}}'.format(prefix=prefix)
        if nsh > 0: return 2, '{prefix} {{unstow}}'.format(prefix=prefix)
        return 0, "[no local mods]"
    outcount("git fetch")
    nin = outcount("git log --pretty=oneline ..origin/master")
    nout = outcount("git log --pretty=oneline origin/master..")
    prefix = 'onsub --chdir {path} --depth 1 --comment "wc={nst},sh={nsh},out={nout},in={nin}"'.format(path=path, nst=nst, nsh=nsh, nout=nout, nin=nin)
    if nin > 0 and nout == 0: return 3, '{prefix} {{get}}'.format(prefix=prefix)
    if nout > 0 and nin == 0:
        if nst > 0: return 4, '{prefix} {{put-upload}}'.format(prefix=prefix)
        return 5, '{prefix} {{upload}}'.format(prefix=prefix)
    if nout > 0 and nin > 0:
        if nst > 0: return 6, '{prefix} {{download-get}}'.format(prefix=prefix)
        return 7, '{prefix} {{download}}'.format(prefix=prefix)
    if nst > 0: return 8, '{prefix} {{put}}'.format(prefix=prefix)
    if nsh > 0: return 9, '{prefix} {{unstow}}'.format(prefix=prefix)
    return 0, "[no local mods, no repository changes]"

def mygitcheck(args): return gitcheck(5, False, os.getcwd(), False, *args)

if __name__ == "__main__":
    ec, out = mygitcheck(sys.argv[1:])
    print(out)
    sys.exit(ec)
    pass
