colors = {
#     "path": "blue",
#     "command": "cyan",
#     "good": "green",
#     "bad": "magenta",
#     "error": "red",
#     "partition": "yellow",
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
    "cwd": f"{os.getcwd()}",
}

deflinux = {
    "sep": ";",
    "echo": "/bin/echo",
    "lswcl": "ls | wc -l",
}

defwindows = {
    "sep": "&",
}

default = {}
default.update(defdefault)
if os.name =="nt": default.update(defwindows)
else: default.update(deflinux)

def gitmakecommand(verbose, debug, path, *rest):
    assert len(rest) >= 1
    url = rest[0]
    cmd = "git clone {url} {path}".format(url=url, path=path)
    if debug: print(cmd)
    return cmd

gitdefault = {
    "py:priority": lambda verbose, debug, path: 4 if os.path.exists(".git") else 0,
    "py:makecommand": gitmakecommand,
    "cmd": "git",
    "write": "{cmd} ci -a",
    "get": "{cmd} pull",
    "put": "{cmd} push",
    "remotes": "{cmd} remote -v",
    "allremotes": "{remotes}",
}

gitlinux = {}
gitwindows = {}

git = {}
git.update(default)
git.update(gitdefault)
if os.name == "nt": git.update(gitwindows)
else: git.update(gitlinux)
git["py:enable"] = True

def hgmakecommand(verbose, debug, path, *rest):
    assert len(rest) >= 1
    rrev = ""
    if len(rest) >= 2: rrev = "-r {rev}".format(rev=rest[1])
    url = rest[0]
    cmd = "hg clone {url} {path} {rrev}".format(url=url, path=path, rrev=rrev)
    if debug: print(cmd)
    return cmd

def hgwrite(verbose, debug, path, noexec, *rest):
    cmd = " ".join(["hg ci"] + list(rest))
    if noexec: return 0, "[noexec] {cmd}".format(cmd=cmd)
    return mycheck_call(cmd)

hgdefault =  {
    "py:priority": lambda verbose, debug, path: 3 if os.path.exists(".hg") else 0,
    "py:makecommand": hgmakecommand,
    "cmd": "hg",
    "py:write": hgwrite,
    "write": "{cmd} ci",
    "get": "{cmd} pull --update",
    "put": "{cmd} push",
}

hglinux = {
    "remotes": '{echo} -n "default = "; {cmd} paths default',
    "allremotes": '{remotes}; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull',
}

hgwindows = {
    "remotes": '{cmd} paths default',
    "allremotes": '{remotes}; {cmd} paths default-push; {cmd} paths default-pull',
}

hg = {}
hg.update(default)
hg.update(hgdefault)
if os.name == "nt": hg.update(hgwindows)
else: hg.update(hglinux)
hg["py:enable"] = True

def svnmakecommand(verbose, debug, path, *rest):
    assert len(rest) >= 1
    rev = "head"
    if len(rest) >= 2: rev = rest[1]
    url = rest[0]
    cmd = "svn checkout {url}@{rev} {path}".format(url=url, path=path, rev=rev)
    if debug: print(cmd)
    return cmd

svndefault = {
    "py:priority": lambda verbose, debug, path: 2 if os.path.exists(".svn") else 0,
    "py:makecommand": svnmakecommand,
    "cmd": "svn",
    "write": "{cmd} [noop]",
    "get": "{cmd} up",
    "put": "{cmd} ci",
    "remotes": "{cmd} info --show-item url",
    "allremotes": "{remotes}",
}

svnlinux = {}
svnwindows = {}

svn = {}
svn.update(default)
svn.update(svndefault)
if os.name == "nt": svn.update(svnwindows)
else: svn.update(svnlinux)
svn["py:enable"] = True

def everymakefunction(verbose, debug, path, noexec, *rest):
    if verbose >=4: print("os.makedirs({path})".format(path=path))
    if noexec: return 0, "[noexec] os.makedirs({path})".format(path=path)
    os.makedirs(path)
    return 0, "os.makedirs({path})".format(path=path)

everydefault = {
    "py:priority": lambda verbose, debug, path: 1,
    "py:makefunction": everymakefunction,
}

everylinux = {}
everywindows = {}

every = {}
every.update(default)
every.update(everydefault)
if os.name == "nt": every.update(everywindows)
else: every.update(everylinux)

localpy = f"{HOME()}/.onsub,local.py"
if os.path.exists(localpy): exec(open(localpy).read(), globals(), locals())
