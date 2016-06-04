import os
import yaml
from util import warn, mention
from mem import mem

mem.registries = {}

def load_registries():
    # first load default registry from /var/lib/grua
    load_registry("/var/lib/grua/reg")


def load_registry(reg_spec):
    if reg_spec.startswith("/"):
        if not os.path.isfile(reg_spec + "/reg.yml"):
            warn("Registry " + reg_spec + "/reg.yml does not exist on disk, cannot load")
            return
        load_file_registry(reg_spec)

    #if reg_spec.startswith("git:"):
    #    load_git_registry()

def load_file_registry(reg_spec):
    with open(reg_spec, 'r') as stream:
        cfg = yaml.load(stream)
        if cfg.has_key('registries'):
            for registry in cfg['registries']:
                mention("found registry: " + registry)


