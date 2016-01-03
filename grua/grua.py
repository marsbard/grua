#!/usr/bin/env python
import shutil, os.path, time, subprocess, shlex, re
from collections import deque
from subprocess import call

Project = 'grua'  # gets replaced by 'project' value in 'global' from grua.yaml
GruaBase = '/var/lib/grua'
VolumePath = GruaBase + '/volumes' # replaced by 'global/volumepath' in grua.yaml
ConfigPath = os.environ["HOME"] + "/.grua"

UnstackTimeout = 15
Dependencies = dict()


def announce(msg):
    if Mode['noisy'] == 'noisy':
        print "\n>>> " + msg + "\n"

def mention(msg):
    if Mode['noisy'] == 'noisy':
        print ">> " + msg

def note(msg):
    if Mode['noisy'] == 'noisy':
        print "> " + msg





def find_bridge_ip():
    command = ["ip", "addr", "show", "dev", "docker0"]
    sp = subprocess.Popen((command), stdout=subprocess.PIPE)

    output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split()[1].split('/')[0]

    sp.wait()

    # ensure we have a valid ip
    p = re.compile(
        '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
    if not p.match(output):
        raise Exception(output + " is not a valid IP address for BridgeIP")

    return output

BridgeIp = find_bridge_ip()




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




def inspect_container(container, go_template):
    command = ['docker', 'inspect', '-f', (" ").join(go_template), get_container(container)]

    note(" ".join(command))
    return subprocess.check_output(command, stderr=subprocess.STDOUT).strip()

def tpl_lookup(template):
    words = template.split()
    selecta = words[0]

    words.pop(0)

    if selecta == "ENV":
        return os.environ.get(words[0], '')

    if selecta == "INSPECT":
        container = words[0]
        words.pop(0)
        return inspect_container(container, words)

    if selecta == "GRUA":
        key = words[0]
        words.pop(0)
        if key == 'BRIDGE_IP':
            return BridgeIp
        if key == "PROJECT":
            return Project



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


def get_value(dict, key):
    if not dict.has_key(key):
        return ''
    return parse_template(dict[key])


def calc_deps(container, config):
    for key in config[container]:
        if not Dependencies.has_key(container):
            Dependencies[container] = []
        val = config[container][key]
        if key == "before":
            for before in val:
                if before not in Dependencies:
                    Dependencies[before] = [container]
                else:
                    Dependencies[before].append(container)

        if key == "after":
            if container not in Dependencies:
                Dependencies[container] = val
            else:
                for after in val:
                    if after not in Dependencies[container]:
                        Dependencies[container].append(after)


def fill_container(container, config):
    announce("Filling "  + container + " container")
    if config.has_key('build'):
        tag = Project + "/" + container
        if config.has_key('tag'):
            tag = get_value(config, 'tag')

        build = get_value(config, 'build')
        target = build
        if build[:4] == 'git:':
            if not config.has_key('tag'):
                raise Exception("If you are using a git repo for 'build' you must also specify 'tag'")
            tag = get_value(config,'tag')

            url = build[4:]
            print "Cloning " + tag + " from " + url
            dir = "_grua_" + tag.replace("/", "_")

            if os.path.isdir(dir):
                shutil.rmtree(dir)

            command = ['git', 'clone', url, dir]
            note (" ".join(command))
            call(command)
            target = dir

        mention("building " + container + " ( " + target + " ) " + " with tag '" + tag + "'")
        command = ['docker', 'build', '-t', tag, target]
        note (" ".join(command))
        call(command)
    else:
        mention(container + " uses an image. Pulling " + get_value(config, 'image'))
        command = ['docker', 'pull', get_value(config, 'image')]
        note (" ".join(command))
        call(command)


def wait_for_up(container, config):
    upwhen = config['upwhen']
    timeout = 30
    if upwhen.has_key('timeout'):
        timeout = get_value(upwhen, 'timeout')

    if upwhen.has_key('logmsg'):
        logmsg = get_value(upwhen, 'logmsg')

    mention("Waiting for '" + logmsg + "' to indicate that " + container + " is stacked")
    waited = 0
    ok = False
    while waited <= timeout:
        command = ["docker", "logs", get_container(container)]

        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
        if output.find(logmsg) > 0:
            ok = True
            break
        else:
            time.sleep(1)
            waited = waited + 1

    if upwhen.has_key('sleep'):
        mention("Sleeping " + str(upwhen['sleep']) + " extra seconds as configured")
        time.sleep(int(upwhen['sleep']))

    if not ok:
        raise Exception("Timed out waiting for " + container + " to start")


def get_image(config):
    if config.has_key('image'):
        image = get_value(config, 'image')  # .split(':')[0]
    elif config.has_key('tag'):
        image = get_value(config, 'tag')
    else:
        image = Project + '/' + get_value(config, 'build')

    return image

def get_container(name):
    return Project + "_" + name

def stack_container(container, config):
    announce("Stacking " + container + " container")
    if config.has_key('run') and not config['run']:
        note ("container has 'run' key set to " + str(config['run']) + ", skipping")
        return

    command = ['docker', 'run', '-d', '--name', get_container(container)]

    if config.has_key('options'):
        for option in config['options']:
            command = command + [parse_template(option)]

    if config.has_key('hostname'):
        command = command + ['--hostname', get_value(config, 'hostname')]
    else:
        command = command + ['--hostname', container]

    if config.has_key('dns'):
        command = command + ['--dns', get_value(config, 'dns')]

    if config.has_key('volumes'):
        for volumespec in config['volumes']:
            if volumespec.startswith("/"):
                command = command + ['-v', parse_template(volumespec)]
            else:
                command = command + ['-v', VolumePath + "/" + Project + "/" + container + "/" + parse_template(volumespec)]

    if config.has_key('ports'):
        for portspec in config['ports']:
            command = command + ['-p', parse_template(portspec)]

    if config.has_key('environment'):
        for envvar in config['environment']:
            command = command + ['-e', parse_template(envvar) + '=' + parse_template(config['environment'][envvar])]

    if config.has_key('link'):
        for link in config['link']:
            command = command + ["--link=" + get_container(parse_template(link))]

    command.append(get_image(config))

    if config.has_key('command'):
        command = command + shlex.split(get_value(config, 'command'))

    note(" ".join(command))
    call(command)

    if config.has_key('upwhen'):
        wait_for_up(container, config)


def unstack_container(container):
    announce("Unstacking " + container + " container")
    command = ['docker', 'stop', get_container(container)]
    note (" ".join(command))
    call(command)

    command = ['docker', 'rm', '--force', get_container(container)]
    note (" ".join(command))
    call(command)


def container_status(container):
    command = ['docker', 'inspect', '--format="{{.State.Status}}"', get_container(container)]
    # note(" ".join(command))
    try:
        result = subprocess.check_output(command, stderr=subprocess.STDOUT)
        if result == "running\n":
            output = "^ stacked ^"
        else:
            output = result
    except subprocess.CalledProcessError:
        output = "_ unstacked _"

    mention(container + ": " + output),

def empty_container(container, config):
    announce("Emptying image " + container)
    command = ['docker', 'rmi', get_image(config)]
    note(" ".join(command))
    call(command)


def enter_container(which, commands):
    run=["/bin/bash"]
    if len(commands) > 0:
        run = list(commands)
    announce("Entering '" + which[0] + "' container and running: " + str(run))
    command = ['docker', 'exec', '-ti', get_container(which[0])] + run
    note(" ".join(command))
    call(command)


def edit_yaml():
    announce("Editing " + yamlpath)
    command = [os.environ['EDITOR'], yamlpath + '/grua.yaml']
    note(" ".join(command))
    call(command)


def edit_dockerfile(container):
    announce("Editing dockerfile for " + container)
    command = [os.environ['EDITOR'], yamlpath + '/' + container + "/Dockerfile"]
    note(" ".join(command))
    call(command)


def print_mode():
    Mode = get_mode()
    print Mode['noisy'] + ", " + Mode['destructive']

def process_command(command_list):
    Mode = get_mode()

    commands = deque(command_list)

    command = commands.popleft()

    if len(commands) > 0:
        which = [commands.popleft()]
    else:
        deps = sorted_run_deps
        deps.remove('global')
        which = deps

    if command == 'fill':
        for container in which:
            fill_container(container, config[container])

    elif command == 'stack':
        for container in which:
            if config[container].has_key('run') and not config[container]['run']:
                pass
            else:
                stack_container(container, config[container])

    elif command == 'unstack':
        for container in reversed(which):

            if config[container].has_key('run') and not config[container]['run']:
                pass
            else:
                unstack_container(container)

    elif command == 'restack':
        for container in which:

            if config[container].has_key('run') and not config[container]['run']:
                pass
            else:
                unstack_container(container)
                stack_container(container, config[container])

    elif command == "status":
        for container in which:
            if config[container].has_key('run') and not config[container]['run']:
                pass
            else:
                container_status(container)

    elif command == "empty":
        for container in reversed(which):
            unstack_container(container)
            empty_container(container, config[container])

    elif command == "refill":
        for container in which:
            unstack_container(container)
        if Mode['destructive']=='destructive':
            empty_container(container, config[container])
        fill_container(container, config[container])
            
    elif command == "enter":
        if len(which) > 1:
            raise(Exception("You may only enter one container at a time. Please provide container name"))

        enter_container(which, commands)

    elif command == "refstk":
        if len(which) > 1:
            raise(Exception("You may only refstk one container at a time. Please provide container name"))

        container = which[0]

        unstack_container(container)
        if Mode['destructive']=='destructive':
            empty_container(container, config[container])
        fill_container(container, config[container])
        stack_container(container, config[container])

    elif command == "edit":
        edit_yaml()

    elif command == "editd":
        for container in which:
            if config[container].has_key('build'):
                edit_dockerfile(container)

    elif command == "mode":
        MODE_USAGE="Mode can either be 'noisy', 'quiet', 'destructive', 'conservative'"
        if len(command_list) == 1:
            print_mode()
            return
        mode = command_list[1]
        config_path = ConfigPath + "/" + Project

        quietFile = config_path + "/quiet"
        noisyFile = config_path + "/noisy"
        destructFile = config_path + "/destructive"
        conserveFile = config_path + "/conservative"

        if mode == "noisy":
            if os.path.isfile(quietFile):
                os.remove(quietFile)
            touch(noisyFile)
        elif mode == "quiet":
            if os.path.isfile(noisyFile):
                os.remove(noisyFile)
            touch(quietFile)
        elif mode == "destructive":
            if os.path.isfile(conserveFile):
                os.remove(conserveFile)
            touch(destructFile)
        elif mode == "conservative":
            if os.path.isfile(destructFile):
                os.remove(destructFile)
            touch(conserveFile)
        else:
            print MODE_USAGE
            return

        print_mode()

    else:
        raise Exception("Unknown command '" + command + "'")


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

def sort_containers():
    tups = list()
    for dep in Dependencies.keys():
        tups.append((dep, Dependencies[dep]))

    s = topological_sort(tups)

    sorted = list();
    for dummy in Dependencies:
        sorted.append(s.next())
    return sorted


def find_yaml_location():
    pathname = os.path.curdir
    while pathname != '/':
        if os.path.isfile(pathname + '/grua.yaml'):
            return pathname
        pathname = os.path.abspath(os.path.join(pathname, os.pardir))

    raise (IOError("grua.yaml file not found"))

def get_mode():
    noisy='noisy'
    destructive='destructive'
    if os.path.isfile(ConfigPath + "/" + Project + "/quiet"):
        noisy='quiet'
    if os.path.isfile(ConfigPath + "/" + Project + "/conservative"):
        destructive='conservative'

    return { "noisy": noisy, "destructive": destructive}


def usage():
    print "                grua\n                ----"
    print "              //\\  ___"
    print "              Y  \\/_/=|"
    print "             _L  ((|_L_|"
    print "            (/\)(__(____) cjr\n"
    print "   grua fill\t\tBuild requisite containers"
    print "   grua empty\t\tDestroy all the related images"
    print "   grua refill\t\tEmpty followed by fill - rebuild image(s)"
    print
    print "   grua stack\t\tRun container composition"
    print "   grua unstack\t\tStop and remove container composition"
    print "   grua restack\t\tUnstack and restack container composition"
    print
    print "   grua enter\t\tEnter container, run bash or opt args"
    print "   grua status\t\tShow status of containers"
    print "   grua edit\t\tEdit grua.yaml from within subfolder"
    print "   grua editd\t\tEdit Dockerfile(s) from within subfolder"
    print
    print "   grua mode\t\tSet operating mode"
    print 
    print "> grua mode is currently: " + Mode['noisy'] + ", " + Mode['destructive'] 
    print 



