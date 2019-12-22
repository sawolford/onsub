#!/usr/bin/env python3
import os, signal, sys, time
import argparse as ap
import subprocess as sp
import multiprocessing as mp
import colorama as ca
from colorama import Fore, Back, Style
import pebble as pb
import runpy as rp
import hashlib as hl
import pushd as pd
import config.onsubbuiltin as od

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    return

def error(code, *args, **kwargs):
    eprint(*args, **kwargs)
    sys.exit(code)
    return

def substitute(st, rc, openbrace, closebrace, count):
    while count >= 0:
        try: nst = st.format(**rc)
        except ValueError as exc: error(256 - 9, "Invalid substitution string: {exc}".format(exc=exc))
        except KeyError as exc: error(256 - 10, "Substitution not found: {exc}".format(exc=exc))
        if nst == st: break
        st = nst
        count -= 1
        continue
    return st.replace(openbrace, "{").replace(closebrace, "}")

def check_call(cmd):
    try: ec = sp.check_call(cmd, shell=True)
    except sp.CalledProcessError as exc: ec = exc.returncode
    return ec, "{cmd}".format(cmd=cmd)

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

def work(path, cmd, section, verbose, debug, noexec):
    pheader = "{path} ({section})".format(path=path, section=section)
    cheader = "{cmd}".format(cmd=cmd)
    if verbose >= 4: print(pheader, cheader)
    if noexec: return pheader, cheader, 0, "[noexec] {cmd}".format(cmd=cmd)
    ec, out = check_output(cmd)
    if debug:
        print(pheader, cheader, "=", ec)
        print(out)
        pass
    return pheader, cheader, ec, out

def cdwork(path, cmd, section, verbose, debug, noexec, cd):
    with pd.pushd(cd): rv = work(path, cmd, section, verbose, debug, noexec)
    return rv

def tocolor(fcolor, colors, color):
    if not fcolor: return ""
    try: return colors[color]
    except KeyError: pass
    try: od.colors[color]
    except KeyError: pass
    return ""

class pyfuncfuture:
    def __init__(self, pheader, cheader, ec, out):
        self.pheader = pheader
        self.cheader = cheader
        self.ec = ec
        self.out = out
        return
    def done(self): return True
    def cancel(self): return
    def result(self): return self.pheader, self.cheader, self.ec, self.out
    pass

def HOME():
    if "HOME" in os.environ: return os.environ["HOME"]
    if "USERPROFILE" in os.environ: return os.environ["USERPROFILE"]
    if "HOMEDRIVE" in os.environ and "HOMEPATH" in os.environ: return "{}/{}".format(homedrive, homepath)
    return "NO HOME"

def display(verbose, color, colors, pheader, cheader, ec, out):
    out = out.strip()
    if verbose >= 3:
        print(tocolor(color, colors, "path") + pheader, end="")
        print(" ", end="")
        print(tocolor(color, colors, "command") + cheader)
        pass
    if verbose >= 2 and len(out):
        if ec: print(tocolor(color, colors, "bad") + out)
        else: print(tocolor(color, colors, "good") + out)
        pass
    return

