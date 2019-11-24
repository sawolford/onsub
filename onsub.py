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
    parser.add_argument("--enable", help="Enabled sections", action="append")
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
    enables = []
    if args.enable: enables = args.enable
    quiet = args.quiet
    verbose = args.verbose
    if len(args.rest) < 1: error(1, "Not enough command arguments")
    rest = " ".join(command + args.rest)

    rc = open(config).read()
    dd = {}
    exec(rc, globals(), dd)
    check_vars(dd)
    markers = {}
    for kk, vv in dd.items():
        if kk == "default": continue
        try: marker = dd[kk]["marker"]
        except KeyError: error(2, "No marker in {kk} section".format(kk=kk))
        if len(enables) == 0 or kk in enables: markers[kk] = marker
        continue

    root = os.getcwd()
    for path, subdirs, files in os.walk(".", followlinks=True):
        dd = {}
        nsep = path.count(os.path.sep)
        if depth >= 0 and nsep > depth: continue
        for section, marker in markers.items():
            markerfile = "{path}/{marker}".format(path=path, marker=marker)
            if os.path.exists(markerfile):
                with pushd.pushd(path) as ctx:
                    exec(rc, globals(), dd)
                    default = dd["default"]
                    default.update(dd[section])
                    doit(default, rest, count, section, quiet, verbose, debug)
                    pass
                pass
            continue
        continue
    return

if __name__ == "__main__":
    main()
    pass
