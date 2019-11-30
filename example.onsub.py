colors = {
#     "path": "blue",
#     "command": "cyan",
#     "good": "green",
#     "bad": "magenta",
#     "error": "red",
#     "partition": "yellow",
}

def fileCheck(verbose, debug, path, *args):
    if len(args) != 1: return 1, "fileCheck: wrong number of arguments"
    fname = args[0]
    if verbose >= 4: print("os.path.exists({fname})".format(fname=fname))
    exists = os.path.exists(fname)
    fpath = "{path}/{fname}".format(path=path, fname=fname)
    if exists: return 0, "{fpath} exists".format(fpath=fpath)
    return 1, "{fpath} does not exist".format(fpath=fpath)

defdefault = {
    "py:fileCheck": fileCheck,
}

deflinux = {
    "echo": "/bin/echo",
    "lswcl": "ls | wc -l",
}
if os.name != "nt": deflinux["cwd"] = f'{sp.check_output("pwd").strip().decode()}'

defwindows = {}

default = {}
default.update(defdefault)
if os.name =="nt": default.update(defwindows)
else: default.update(deflinux)

def gitmakecommand(verbose, debug, path, *rest):
    assert len(rest) >= 1
    url = rest[0]
    cmd = "git clone {url} {path}".format(path=path, url=url)
    if debug: print(cmd)
    return cmd

gitdefault = {
    "py:include": lambda verbose, debug, path: os.path.exists(".git"),
    "py:makecommand": gitmakecommand,
    "cmd": "git",
    "get": "{cmd} pull",
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
    cmd = "hg clone {url} {path} {rrev}".format(path=path, url=url, rrev=rrev)
    if debug: print(cmd)
    return cmd

hgdefault =  {
    "py:include": lambda verbose, debug, path: os.path.exists(".hg"),
    "py:makecommand": hgmakecommand,
    "cmd": "hg",
    "get": "{cmd} pull --update",
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
    cmd = "svn checkout {url}@{rev} {path}".format(path=path, url=url, rev=rev)
    if debug: print(cmd)
    return cmd

svndefault = {
    "py:include": lambda verbose, debug, path: os.path.exists(".svn"),
    "py:makecommand": svnmakecommand,
    "cmd": "svn",
    "get": "{cmd} up",
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

def everymakefunction(verbose, debug, path, *rest):
    if verbose >=4: print("os.makedirs({path})".format(path=path))
    os.makedirs(path)
    return 0, "os.makedirs({path})".format(path=path)

everydefault = {
    "py:include": lambda verbose, debug, path: True,
    "py:makefunction": everymakefunction,
}

everylinux = {}
everywindows = {}

every = {}
every.update(default)
every.update(everydefault)
if os.name == "nt": every.update(everywindows)
else: every.update(everylinux)