def genParser():
    fc = lambda prog: ap.RawDescriptionHelpFormatter(prog, max_help_position=36, width=120)
    parser = ap.ArgumentParser(description="walks filesystem executing arbitrary commands", formatter_class=fc)
    parser.add_argument("--chdir", help="chdir first", type=str)
    parser.add_argument("--color", help="enables colorized output", action="store_true", default=None)
    parser.add_argument("--comment", help="ignored", type=str)
    parser.add_argument("--configfile", help="config file", type=str)
    parser.add_argument("--count", help="count for substitutions", type=int)
    parser.add_argument("--debug", help="debug flag", action="store_true", default=None)
    parser.add_argument("--depth", help="walk depth", type=int)
    parser.add_argument("--disable", help="disable section", action="append")
    parser.add_argument("--discard", help="discard error codes", action="store_true", default=None)
    parser.add_argument("--dump", help="dump section", action="append")
    parser.add_argument("--dumpall", help="dump all sections", action="store_true", default=None)
    parser.add_argument("--enable", help="enable section", action="append")
    parser.add_argument("--file", help="file with folder names", action="append")
    parser.add_argument("--hashed", help="check hashes of unknown files", action="store_true", default=None)
    parser.add_argument("--ignore", help="ignore folder names", action="append")
    parser.add_argument("--invert", help="invert error codes", action="store_true", default=None)
    parser.add_argument("--make", help="make folders", action="store_true", default=None)
    parser.add_argument("--nocolor", help="disables colorized output", action="store_true", default=None)
    parser.add_argument("--noenable", help="no longer enable any sections", action="store_true", default=None)
    parser.add_argument("--noexec", help="do not actually execute", action="store_true", default=None)
    parser.add_argument("--nofile", help="ignore file options", action="store_true", default=None)
    parser.add_argument("--nohashed", help="do not check hashes of unknown files", action="store_true", default=None)
    parser.add_argument("--noignore", help="ignore ignore options", action="store_true", default=None)
    parser.add_argument("--nomake", help="do not make folders", action="store_true", default=None)
    parser.add_argument("--preconfig", help="preconfig option", action="append")
    parser.add_argument("--postconfig", help="postconfig option", action="append")
    parser.add_argument("--py:closebrace", dest="pyclosebrace", help="key for py:closebrace", type=str)
    parser.add_argument("--py:enable", dest="pyenable", help="key for py:enable", type=str)
    parser.add_argument("--py:makecommand", dest="pymakecommand", help="key for py:makecommand", type=str)
    parser.add_argument("--py:makefunction", dest="pymakefunction", help="key for py:makefunction", type=str)
    parser.add_argument("--py:openbrace", dest="pyopenbrace", help="key for py:openbrace", type=str)
    parser.add_argument("--py:priority", dest="pypriority", help="key for py:priority", type=str)
    parser.add_argument("--sleepmake", help="sleep between make calls", type=float)
    parser.add_argument("--sleepcommand", help="sleep between command calls", type=float)
    parser.add_argument("--suppress", help="suppress repeated error output", action="store_true", default=None)
    parser.add_argument("--verbose", help="verbose level", type=int)
    parser.add_argument("--workers", help="number of workers", type=int)
    parser.add_argument("rest", nargs=ap.REMAINDER)
    return parser

def option(*args):
    for arg in args:
        if arg is not None: return arg
        continue
    return None
def opt(flag, value): return value if flag else None
def optnot(arg): return True if arg == False else (False if arg == True else None)

futures = []
def sighandler(signum, frame):
    global futures
    for future in futures: future.cancel()
    sys.exit()
    return

def waitFutures(verbose, debug, color, colors, discard, invert, futures):
    results = []
    while True:
        nfutures = []
        for future in futures:
            if future.done():
                pheader, cheader, ec, out = future.result()
                if verbose >= 5: display(verbose, color, colors, pheader, cheader, ec, out)
                results.append((pheader, cheader, 0 if discard else (ec if not invert else not ec), out))
                pass
            else: nfutures.append(future)
            continue
        if len(nfutures) == 0: break
        futures = nfutures
        continue
    return results

def dispResults(verbose, debug, color, colors, partition, results):
    nerrors = 0
    if len(results):
        if verbose >= 3: print(tocolor(color, colors, "partition") + partition)
        for pheader, cheader, ec, out in results:
            if ec: nerrors += 1
            display(verbose, color, colors, pheader, cheader, ec, out)
            continue
        pass
    return nerrors

def readConfig(configfile, preconfigs=[], postconfigs=[]):
    rc = od.__dict__.copy()
    rc["HOME"] = HOME
    rc["check_call"] = check_call
    rc["check_output"] = check_output
    for config in preconfigs:
        exec(config, globals(), rc)
        continue
    if type(configfile) == type("") and os.path.exists(configfile): rc.update(rp.run_path(configfile, rc))
    for config in postconfigs:
        exec(config, globals(), rc)
        continue
    return rc

def rcPython(verbose, debug, path, rc):
    rc = rc.copy()
    for key, value in rc.items():
        if len(key) > 2 and key[:3] != "py:" and callable(value): rc[key] = value(verbose, debug, path)
        continue
    return rc

