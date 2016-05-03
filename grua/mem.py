
import os


class mem: pass


mem.Project = 'grua'  # gets replaced by 'project' value in 'global' from grua.yaml
mem.GruaBase = '/var/lib/grua'
mem.VolumePath = mem.GruaBase + '/volumes'  # replaced by 'global/volumepath' in grua.yaml
mem.ConfigPath = os.environ["HOME"] + "/.grua"

mem.yaml_path = "."
mem.config = {}
mem.sorted_run_deps = []

mem.UnstackTimeout = 15
mem.Dependencies = dict()