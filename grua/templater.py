import os
import docker
from mem import mem


def tpl_lookup(template):
    words = template.split()
    selecta = words[0]

    words.pop(0)

    if selecta == "ENV":
        # declaration something like <% ENV VARNAME %> or <% ENV VARNAME | default value words words words %>

        # varname is first
        varname = words.pop(0)

        # strip the first pipe character if found
        if ("|" in words):
            words.remove('|')

        # use remaining words if any as default if the varname not found in the environment
        default = ' '.join(words)
        value = os.environ.get(varname, '')

        if value == '':
            value = default

        return value

    if selecta == "INSPECT":
        container = words[0]
        words.pop(0)
        return docker.inspect_container(container, words)

    if selecta == "GRUA":
        key = words[0]
        words.pop(0)
        if key == 'BRIDGE_IP':
            return mem.BridgeIp
        if key == "PROJECT":
            return mem.Project


def get_value(dict, key):
    if not dict.has_key(key):
        return ''
    return parse_template(dict[key])


def parse_template(tpl):
    a1 = str(tpl).split("<%")
    if len(a1) == 1:
        return tpl
    out = a1[0]
    for i in range(1, len(a1)):
        a2 = a1[i].split("%>")
        for j in range(0, len(a2)):
            if j % 2 == 1:
                out += a2[j]
            else:
                out += tpl_lookup(a2[j].strip())

    return out

