from mem import mem


def sort_containers():
    tups = list()
    for dep in mem.Dependencies.keys():
        tups.append((dep, mem.Dependencies[dep]))

    s = topological_sort(tups)

    sorted_c = list();
    for dummy in mem.Dependencies:
        sorted_c.append(s.next())
    return sorted_c


# http://stackoverflow.com/a/11564323
def topological_sort(source):
    """perform topo sort on elements.

  :arg source: list of ``(name, [list of dependencies])`` pairs
  :returns: list of names, with dependencies listed first
  """
    pending = [(name, set(deps)) for name, deps in source]  # copy deps so we can modify set in-place
    emitted = []
    while pending:
        next_pending = []
        next_emitted = []
        for entry in pending:
            name, deps = entry
            deps.difference_update(emitted)  # remove deps we emitted last pass
            if deps:  # still has deps? recheck during next pass
                next_pending.append(entry)
            else:  # no more deps? time to emit
                yield name
                emitted.append(name)  # <-- not required, but helps preserve original ordering
                next_emitted.append(name)  # remember what we emitted for difference_update() in next pass
        if not next_emitted:  # all entries have unmet deps, one of two things is wrong...
            raise ValueError("cyclic or missing dependency detected: %r" % (next_pending,))
        pending = next_pending
        emitted = next_emitted


def calc_deps(container, config):
    for key in config[container]:
        if not mem.Dependencies.has_key(container):
            mem.Dependencies[container] = []
        val = config[container][key]
        if key == "before":
            for before in val:
                if before not in mem.Dependencies:
                    mem.Dependencies[before] = [container]
                else:
                    mem.Dependencies[before].append(container)

        if key == "after":
            if container not in mem.Dependencies:
                mem.Dependencies[container] = val
            else:
                for after in val:
                    if after not in mem.Dependencies[container]:
                        mem.Dependencies[container].append(after)
