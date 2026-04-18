import shutil, pathlib

site = pathlib.Path("_site")
if site.exists():
    shutil.rmtree(site)