def main():
    global futures
    signal.signal(signalnum=signal.SIGINT, handler=signal.SIG_IGN)
    ca.init(autoreset=True)
    parser = genParser()
    try: onsub = os.environ["ONSUB"].split()
    except KeyError: onsub = []
    cmdargs = parser.parse_args(onsub + sys.argv[1:])
    homepy = f'{HOME()}/.onsub.py'
    if getattr(sys, "frozen", False): cmdname = sys.executable
    else: cmdname = __file__
    exepy = "{dir}/config/onsubdefaults.py".format(dir=os.path.realpath(os.path.dirname(cmdname)))
    configfile = option(cmdargs.configfile, homepy if os.path.exists(homepy) else (exepy if os.path.exists(exepy) else None))
    rc = readConfig(configfile)
    rcarguments = rc["arguments"] if "arguments" in rc else []
    rchashes = rc["hashes"] if "hashes" in rc else []
    fileargs = parser.parse_args(rcarguments)
    chdir = option(cmdargs.chdir)
    color = option(cmdargs.color, optnot(cmdargs.nocolor), fileargs.color, optnot(fileargs.nocolor), True)
    count = option(cmdargs.count, fileargs.count, 10)
    debug = option(cmdargs.debug, fileargs.debug, False)
    depth = option(cmdargs.depth, -1)
    disables = (cmdargs.disable or []) + (fileargs.disable or [])
    discard = option(cmdargs.discard, False)
    dumps = cmdargs.dump or []
    dumpall = option(cmdargs.dumpall, False)
    enables = (cmdargs.enable or []) + (fileargs.enable or [])
    hashed = option(cmdargs.hashed, optnot(cmdargs.nohashed), fileargs.hashed, optnot(fileargs.nohashed), True)
    invert = option(cmdargs.invert, False)
    noenable = option(cmdargs.noenable, fileargs.noenable, False)
    noexec = option(cmdargs.noexec, fileargs.noexec, False)
    nofile = option(cmdargs.nofile, fileargs.nofile, False)
    files = (cmdargs.file or []) + (fileargs.file or []) if not nofile else []
    noignore = option(cmdargs.noignore, fileargs.noignore, False)
    ignores = (cmdargs.ignore or []) + (fileargs.ignore or []) if not noignore else []
    make = option(cmdargs.make, optnot(cmdargs.nomake), fileargs.make, optnot(fileargs.nomake), False)
    preconfigs = option(cmdargs.preconfig, [])
    postconfigs = option(cmdargs.preconfig, [])
    pyclosebrace = option(cmdargs.pyclosebrace, fileargs.pyclosebrace, "%]")
    pyenable = option(cmdargs.pyenable, fileargs.pyenable, "py:enable")
    pymakecommand = option(cmdargs.pymakecommand, fileargs.pymakecommand, "py:makecommand")
    pymakefunction = option(cmdargs.pymakefunction, fileargs.pymakefunction, "py:makefunction")
    pyopenbrace = option(cmdargs.pyopenbrace, fileargs.pyopenbrace, "%[")
    pypriority = option(cmdargs.pypriority, fileargs.pypriority, "py:priority")
    sleepmake = option(cmdargs.sleepmake, fileargs.sleepmake, 0.1)
    sleepcommand = option(cmdargs.sleepcommand, fileargs.sleepcommand, 0)
    suppress = option(cmdargs.suppress, fileargs.suppress, False)
    verbose = option(cmdargs.verbose, fileargs.verbose, 4)
    workers = option(cmdargs.workers, fileargs.workers, mp.cpu_count())
    rest = cmdargs.rest
    noop = True if not dumpall and len(dumps) == 0 and len(rest) < 1 else False
    if chdir: os.chdir(chdir)

    paths = {}
    for file in files:
        if not os.path.exists(file): error(256 - 1, 'Input file "{file}" does not exist'.format(file=file))
        hd = hl.sha256(open(file).read().encode()).hexdigest()
        if hashed and hd not in rchashes: error(256 - 2, 'Input file "{file}" does not have allowed hash ({hd})'.format(file=file, hd=hd))
        rc = readConfig(file, preconfigs, postconfigs)
        for section in rc:
            if section in ["python_path", "futures"]: continue
            rcsection = rc[section]
            if type(rcsection) != type([]): continue
            for path in rcsection:
                paths.setdefault(section, []).append(path)
                continue
            continue
        continue
    

    def pathIterate(ignores):
        for root, dirs, files in os.walk(".", followlinks=True, topdown=True):
            dirs[:] = [d for d in dirs if d not in ignores]
            yield root, None, None
        return
    def fileIterate(ignores, paths=paths):
        for section in paths:
            for entry in paths[section]:
                if type(entry) == type(""): yield entry, section, None
                else: yield entry[0], section, entry[1:]
                continue
            continue
        return
    
    rc = readConfig(configfile, preconfigs, postconfigs)
    colors = rc["colors"]
    priorities = {}
    dumpFound = False
    for section, vv in rc.items():
        if section == "colors" or section == "__builtins__": continue
        if type(rc[section]) != type({}): continue
        if dumpall or section in dumps:
            dumpFound = True
            rcsection = rc[section]
            print("{section} = {{".format(section=section))
            for kk, vv in rcsection.items():
                print("\t{kk} = {vv}".format(kk=kk, vv=vv))
                continue
            print("}")
            continue
        enable = section in enables
        disable = section in disables
        rcsection = rc[section]
        try: defenable = rcsection[pyenable]
        except KeyError: defenable = False
        if ((noenable or not defenable) and not enable) or disable: continue
        try: priority = rcsection[pypriority]
        except KeyError: error(256 - 3, 'No {pypriority} key in {section} section'.format(pypriority=pypriority, section=section))
        priorities[section] = priority
        continue
    if len(dumps) > 0:
        if not dumpFound: error(256 - 4, "No matching sections found")
        return 0

    pool = pb.ProcessPool(max_workers=workers)
    signal.signal(signal.SIGINT, sighandler)

    for path, section, entry in fileIterate(ignores):
        if not make: continue
        if not entry: entry = tuple()
        if section not in priorities: continue
        rcsection = rcPython(verbose, debug, path, rc[section])
        makefunction = makecommand = None
        try: makecommand = rcsection[pymakecommand]
        except KeyError:
            try: makefunction = rcsection[pymakefunction]
            except: error(256 - 6, 'No "{pymakecommand}" or "{pymakefunction}" key in section {section}'.format(pymakecommand=pymakecommand, pymakefunction=pymakefunction, section=section))
            pass
        time.sleep(sleepmake)
        if makecommand:
            cmd = makecommand(verbose, debug, path, *entry)
            if not cmd: continue
            cmd = substitute(cmd, rcsection, pyopenbrace, pyclosebrace, count)
            future = pool.schedule(work, args=[path, cmd, section, verbose, debug, noexec])
            pass
        else:
            ec, out = makefunction(verbose, debug, path, noexec, *entry)
            future = pyfuncfuture(path, makefunction.__name__, ec, out)
            pass
        futures.append(future)
        continue
    results = waitFutures(verbose, debug, color, colors, discard, invert, futures)
    nerrors = dispResults(verbose, debug, color, colors, "<<< MAKE >>>", results)
    if noop: return nerrors

    root = os.getcwd()
    futures = []
    errors = []
    if len(files) > 0: cmdIterate = fileIterate
    else: cmdIterate = pathIterate
    for path, fsection, _ in cmdIterate(ignores):
        if not os.path.isdir(path): error(256 - 7, 'Folder "{path}" does not exist.'.format(path=path))
        nsep = path.count(os.path.sep)
        if depth >= 0 and nsep >= depth: continue
        if len(path) > 2 and (path[0:2] == "./" or path[0:2] == ".\\"): path = path[2:]
        if fsection:
            section = fsection
            if section not in priorities: continue
        else:
            maxsection = (0, "")
            for section, priority in priorities.items():
                with pd.pushd(path): pvalue = priority(verbose, debug, path)
                if pvalue > maxsection[0]:
                    maxsection = (pvalue, section)
                    pass
                continue
            if maxsection[0] == 0: continue
            section = maxsection[1]
            pass
        rcsection = rcPython(verbose, debug, path, rc[section])
        time.sleep(sleepcommand)
        if len(rest) > 0 and len(rest[0]) > 2 and rest[0][:3] == "py:":
            cmd = rest[0]
            rem = rest[1:]
            pheader = "{path} ({section})".format(path=path, section=section)
            cheader = "{cmd}".format(cmd=cmd)
            try: pyfunc = rcsection[cmd]
            except KeyError: error(256 - 8, 'No "{cmd}" key in section {section}'.format(cmd=cmd, section=section))
            with pd.pushd(path): ec, out = pyfunc(verbose, debug, path, noexec, *rem)
            future = pyfuncfuture(pheader, cheader, ec, out)
            if verbose >= 6: display(verbose, color, colors, pheader, cheader, ec, out)
            pass
        else:
            command = rest[0]
            if command[0] == "\\": command = command[1:]
            elif command in rcsection: command = "{{{command}}}".format(command=command)
            cmd = substitute(" ".join([command] + rest[1:]), rcsection, pyopenbrace, pyclosebrace, count)
            future = pool.schedule(cdwork, args=[path, cmd, section, verbose, debug, noexec, path])
            pass
        futures.append(future)
        continue
    results = waitFutures(verbose, debug, color, colors, discard, invert, futures)

    nerrors = dispResults(verbose, debug, color, colors, "<<< RESULTS >>>", results)
    if not suppress and verbose >= 1 and nerrors > 0:
        print(tocolor(color, colors, "partition") + "<<< ERRORS >>>")
        for pheader, cheader, ec, out in results:
            if not ec: continue
            print(tocolor(color, colors, "errorcode") + "({ec})".format(ec=ec), end="")
            print(" ", end="")
            print(tocolor(color, colors, "path") + pheader, end="")
            print(" ", end="")
            print(tocolor(color, colors, "command") + cheader)
            if len(out): print(tocolor(color, colors, "error") + out.strip())
            continue
        pass
    return nerrors

if __name__ == "__main__":
    mp.freeze_support()
    rv = main()
    if rv >= 245: print("Errors exceed 245", file=sys.stderr)
    sys.exit(rv)
