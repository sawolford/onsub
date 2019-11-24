#!/usr/bin/env python3
import os, sys
import argparse as ap
import subprocess as sp
import termcolor as tc
import pushd

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    return

def error(code, *args, **kwargs):
    eprint(*args, **kwargs)
    sys.exit(code)
    return

def check_vars(vars):
    assert "default" in vars
    assert "hg" in vars
    assert "git" in vars
    return

def format(st, dd, count):
    while count >= 0:
        nst = st.format(**dd)
        if nst == st: break
        st = nst
        count -= 1
        continue
    return st

def mysystem(cmd, extra, quiet, verbose):
    if verbose:
        tc.cprint("=== {path} ({extra}) ===".format(path=os.getcwd(), extra=extra), "blue", end="")
        tc.cprint(" ", end="")
        tc.cprint("{cmd}".format(cmd=cmd), "green",)
    try:
        out = sp.check_output(cmd, shell=True, stderr=sp.STDOUT).strip().decode()
        ec = 0
    except sp.CalledProcessError as exc:
        out = exc.output.strip().decode()
        ec = exc.returncode
        pass
    return ec, out

def doit(default, rest, count, extra, quiet, verbose, debug):
    cmd = format(rest, default, count)
    ec, out = mysystem(cmd, extra, quiet, verbose)
    if ec: tc.cprint(out, "red")
    elif verbose: tc.cprint(out)
    return ec, out

def main():
    parser = ap.ArgumentParser(description="Walks filesystem executing arbitrary commands", formatter_class=ap.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--command", help="Prefix {cmd}", action="store_true", default=False)
    parser.add_argument("--config", help="Config file", type=str, default=f'{os.environ["HOME"]}/.onsub')
    parser.add_argument("--count", help="Count for subsitutions", type=int, default=10)
    parser.add_argument("--debug", help="Debug flag", action="store_true", default=False)
    parser.add_argument("--depth", help="Walk depth", type=int, default=-1)
    parser.add_argument("--git", help="Git", action="store_true", default=False)
    parser.add_argument("--hg", help="Hg", action="store_true", default=False)
    parser.add_argument("--quiet", help="Quiet", action="store_true", default=False)
    parser.add_argument("--verbose", help="Verbose", action="store_true", default=False)
    parser.add_argument("rest", nargs=ap.REMAINDER)
    args = parser.parse_args()
    command = []
    if args.command: command = ["{cmd}"]
    config = args.config
    count = args.count
    debug = args.debug
    depth = args.depth
    neither = not args.hg and not args.git
    dohg = dogit = False
    if args.hg or neither: dohg = True
    if args.git or neither: dogit = True
    quiet = args.quiet
    verbose = args.verbose
    if len(args.rest) < 1: error(1, "Not enough command arguments")
    rest = " ".join(command + args.rest)

    rc = open(config).read()
    dd = {}
    exec(rc, globals(), dd)
    check_vars(dd)

    hgdir = ".hg"
    gitdir = ".git"
    root = os.getcwd()
    for path, subdirs, files in os.walk(".", followlinks=True):
        dd = {}
        nsep = path.count(os.path.sep)
        if depth >= 0 and nsep > depth: continue
        if dohg and os.path.exists("{path}/{hgdir}".format(path=path, hgdir=hgdir)):
            with pushd.pushd(path) as ctx:
                exec(rc, globals(), dd)
                default = dd["default"]
                default.update(dd["hg"])
                doit(default, rest, count, "hg", quiet, verbose, debug)
                pass
            pass
        if dogit and os.path.exists("{path}/{gitdir}".format(path=path, gitdir=gitdir)):
            with pushd.pushd(path) as ctx:
                exec(rc, globals(), dd)
                default = dd["default"]
                default.update(dd["git"])
                doit(default, rest, count, "git", quiet, verbose, debug)
                pass
            pass
        continue
    return

if __name__ == "__main__":
    main()
    pass
