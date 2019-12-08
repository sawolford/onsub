#!/usr/bin/env python3
import re, sys
import subprocess as sp
sectre = re.compile("(.*) \((.+)\)")
cmd = "onsub --nocolor --verbose 3 --noop " + " ".join(sys.argv[1:])
try: result = sp.check_output(cmd, shell=True, stderr=sp.DEVNULL).decode()
except sp.CalledProcessError as exc: result = []
sections = {}
for line in result.splitlines():
    line = line.strip()
    if len(line) == 0 or line == "<<< RESULTS >>>": continue
    mm = sectre.match(line)
    if mm and len(mm.groups()) == 2:
        folder = mm.group(1)
        section = mm.group(2)
        sections.setdefault(section, []).append(folder)
        pass
    continue
for section, folders in sections.items():
    print("{section} = [".format(section=section))
    for folder in folders:
        print('\t("{folder}"),'.format(folder=folder))
        continue
    print("]")
    continue
