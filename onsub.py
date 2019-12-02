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

def format(st, rc, openbrace, closebrace, count):
    while count >= 0:
        nst = st.format(**rc)
        if nst == st: break
        st = nst
        count -= 1
        continue
    return st.replace(openbrace, "{").replace(closebrace, "}")

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

def work(path, cmd, section, verbose, debug, noexec):
    pheader = "{path} ({section})".format(path=path, section=section)
    cheader = "{cmd}".format(cmd=cmd)
    if verbose >= 4: print(pheader, cheader)
    if noexec: return pheader, cheader, 0, "[noexec] {cmd}".format(cmd=cmd)
    ec, out = mysystem(cmd)
    if debug:
        print(pheader, cheader, "=", ec)
        print(out)
        pass
    return pheader, cheader, ec, out

def cdwork(path, cmd, section, verbose, debug, noexec, cd):
    with pd.pushd(cd): rv = work(path, cmd, section, verbose, debug, noexec)
    return rv

def color(nocolor, colors, color):
    if nocolor: return None
    return colors[color]

class pyfuncfuture:
    def __init__(self, pheader, cheader, ec, out):
        self.pheader = pheader
        self.cheader = cheader
        self.ec = ec
        self.out = out
        return
    def result(self): return self.pheader, self.cheader, self.ec, self.out
    pass

def HOME():
    if os.name != "nt": return os.environ["HOME"]
    homedrive = os.environ["HOMEDRIVE"]
    homepath = os.environ["HOMEPATH"]
    return "{homedrive}/{homepath}".format(homedrive=homedrive, homepath=homepath)

