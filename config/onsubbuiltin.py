import os
from colorama import Fore, Back, Style
import pushd as pd

colors = {
    "path": Fore.BLUE + Back.RESET + Style.BRIGHT,
    "command": Fore.CYAN + Back.RESET + Style.BRIGHT,
    "errorcode": Fore.RED + Back.RESET + Style.BRIGHT,
    "partition": Fore.YELLOW + Back.RESET + Style.BRIGHT,
    # "good": Fore.GREEN + Back.RESET + Style.BRIGHT,
    # "bad": Fore.MAGENTA + Back.RESET + Style.BRIGHT,
    # "error": Fore.RED + Back.RESET + Style.BRIGHT,
}

def getcwd(path):
    try:
        with pd.pushd(path): return os.getcwd()
        pass
    except FileNotFoundError: pass
    return ""

defdefault = {
    "onsub": "onsub",
    "cwd": lambda v, d, path: getcwd(path),
}
deflinux = {
    "sep": ";",
    "echo": "/bin/echo",
}
defwindows = { "sep": "&", }

default = {}
default.update(defdefault)
if os.name =="nt": default.update(defwindows)
else: default.update(deflinux)

def gitmakecommand(verbose, debug, path, *rest):
    if os.path.exists(path): return None
    assert len(rest) >= 1
    url = rest[0]
    cmd = "{{cmd}} clone {url} {path}".format(url=url, path=path)
    if debug: print(cmd)
    return cmd

def gitpriority(verbose, debug, path): return 4 if os.path.exists(".git") else 0

gitdefault = {
    "type": "echo '(git)' {cwd}",
    "ctype": "echo " + Fore.GREEN + Back.RESET + Style.BRIGHT + "'(git)'" + Fore.RESET + " {cwd}",
    "py:priority": gitpriority, 
    "py:makecommand": gitmakecommand,
    "cmd": "git",
    "remote": "{cmd} remote get-url origin",
    "allremote": "{cmd} remote -v",
    "wcrev": "{cmd} rev-parse --verify --short HEAD",
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
    if os.path.exists(path): return None
    assert len(rest) >= 1
    rrev = ""
    if len(rest) >= 2: rrev = "-r {rev}".format(rev=rest[1])
    url = rest[0]
    cmd = "{{cmd}} clone {url} {path} {rrev}".format(url=url, path=path, rrev=rrev)
    if debug: print(cmd)
    return cmd

def hgpriority(verbose, debug, path): return 3 if os.path.exists(".hg") else 0

hgdefault =  {
    "type": "echo '(hg)' {cwd}",
    "ctype": "echo " + Fore.CYAN + Back.RESET + Style.BRIGHT + "'(hg)'" + Fore.RESET + " {cwd}",
    "py:priority": hgpriority,
    "py:makecommand": hgmakecommand,
    "cmd": "hg",
    "wcrev": "{cmd} id -i",
}
hglinux = {
    "remote": '{cmd} paths default',
    "allremote": '{echo} -n "default = "; {cmd} paths default; {echo} -n "default-push = "; {cmd} paths default-push; {echo} -n "default-pull = "; {cmd} paths default-pull',
}
hgwindows = {
    "remote": '{cmd} paths default',
    "allremote": '{remote}; {cmd} paths default-push; {cmd} paths default-pull',
}

hg = {}
hg.update(default)
hg.update(hgdefault)
if os.name == "nt": hg.update(hgwindows)
else: hg.update(hglinux)
hg["py:enable"] = True

def svnmakecommand(verbose, debug, path, *rest):
    if os.path.exists(path): return None
    assert len(rest) >= 1
    rev = "head"
    if len(rest) >= 2: rev = rest[1]
    url = rest[0]
    cmd = "{{cmd}} checkout {url}@{rev} {path}".format(url=url, path=path, rev=rev)
    if debug: print(cmd)
    return cmd

def svnpriority(verbose, debug, path): return 2 if os.path.exists(".svn") else 0

svndefault = {
    "type": "echo '(svn)' {cwd}",
    "ctype": "echo " + Fore.MAGENTA + Back.RESET + Style.BRIGHT + "'(svn)'" + Fore.RESET + " {cwd}",
    "py:priority": svnpriority,
    "py:makecommand": svnmakecommand,
    "cmd": "svn",
    "remote": "{cmd} info --show-item url",
    "allremote": "{remote}",
    "wcrev": "{cmd} info --show-item revision"
}
svnlinux = {}
svnwindows = {}

svn = {}
svn.update(default)
svn.update(svndefault)
if os.name == "nt": svn.update(svnwindows)
else: svn.update(svnlinux)
svn["py:enable"] = True

def allmakefunction(verbose, debug, path, noexec, *rest):
    if os.path.exists(path): return 0, 'path "{path}" already exists'.format(path=path)
    if verbose >=4: print("os.makedirs({path})".format(path=path))
    if noexec: return 0, "[noexec] os.makedirs({path})".format(path=path)
    os.makedirs(path)
    return 0, "os.makedirs({path})".format(path=path)

def allpriority(verbose, debug, path): return 1

alldefault = {
    "type": "echo '(all)' {cwd}",
    "ctype": "{type}",
    "py:priority": allpriority,
    "py:makefunction": allmakefunction,
}
alllinux = {}
allwindows = {}

all = {}
all.update(default)
all.update(alldefault)
if os.name == "nt": all.update(allwindows)
else: all.update(alllinux)
