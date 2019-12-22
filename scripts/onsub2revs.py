#!/usr/bin/env python3
import re, sys
import subprocess as sp
sectre = re.compile("(.*) \((.+)\)")
args = " ".join(sys.argv[1:])
cmd = 'onsub --nocolor --verbose 3 ' + args + ' "{remote} {sep} {wcrev}"'
try: result = sp.check_output(cmd, shell=True, stderr=sp.DEVNULL).decode()
except sp.CalledProcessError as exc: result = []
sections = {}
folder = section = repo = None
for line in result.splitlines():
    line = line.strip()
    if len(line) == 0 or line == "<<< RESULTS >>>": continue
    if folder and repo:
        rev = line
        sections.setdefault(section, []).append((folder, repo, rev))
        folder = section = repo = None
        continue
    if folder:
        repo = line
        continue
    mm = sectre.match(line)
    if mm and len(mm.groups()) == 2:
        folder = mm.group(1)
        section = mm.group(2)
        pass
    continue
for section, folderrepos in sorted(sections.items()):
    print("{section} = [".format(section=section))
    for folder, repo, rev in sorted(folderrepos):
        print('\t("{folder}", "{repo}", "{rev}"),'.format(folder=folder, repo=repo, rev=rev))
        continue
    print("]")
    continue
