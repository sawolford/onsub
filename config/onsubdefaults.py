localpy = f"{HOME()}/.onsublocal.py"
if os.path.exists(localpy): exec(open(localpy).read(), globals(), locals())
