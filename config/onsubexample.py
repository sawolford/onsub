arguments = [
    # "--chdir", ".",
    # "--color",
    # "--comment", "ignored",
    # "--count", "10",
    # "--debug",
    # "--depth", "1",
    # "--disable", "all",
    # "--discard",
    # "--dump",
    # "--dumpall",
    # "--enable", "all",
    # "--file", "subs.py",
    # "--hashed",
    # "--ignore", ".hg", "--ignore", ".git", "--ignore", ".svn",
    # "--invert",
    # "--make",
    # "--nocolor",
    # "--noenable",
    # "--noexec",
    # "--nofile",
    # "--nohashed",
    # "--noignore",
    # "--nomake",
    # "--norecurse",
    # "--preconfig", "",
    # "--postconfig", "",
    # "--py:closebrace", "%]",
    # "--py:enable", "py:enable",
    # "--py:makecommand", "py:makecommand",
    # "--py:makefunction", "py:makefunction",
    # "--py:openbrace", "%[",
    # "--py:priority", "py:priority",
    # "--recurse",
    # "--sleepmake", ".1",
    # "--sleepcommand", "0",
    # "--suppress",
    # "--verbose", "5",
    # "--workers", "8",
]

colors = {
    # "path": Fore.BLUE + Back.RESET + Style.BRIGHT,
    # "command": Fore.CYAN + Back.RESET + Style.BRIGHT,
    # "errorcode": Fore.RED + Back.RESET + Style.BRIGHT,
    # "partition": Fore.YELLOW + Back.RESET + Style.BRIGHT,
    # "good": Fore.GREEN + Back.RESET + Style.BRIGHT,
    # "bad": Fore.MAGENTA + Back.RESET + Style.BRIGHT,
    # "error": Fore.RED + Back.RESET + Style.BRIGHT,
}

def fileCheck(verbose, debug, path, noexec, *args):
    if len(args) != 1: return 1, "fileCheck: wrong number of arguments"
    fname = args[0]
    if verbose >= 4: print("os.path.exists({fname})".format(fname=fname))
    if noexec: return 0, "[noexec] py:fileCheck"
    exists = os.path.exists(fname)
    fpath = "{path}/{fname}".format(path=path, fname=fname)
    if exists: return 0, "{fpath} exists".format(fpath=fpath)
    return 1, "{fpath} does not exist".format(fpath=fpath)

defdefault = {
    "py:fileCheck": fileCheck,
}
deflinux = {
    "lswcl": "ls | wc -l",
}
defwindows = {}

default = {}
default.update(defdefault)
if os.name =="nt": default.update(defwindows)
else: default.update(deflinux)

gitdefault = {
}
gitlinux = {}
gitwindows = {}

git = {}
git.update(default)
git.update(gitdefault)
if os.name == "nt": git.update(gitwindows)
else: git.update(gitlinux)
git["py:enable"] = True

hgdefault =  {}
hglinux = {}
hgwindows = {}

hg = {}
hg.update(default)
hg.update(hgdefault)
if os.name == "nt": hg.update(hgwindows)
else: hg.update(hglinux)
hg["py:enable"] = True

svndefault = {}
svnlinux = {}
svnwindows = {}

svn = {}
svn.update(default)
svn.update(svndefault)
if os.name == "nt": svn.update(svnwindows)
else: svn.update(svnlinux)
svn["py:enable"] = True

alldefault = {}
alllinux = {}
allwindows = {}

all = {}
all.update(default)
all.update(alldefault)
if os.name == "nt": all.update(allwindows)
else: all.update(alllinux)

localpy = f"{HOME()}/.onsublocal.py"
if os.path.exists(localpy): exec(open(localpy).read(), globals(), locals())