def main():
    signal.signal(signalnum = signal.SIGINT, handler = signal.SIG_DFL)
    if os.name == "nt": os.system("color")
    fc = lambda prog: ap.ArgumentDefaultsHelpFormatter(prog, max_help_position=36, width=120)
    parser = ap.ArgumentParser(description="walks filesystem executing arbitrary commands", formatter_class=fc)
    parser.add_argument("--chdir", help="chdir first", type=str)
    parser.add_argument("--command", help="prefix {cmd}", action="store_true", default=False)
    parser.add_argument("--config", help="config option", action="append")
    parser.add_argument("--configfile", help="config file", type=str, default=f'{HOME()}/.onsub.py')
    parser.add_argument("--count", help="count for substitutions", type=int, default=10)
    parser.add_argument("--debug", help="debug flag", action="store_true")
    parser.add_argument("--depth", help="walk depth", type=int, default=-1)
    parser.add_argument("--disable", help="disable section", action="append")
    parser.add_argument("--dump", help="dump section", action="append")
    parser.add_argument("--dumpall", help="dump all sections", action="store_true", default=False)
    parser.add_argument("--enable", help="enable section", action="append")
    parser.add_argument("--file", help="file with folder names", action="append")
    parser.add_argument("--nocolor", help="disables colorized output", action="store_true", default=False)
    parser.add_argument("--noenable", help="no longer enable any sections", action="store_true", default=False)
    parser.add_argument("--noexec", help="do not actually execute", action="store_true", default=False)
    parser.add_argument("--noop", help="no command execution", action="store_true")
    parser.add_argument("--py:closebrace", dest="pyclosebrace", help="key for py:closebrace", type=str, default="%]")
    parser.add_argument("--py:enable", dest="pyenable", help="key for py:enable", type=str, default="py:enable")
    parser.add_argument("--py:makecommand", dest="pymakecommand", help="key for py:makecommand", type=str, default="py:makecommand")
    parser.add_argument("--py:makefunction", dest="pymakefunction", help="key for py:makefunction", type=str, default="py:makefunction")
    parser.add_argument("--py:openbrace", dest="pyopenbrace", help="key for py:openbrace", type=str, default="%[")
    parser.add_argument("--py:priority", dest="pypriority", help="key for py:priority", type=str, default="py:priority")
    parser.add_argument("--suppress", help="suppress repeated error output", action="store_true")
    parser.add_argument("--verbose", help="verbose level", type=int, default=4)
    parser.add_argument("--workers", help="number of workers", type=int, default=mp.cpu_count())
    parser.add_argument("rest", nargs=ap.REMAINDER)
    args = parser.parse_args()
    command = []
    if args.command: command = ["{cmd}"]
    noop = False
    if args.noop: noop = True
    rest = args.rest
    configfile = args.configfile
    configs = []
    if args.config: configs = args.config
    count = args.count
    debug = args.debug
    noenable = args.noenable
    depth = args.depth
    dumps = []
    if args.dump: dumps = args.dump
    dumpall = args.dumpall
    if not noop and not dumpall and len(dumps) == 0 and len(args.rest) < 1: error(256 - 1, "Not enough command arguments")
    disables = []
    if args.disable: disables = args.disable
    enables = []
    if args.enable: enables = args.enable
    files = []
    if args.file: files = args.file
    nocolor = args.nocolor
    noexec = args.noexec
    suppress = args.suppress
    verbose = args.verbose
    workers = args.workers
    pyclosebrace = args.pyclosebrace
    pyenable = args.pyenable
    pymakefunction = args.pymakefunction
    pymakecommand = args.pymakecommand
    pyopenbrace = args.pyopenbrace
    pypriority = args.pypriority
    if args.chdir: os.chdir(args.chdir)

    paths = {}
    for file in files:
        if not os.path.exists(file): error(256 - 2, 'Input file {file} does not exist'.format(file=file))
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
    
    if not os.path.exists(configfile): error(256 - 3, 'Configuration file {configfile} does not exist'.format(configfile=configfile))
    rcstring = open(configfile).read()
    rc = {}
    exec(rcstring, globals(), rc)
    for config in configs:
        exec(config, globals(), rc)
        continue
    priorities = {}
    dumpFound = False
    for section, vv in rc.items():
        if section == "colors": continue
        if type(rc[section]) != type({}): continue
        if dumpall or section in dumps:
            dumpFound = True
            default = rc[section]
            print("{section} = {{".format(section=section))
            for kk, vv in default.items():
                print("\t{kk} = {vv}".format(kk=kk, vv=vv))
                continue
            print("}")
            continue
        enable = section in enables
        disable = section in disables
        default = rc[section]
        try: defenable = default[pyenable]
        except KeyError: defenable = False
        if ((noenable or not defenable) and not enable) or disable: continue
        try: priority = default[pypriority]
        except KeyError: error(256 - 4, 'No {pypriority} key in {section} section'.format(pypriority=pypriority, section=section))
        priorities[section] = priority
        continue
    if len(dumps) > 0:
        if not dumpFound: error(256 - 5, "No matching sections found")
        return 0

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
            if section in priorities:
                exec(rcstring, globals(), rc)
                default = rc[section]
                makefunction = makecommand = None
                try: makecommand = default[pymakecommand]
                except KeyError:
                    try: makefunction = default[pymakefunction]
                    except: error(256 - 6, 'No "{pymakecommand}" or "{pymakefunction}" key in section {section}'.format(pymakecommand=pymakecommand, pymakefunction=pymakefunction, section=section))
                    pass
                if makecommand:
                    cmd = makecommand(verbose, debug, path, *entry)
                    future = pool.schedule(work, args=[path, cmd, section, verbose, debug, noexec])
                    pass
                else:
                    ec, out = makefunction(verbose, debug, path, noexec, *entry)
                    future = pyfuncfuture(path, makefunction.__name__, ec, out)
                    pass
                if noop:
                    futures.append(future)
                    continue
                future.result()
                pass
            pass

        maxpriority = (0, "")
        for possible, priority in priorities.items():
            if section and section != possible: continue
            with pd.pushd(path): pvalue = priority(verbose, debug, path)
            if pvalue > maxpriority[0]:
                maxpriority = (pvalue, possible)
                pass
            continue
        if maxpriority[0] == 0: continue
        possible = maxpriority[1]
        with pd.pushd(path): exec(rcstring, globals(), rc)
        default = rc[possible]
        if len(rest) > 0 and len(rest[0]) > 2 and rest[0][:3] == "py:":
            cmd = rest[0]
            rem = rest[1:]
            pheader = "{path} ({possible})".format(path=path, possible=possible)
            cheader = "{cmd}".format(cmd=cmd)
            try: pyfunc = default[cmd]
            except KeyError: error(256 - 7, 'No "{cmd}" key in section {possible}'.format(cmd=cmd, possible=possible))
            with pd.pushd(path): ec, out = pyfunc(verbose, debug, path, noexec, *rem)
            future = pyfuncfuture(pheader, cheader, ec, out)
            pass
        else:
            cmd = format(" ".join(command + args.rest), default, pyopenbrace, pyclosebrace, count)
            future = pool.schedule(cdwork, args=[path, cmd, possible, verbose, debug, noexec, path])
            pass
        futures.append(future)
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
            tc.cprint(pheader, color(nocolor, colors, "path"), end="")
            tc.cprint(" ", end="")
            tc.cprint(cheader, color(nocolor, colors, "command"))
            pass
        if verbose >= 2:
            if ec: tc.cprint(out, color(nocolor, colors, "bad"))
            else: tc.cprint(out, color(nocolor, colors, "good"))
            pass
        continue

    if not suppress and verbose >= 1 and nerrors > 0:
        tc.cprint("<<< ERRORS >>>", color(nocolor, colors, "partition"))
        for pheader, cheader, ec, out in results:
            if not ec: continue
            tc.cprint("({ec})".format(ec=ec), color(nocolor, colors, "error"), end="")
            tc.cprint(" ", end="")
            tc.cprint(pheader, color(nocolor, colors, "path"), end="")
            tc.cprint(" ", end="")
            tc.cprint(cheader, color(nocolor, colors, "command"))
            tc.cprint(out, color(nocolor, colors, "error"))
            continue
        pass
    return nerrors

if __name__ == "__main__":
    mp.freeze_support()
    rv = main()
    if rv >= 248: print("Errors exceed 248", file=sys.stderr)
    sys.exit(rv)
