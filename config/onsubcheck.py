from colorama import Fore, Back, Style

gitlinux = { "put": '{cmd} commit -a -e -m "# $(pwd)"', }
gitwindows = { "put": "{cmd} commit -a", }
gitnew = {
    # helpers
    "mtool": "kdiff3",
    "stash2wc": "{cmd} stash pop",
    "index2wc": "{cmd} reset --mixed",
    "mergetool": "{cmd} mergetool -y --tool={mtool}",
    "sync": "{cmd} fetch",
    "rebcon": "{cmd} rebase --continue",
    "cleanup": "{cmd} reflog expire --expire=now --all",
    # commands
    "check": "gitcheck",
    "stow": "{cmd} stash",
    "unstow": "{stash2wc} {sep} {mergetool} {sep} {index2wc} {sep} {cmd} stash clear",
    "upload": "{cmd} push",
    "combine": "{mergetool} {sep} {rebcon}",
    "download": "{sync} {sep} {stow} {sep} {cmd} rebase --interactive origin/master {sep} {combine}",
    "st": "{cmd} status --short",
    "in": "{cmd} log --pretty=oneline ..origin/master",
    "out": "{cmd} log --pretty=oneline origin/master..",
    "di": "{cmd} --no-pager diff --color"
}
git.update(gitnew)
if os.name == "nt": git.update(gitwindows)
else: git.update(gitlinux)

hglinux = { "put": '{cmd} commit -e -m "HG: $(pwd)"', }
hgwindows = { "put": "{cmd} commit", }
hgnew = {
    # helpers
    "sync": "{cmd} pull",
    # commands
    "check": "hgcheck",
    "stow": "{cmd} shelve",
    "unstow": "{cmd} unshelve",
    "upload": "{cmd} push",
    "download": "{stow} {sep} {cmd} pull --rebase",
    "st": "{cmd} status -q",
    "in": "{cmd} in -q",
    "out": "{cmd} out -q",
    "di": "{cmd} diff --pager never --color always"
}
hg.update(hgnew)
if os.name == "nt": hg.update(hgwindows)
else: hg.update(hglinux)

svnnew = {
    # commands
    "check": "svncheck",
    "upload": "echo [unimplemented]",
    "download": "echo [unimplemented]",
    "put": "echo [unimplemented]",
    "get": "echo [unimplemented]",
    "download": "svn update --accept l",
    "upload": "svn commit",
    "st": "{cmd} status -q",
    "di": "{cmd} diff"
}
svn.update(svnnew)
