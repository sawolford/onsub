#!/usr/bin/env python3
import os, signal, sys
import argparse as ap
import subprocess as sp
import multiprocessing as mp
import termcolor as tc
import pushd as pd
import pebble as pb

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

def work(path, cmd, section, verbose, debug):
    pheader = "{path} ({section})".format(path=path, section=section)
    cheader = "{cmd}".format(cmd=cmd)
    if verbose >= 4: print(pheader, cheader)
    ec, out = mysystem(cmd)
    if debug:
        print(pheader, cheader, "=", ec)
        print(out)
        pass
    return pheader, cheader, ec, out

def cdwork(path, cmd, section, verbose, debug, cd):
    with pd.pushd(cd): rv = work(path, cmd, section, verbose, debug)
    return rv

class pyfuncfuture:
    def __init__(self, pheader, cheader, ec, out):
        self.pheader = pheader
        self.cheader = cheader
        self.ec = ec
        self.out = out
        return
    def result(self): return self.pheader, self.cheader, self.ec, self.out
    pass

def main():
    signal.signal(signalnum = signal.SIGINT, handler = signal.SIG_DFL)
    if os.name == "nt": os.system("color")
    fc = lambda prog: ap.ArgumentDefaultsHelpFormatter(prog, max_help_position=32)
    parser = ap.ArgumentParser(description="Walks filesystem executing arbitrary commands", formatter_class=fc)
    parser.add_argument("--command", help="Prefix {cmd}", action="store_true", default=False)
    parser.add_argument("--config", help="Config option", action="append")
    parser.add_argument("--configfile", help="Config file", type=str, default=f'{os.environ["HOME"]}/.onsub.py')
    parser.add_argument("--count", help="Count for subsitutions", type=int, default=10)
    parser.add_argument("--debug", help="Debug flag", action="store_true")
    parser.add_argument("--depth", help="Walk depth", type=int, default=-1)
    parser.add_argument("--enable", help="Enabled sections", action="append")
    parser.add_argument("--file", help="File with folder names", action="append")
    parser.add_argument("--noop", help="No command execution", action="store_true")
    parser.add_argument("--py:include", dest="include", help="Key for py:include", type=str, default="py:include")
    parser.add_argument("--py:makecommand", dest="makecommand", help="Key for py:makecommand", type=str, default="py:makecommand")
    parser.add_argument("--py:makefunction", dest="makefunction", help="Key for py:makefunction", type=str, default="py:makefunction")
    parser.add_argument("--py:private", dest="private", help="Key for py:private", type=str, default="py:private")
    parser.add_argument("--suppress", help="Suppress repeated error output", action="store_true")
    parser.add_argument("--verbose", help="Verbose level", type=int, default=4)
    parser.add_argument("--workers", help="Number of workers", type=int, default=mp.cpu_count())
    parser.add_argument("rest", nargs=ap.REMAINDER)
    args = parser.parse_args()
    command = []
    if args.command: command = ["{cmd}"]
    noop = False
    if args.noop: noop = True
    elif len(args.rest) < 1: error(256 - 1, "Not enough command arguments")
    rest = args.rest
    configfile = args.configfile
    configs = []
    if args.config: configs = args.config
    count = args.count
    debug = args.debug
    depth = args.depth
    enables = []
    if args.enable: enables = args.enable
    files = []
    if args.file: files = args.file
    suppress = args.suppress
    verbose = args.verbose
    workers = args.workers
    pyinclude = args.include
    pymakefunction = args.makefunction
    pymakecommand = args.makecommand
    pyprivate = args.private

    paths = {}
    for file in files:
        rc = {}
        exec(open(file).read(), globals(), rc)
        for section in rc:
            for path in rc[section]:
                paths.setdefault(section, []).append(path)
                continue
            continue
        continue

    def pathIterate():
        for root, dirs, files in os.walk(".", followlinks=True): yield root, None, None
        return
    if len(paths):
        def pathIterate(paths=paths):
            for section in paths:
                for entry in paths[section]:
                    if type(entry) == type(""): yield entry, section, None
                    else: yield entry[0], section, entry[1:]
                    continue
                continue
            return
        pass
    
    rcstring = open(configfile).read()
    rc = {}
    exec(rcstring, globals(), rc)
    check_vars(rc)
    for config in configs:
        exec(config, globals(), rc)
        continue
    includes = {}
    for kk, vv in rc.items():
        if kk == "default" or kk == "colors": continue
        if type(rc[kk]) != type({}): continue
        private = True
        try: private = rc[kk][pyprivate]
        except KeyError: pass
        if not private:
            try: include = rc[kk][pyinclude]
            except KeyError: error(256 - 2, 'No {pyinclude} key in {kk} section'.format(pyinclude=pyinclude, kk=kk))
            if len(enables) == 0 or kk in enables: includes[kk] = include
            pass
        continue
    colors = {
        "path": "blue",
        "command": "cyan",
        "good": "green",
        "bad": "magenta",
        "error": "red",
        "partition": "yellow",
    }
    try: colors.update(rc["colors"])
    except KeyError: pass

    pool = pb.ProcessPool(max_workers=workers)
    root = os.getcwd()
    errors = []
    futures = []
    for path, section, entry in pathIterate():
        if not entry: entry = tuple()
        rc = {}
        nsep = path.count(os.path.sep)
        if depth >= 0 and nsep >= depth: continue
        if not os.path.exists(path):
            exec(rcstring, globals(), rc)
            default = rc["default"]
            default.update(rc[section])
            makefunction = makecommand = None
            try: makecommand = rc[section][pymakecommand]
            except KeyError:
                try: makefunction = rc[section][pymakefunction]
                except: error(256 - 3, 'No "{pymakecommand}" or "{pymakefunction}" key in section {section}'.format(pymakecommand=pymakecommand, pymakefunction=pymakefunction, section=section))
                pass
            if len(enables) == 0 or section in enables:
                if makecommand:
                    cmd = makecommand(verbose, debug, path, *entry)
                    future = pool.schedule(work, args=[path, cmd, section, verbose, debug])
                    pass
                else:
                    ec, out = makefunction(verbose, debug, path, *entry)
                    future = pyfuncfuture(path, makefunction.__name__, ec, out)
                    pass
                if noop:
                    futures.append(future)
                    continue
                future.result()
                pass
            pass
        for possible, include in includes.items():
            if section and section != possible: continue
            with pd.pushd(path): doinclude = include(verbose, debug, path)
            if doinclude:
                with pd.pushd(path): exec(rcstring, globals(), rc)
                default = rc["default"]
                default.update(rc[possible])
                if len(rest) > 0 and len(rest[0]) > 2 and rest[0][:3] == "py:":
                    cmd = rest[0]
                    rem = rest[1:]
                    pheader = "{path} ({section})".format(path=path, section=section)
                    cheader = "{cmd}".format(cmd=cmd)
                    try: pyfunc = rc[section][cmd]
                    except KeyError: error(256 - 4, 'No "{cmd}" key in section {section}'.format(cmd=cmd, section=section))
                    with pd.pushd(path): ec, out = pyfunc(verbose, debug, path, *rem)
                    future = pyfuncfuture(pheader, cheader, ec, out)
                    pass
                else:
                    cmd = format(" ".join(command + args.rest), default, count)
                    future = pool.schedule(cdwork, args=[path, cmd, section, verbose, debug, path])
                    pass
                futures.append(future)
                pass
            continue
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

    if not suppress and verbose >= 1 and nerrors > 0:
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
    return nerrors

if __name__ == "__main__":
    mp.freeze_support()
    rv = onsub.main()
    if rv >= 251: print("Errors exceed 251", file=sys.stderr)
    sys.exit(rv)
