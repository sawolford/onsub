#!/usr/bin/env python3
import re, sys

if len(sys.argv) != 2:
    print("Usage: {0} <folder>".format(sys.argv[0]), file=sys.stderr)
    sys.exit(1)
    pass
folder = sys.argv[1]
hgguestrepo = "{folder}/.hgguestrepo".format(folder=folder)
hggrmapping = "{folder}/.hggrmapping".format(folder=folder)

tokre = re.compile('=| ')
def tokenize(lines):
    global tokre
    rv = []
    for line in lines:
        tokens = tokre.split(line[:-1])
        tokens = [tok for tok in tokens if len(tok) > 0]
        rv.append(tokens)
        continue
    return rv

guestrepotok = tokenize(open(hgguestrepo).readlines())
grmappingtok = tokenize(open(hggrmapping).readlines())

guestrepo = {}
includerev = False
for name, sym, rev in guestrepotok:
    if rev != "default": includerev = True
    guestrepo[name] = (sym, rev)
    continue

grmapping = {}
for name, repo in grmappingtok:
    grmapping[name] = repo
    continue

print("hg = [")
for name, (sym, rev) in guestrepo.items():
    repo = grmapping[name]
    print('    ("', end="")
    print(name, end="")
    print('", "', end="")
    print(repo, end="")
    if includerev:
        print('", "', end="")
        print(rev, end="")
        pass
    print('"),')
    continue
print("]")