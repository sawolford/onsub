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

def outcount(cmd):
    ec, out = check_output(cmd, stderr=sp.DEVNULL)
    return out.count("\n")

def hgcheck(verbose, debug, path, noexec, *rest):
    if noexec: return 0, "[noexec] hgcheck"
    if not os.path.exists(".hg"): return 0, "[not an hg clone]"
    nst = outcount("hg status -q")
    nsh = outcount("hg shelve --list")
    prefix = 'onsub --chdir {path} --depth 1 --comment "wc={nst},sh={nsh}"'.format(path=path, nst=nst, nsh=nsh)
    if len(rest) and rest[0] == "--local":
        if nst > 0: return 1, '{prefix} {{put}}'.format(prefix=prefix)
        if nsh > 0: return 2, '{prefix} {{unstow}}'.format(prefix=prefix)
        return 0, "[no local mods]"
    nin = outcount("hg in -q")
    nout = outcount("hg out -q")
    prefix = 'onsub --chdir {path} --depth 1 --comment "wc={nst},sh={nsh},out={nout},in={nin}"'.format(path=path, nst=nst, nsh=nsh, nout=nout, nin=nin)
    if nin > 0 and nout == 0: return 3, '{prefix} {{download-get}}'.format(prefix=prefix)
    if nout > 0 and nin == 0:
        if nst > 0: return 4, '{prefix} {{put-upload}}'.format(prefix=prefix)
        return 5, '{prefix} {{upload}}'.format(prefix=prefix)
    if nout > 0 and nin > 0:
        if nst > 0: return 6, '{prefix} {{download-get}}'.format(prefix=prefix)
        return 7, '{prefix} {{download-get}}'.format(prefix=prefix)
    if nst > 0: return 8, '{prefix} {{put}}'.format(prefix=prefix)
    if nsh > 0: return 9, '{prefix} {{unstow}}'.format(prefix=prefix)
    return 0, "[no local mods, no repository changes]"

def myhgcheck(args): return hgcheck(5, False, os.getcwd(), False, *args)

if __name__ == "__main__":
    ec, out = myhgcheck(sys.argv[1:])
    print(out)
    sys.exit(ec)
    pass
