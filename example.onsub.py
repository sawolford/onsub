colors = {
#     "path": "blue",
#     "command": "cyan",
#     "good": "green",
#     "bad": "magenta",
#     "error": "red",
#     "partition": "yellow",
}

defdefault = {}

deflinux = {
    "echo": "/bin/echo",
}
if os.name != "nt": deflinux["cwd"] = f'{sp.check_output("pwd").strip().decode()}'

defwindows = {}

default = {}
default.update(defdefault)
if os.name =="nt": default.update(defwindows)
else: default.update(deflinux)
default["py:private"] = False

def hgmissing(verbose, debug, path, *rest):
    assert len(rest) >= 1
    rrev = ""
    if len(rest) >= 2: rrev = "-r {rev}".format(rev=rest[1])
    url = rest[0]
    cmd = "hg clone {url} {path} {rrev}".format(path=path, url=url, rrev=rrev)
    if verbose >= 4: print(cmd)
    ec, out = mysystem(cmd)
    if verbose >= 5: print(out)
    return ec, out

def fileCheck(path, *args):
    if len(args) != 1: return 1, "fileCheck: wrong number of arguments"
    fname = args[0]
    exists = os.path.exists(fname)
    fpath = "{path}/{fname}".format(path=path, fname=fname)
    if exists: return 0, "{fpath} exists".format(fpath=fpath)
    return 1, "{fpath} does not exist".format(fpath=fpath)

hgdefault =  {
    "py:include": lambda: os.path.exists(".hg"),
    "py:missing": hgmissing,
    "cmd": "hg",
    "get": "{cmd} pull --update",
    "py:fileCheck": fileCheck,
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
hg.update(hgdefault)
if os.name == "nt": hg.update(hgwindows)
else: hg.update(hglinux)
hg["py:private"] = False

def gitmissing(verbose, debug, path, *rest):
    assert len(rest) >= 1
    url = rest[0]
    cmd = "git clone {url} {path}".format(path=path, url=url)
    if verbose >= 4: print(cmd)
    ec, out = mysystem(cmd)
    if verbose >= 5: print(out)
    return ec, out

gitdefault = {
    "py:include": lambda: os.path.exists(".git"),
    "py:missing": gitmissing,
    "cmd": "git",
    "get": "{cmd} pull",
    "remotes": "{cmd} remote -v",
    "allremotes": "{remotes}",
    "py:fileCheck": fileCheck,
}

gitlinux = {}
gitwindows = {}

git = {}
git.update(gitdefault)
if os.name == "nt": git.update(gitwindows)
else: git.update(gitlinux)
git["py:private"] = False

def svnmissing(verbose, debug, path, *rest):
    assert len(rest) >= 1
    rev = "head"
    if len(rest) >= 2: rev = rest[1]
    url = rest[0]
    cmd = "svn checkout {url}@{rev} {path}".format(path=path, url=url, rev=rev)
    if verbose >= 4: print(cmd)
    ec, out = mysystem(cmd)
    if verbose >= 5: print(out)
    return ec, out

svndefault = {
    "py:include": lambda: os.path.exists(".svn"),
    "py:missing": svnmissing,
    "cmd": "svn",
    "get": "{cmd} up",
    "remotes": "{cmd} info --show-item url",
    "allremotes": "{remotes}",
    "py:fileCheck": fileCheck,
}

svnlinux = {}
svnwindows = {}

svn = {}
svn.update(svndefault)
if os.name == "nt": svn.update(svnwindows)
else: svn.update(svnlinux)
svn["py:private"] = False

def everymissing(verbose, debug, path, *rest):
    os.makedirs(path)
    return 0, "os.makedirs({path})".format(path=path)

every = {
    "py:include": lambda: True,
    "py:missing": everymissing,
    "py:private": True,
}
