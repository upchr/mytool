# app/core/db/registry.py

# from app.modules.note.models import *
# from app.modules.node.models import *
# from app.modules.cron.models import *
# from app.modules.notify.models import *
# from app.modules.sys.models import *
import pkgutil
import importlib

for importer, modname, ispkg in pkgutil.iter_modules(['app/modules']):
    if ispkg:
        importlib.import_module(f'app.modules.{modname}.models')
