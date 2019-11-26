#!/usr/bin/env python3
import os, signal, sys
import argparse as ap
import subprocess as sp
import termcolor as tc
from pebble import concurrent
import pushd

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    return

def error(code, *args, **kwargs):
    eprint(*args, **kwargs)
    sys.exit(code)
    return

def check_vars(vars):
    assert "colors" in vars
    assert "default" in vars
    return

def format(st, rc, count):
    while count >= 0:
        nst = st.format(**rc)
        if nst == st: break
        st = nst
        count -= 1
        continue
    return st

def mysystem(cmd):
    try:
        out = sp.check_output(cmd, shell=True, stderr=sp.STDOUT).strip().decode()
        ec = 0
        pass
    except sp.CalledProcessError as exc:
        out = exc.output.strip().decode()
        ec = exc.returncode
        pass
    return ec, out

@concurrent.process
def doit(path, cmd, extra, verbose, debug):
    pheader = "{path} ({extra})".format(path=path, extra=extra)
    cheader = "{cmd}".format(cmd=cmd)
    if verbose >= 4: print(pheader, " ", cheader)
    ec, out = mysystem(cmd)
    if debug:
        print(pheader, cheader, "=", ec)
        print(out)
        pass
    return pheader, cheader, ec, out

def main():
    signal.signal(signalnum = signal.SIGINT, handler = signal.SIG_DFL)
    if os.name == "nt": os.system("color")
    parser = ap.ArgumentParser(description="Walks filesystem executing arbitrary commands", formatter_class=ap.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--command", help="Prefix {cmd}", action="store_true", default=False)
    parser.add_argument("--config", help="Config file", type=str, default=f'{os.environ["HOME"]}/.onsub.py')
    parser.add_argument("--count", help="Count for subsitutions", type=int, default=10)
    parser.add_argument("--debug", help="Debug flag", action="store_true")
    parser.add_argument("--depth", help="Walk depth", type=int, default=-1)
    parser.add_argument("--enable", help="Enabled sections", action="append")
    parser.add_argument("--verbose", help="Verbose", type=int, default=4)
    parser.add_argument("rest", nargs=ap.REMAINDER)
    args = parser.parse_args()
    command = []
    if args.command: command = ["{cmd}"]
    elif len(args.rest) < 1: error(1, "Not enough command arguments")
    rest = " ".join(command + args.rest)
    configfile = args.config
    count = args.count
    debug = args.debug
    depth = args.depth
    enables = []
    if args.enable: enables = args.enable
    verbose = args.verbose

    rcstring = open(configfile).read()
    rc = {}
    exec(rcstring, globals(), rc)
    check_vars(rc)
    markers = {}
    for kk, vv in rc.items():
        if kk == "default" or kk == "colors": continue
        if type(rc[kk]) != type({}): continue
        ignore = True
        try: ignore = rc[kk]["ignore"]
        except KeyError: pass
        if not ignore:
            try: marker = rc[kk]["marker"]
            except KeyError: error(2, "No marker in {kk} section".format(kk=kk))
            if len(enables) == 0 or kk in enables: markers[kk] = marker
            pass
        continue
    colors = rc["colors"]

    root = os.getcwd()
    errors = []
    futures = []
    for path, subdirs, files in os.walk(".", followlinks=True):
        rc = {}
        nsep = path.count(os.path.sep)
        if depth >= 0 and nsep >= depth: continue
        with pushd.pushd(path) as ctx:
            for section, marker in markers.items():
                if marker():
                    exec(rcstring, globals(), rc)
                    default = rc["default"]
                    default.update(rc[section])
                    cmd = format(rest, default, count)
                    future = doit(path, cmd, section, verbose, debug)
                    futures.append(future)
                    pass
                continue
            pass
        continue

    results = []
    for future in futures:
        pheader, cheader, ec, out = future.result()
        results.append((pheader, cheader, ec, out))
        continue

    nerrors = 0
    for pheader, cheader, ec, out in results:
        if ec: nerrors += 1
        if verbose >= 3:
            tc.cprint(pheader, colors["path"], end="")
            tc.cprint(" ", end="")
            tc.cprint(cheader, colors["command"])
            pass
        if verbose >= 2:
            if ec: tc.cprint(out, colors["bad"])
            else: tc.cprint(out, colors["good"])
            pass
        continue

    if nerrors > 0 and verbose >= 1:
        tc.cprint("<<< ERRORS >>>", colors["partition"])
        for pheader, cheader, ec, out in results:
            if not ec: continue
            tc.cprint("({ec})".format(ec=ec), colors["error"], end="")
            tc.cprint(" ", end="")
            tc.cprint(pheader, colors["path"], end="")
            tc.cprint(" ", end="")
            tc.cprint(cheader, colors["command"])
            tc.cprint(out, colors["error"])
            continue
        pass
    return

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
    pass
