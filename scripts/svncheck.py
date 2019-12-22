#!/usr/bin/env python3
import os, sys
import subprocess as sp

def check_output(cmd, stderr=sp.STDOUT):
    try:
        out = sp.check_output(cmd, shell=True, stderr=stderr).decode()
        ec = 0
        pass
    except sp.CalledProcessError as exc:
        out = exc.output.strip().decode()
        ec = exc.returncode
        pass
    return ec, out

def outcount():
    cmd = "svn st -q"
    ec, out = check_output(cmd, stderr=sp.DEVNULL)
    out = out.splitlines()
    rv = 0
    for line in out:
        if (line[0] != " "): rv += 1
        continue
    return rv

def outcountu():
    cmd = "svn status -u"
    ec, out = check_output(cmd, stderr=sp.DEVNULL)
    out = out.splitlines()
    rv = 0
    for line in out[:-1]:
        if line[8] == "*" and line[9] == " ": rv += 1
        continue
    return rv

def svncheck(verbose, debug, path, noexec, *rest):
    if noexec: return 0, "[noexec] svncheck"
    if not os.path.exists(".svn"): return 0, "[not an svn clone]"
    nst = outcount()
    prefix = 'onsub --chdir {path} --depth 1 --comment "wc={nst}"'.format(path=path, nst=nst)
    if len(rest) and rest[0] == "--local":
        if nst > 0: return 1, '{prefix} {{put-upload}}'.format(prefix=prefix)
        return 0, "[no local mods]"
    nin = outcountu()
    prefix = 'onsub --chdir {path} --depth 1 --comment "wc={nst},in={nin}"'.format(path=path, nst=nst, nin=nin)
    if nin > 0: return 2, '{prefix} {{download-get}}'.format(prefix=prefix)
    if nst > 0: return 3, '{prefix} {{put-upload}}'.format(prefix=prefix)
    return 0, "[no local mods, no repository changes]"

def mysvncheck(args): return svncheck(5, False, os.getcwd(), False, *args)

if __name__ == "__main__":
    ec, out = mysvncheck(sys.argv[1:])
    print(out)
    sys.exit(ec)
    pass
