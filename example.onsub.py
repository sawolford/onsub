colors = {
    "path": "blue",
    "command": "cyan",
    "good": "green",
    "bad": "magenta",
    "error": "red",
    "partition": "yellow",
}

defdefault = {}

deflinux = {}
if os.name != "nt":
    deflinux = {
        "cwd": f'{sp.check_output("pwd").strip().decode()}',
        "echo": "/bin/echo",
    }
    pass

defwindows = {}

default = {}
default.update(defdefault)
if os.name =="nt": default.update(defwindows)
else: default.update(deflinux)
default["ignore"] = False

def hgmissing(path, url, rev, verbose, debug):
    cmd = "hg clone {url} {path} -r {rev}".format(path=path, url=url, rev=rev)
    print(cmd)
    ec, out = mysystem(cmd)
    print(out)
    return

hgdefault =  {
    "marker": lambda: os.path.exists(".hg"),
    "missing": hgmissing,
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
hg.update(hgdefault)
if os.name == "nt": hg.update(hgwindows)
else: hg.update(hglinux)
hg["ignore"] = False

def gitmissing(path, url, rev, verbose, debug):
    cmd = "git clone {url} {path}".format(path=path, url=url, rev=rev)
    print(cmd)
    ec, out = mysystem(cmd)
    print(out)
    return

gitdefault = {
    "marker": lambda: os.path.exists(".git"),
    "missing": gitmissing,
    "cmd": "git",
    "get": "{cmd} pull",
    "remotes": "{cmd} remote -v",
    "allremotes": "{remotes}",
}

gitlinux = {}
gitwindows = {}

git = {}
git.update(gitdefault)
if os.name == "nt": git.update(gitwindows)
else: git.update(gitlinux)
git["ignore"] = False

def svnmissing(path, url, rev, verbose, debug):
    cmd = "svn checkout {url} {path}".format(path=path, url=url, rev=rev)
    print(cmd)
    ec, out = mysystem(cmd)
    print(out)
    return

svndefault = {
    "marker": lambda: os.path.exists(".svn"),
    "missing": svnmissing,
    "cmd": "svn",
    "get": "{cmd} up",
    "remotes": "{cmd} info --show-item url",
    "allremotes": "{remotes}",
}

svnlinux = {}
svnwindows = {}

svn = {}
svn.update(svndefault)
if os.name == "nt": svn.update(svnwindows)
else: svn.update(svnlinux)
svn["ignore"] = False

every = {
    "marker": lambda: True,
    "ignore": True,
}
