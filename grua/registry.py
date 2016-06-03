import os
from util import warn

registries = {}


def load_registries():
    # first load default registry from /var/lib/grua
    load_registry("/var/lib/grua/reg")


def load_registry(reg_spec):
    if reg_spec.startswith("/"):
        if not os.path.isfile(reg_spec + "/reg.yml"):
            warn(reg_spec + " does not exist on disk")
            return
        load_file_registry(reg_spec)

    #if reg_spec.startswith("git:"):
    #    load_git_registry()

def load_file_registry(reg_spec):
    with open(reg_spec)

def register_stack(tag, spec):
    pass
