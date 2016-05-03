#!/usr/bin/env python
import shutil, os.path, time, subprocess, shlex, re
from collections import deque
from subprocess import call
from mem import mem


def announce(msg, ignore_quiet=False):
    if mem.Mode['noisy'] == 'noisy' or ignore_quiet:
        print "\n>>> " + msg + "\n"


def mention(msg, ignore_quiet=False):
    if mem.Mode['noisy'] == 'noisy' or ignore_quiet:
        print ">> " + msg


def note(msg, ignore_quiet=False):
    if mem.Mode['noisy'] == 'noisy' or ignore_quiet:
        print "> " + msg


def find_bridge_ip():
    done = False
    try:
        command = ["ip", "addr", "show", "dev", "docker0"]
        sp = subprocess.Popen(command, stdout=subprocess.PIPE)

        output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split()[1].split('/')[0]

        done = True

    except OSError as e:
        if e.errno == os.errno.ENOENT:
            # handle file not found error.
            done = False
        else:
            # Something else went wrong
            raise

    if not done:
        try:
            command = ["ifconfig", "docker0"]

            sp = subprocess.Popen(command, stdout=subprocess.PIPE)

            output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split(':')[1].split()[0]

        except OSError as e:
            if e.errno == os.errno.ENOENT:
                # handle file not found error.
                done = False
            else:
                raise

    if not done:
        raise Exception("Could not find either 'ip' or 'ifconfig' in PATH")

    sp.wait()

    # ensure we have a valid ip
    p = re.compile(
            '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
    if not p.match(output):
        raise Exception(output + " is not a valid IP address for BridgeIP")

    return output


mem.BridgeIp = find_bridge_ip()














def edit_yaml():
    announce("Editing " + mem.yamlpath)
    command = [os.environ['EDITOR'], mem.yamlpath + '/grua.yaml']
    note(" ".join(command))
    call(command)


def edit_dockerfile(container):
    announce("Editing dockerfile for " + container)
    command = [os.environ['EDITOR'], mem.yamlpath + '/' + container + "/Dockerfile"]
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
        # which = [commands.popleft()]
        # exclude here commands which cannot take multiple container names but instead take further args
        if command != "enter":
            which = commands
    else:
        deps = mem.sorted_run_deps
        deps.remove('global')
        which = deps

    if command == 'fill':
        for container in which:
            fill_container(container, mem.config[container])

    elif command == 'stack':
        for container in which:
            if mem.config[container].has_key('run') and not mem.config[container]['run']:
                pass
            else:
                stack_container(container, mem.config[container])

    elif command == 'unstack':
        for container in reversed(which):

            if mem.config[container].has_key('run') and not mem.config[container]['run']:
                pass
            else:
                unstack_container(container)

    elif command == 'restack':
        for container in which:

            if mem.config[container].has_key('run') and not mem.config[container]['run']:
                pass
            else:
                unstack_container(container)
                stack_container(container, mem.config[container])

    elif command == "status":
        for container in which:
            if mem.config[container].has_key('run') and not mem.config[container]['run']:
                pass
            else:
                container_status(container)

        Mode = get_mode()
        print "Mode is " + Mode['noisy'] + ", " + Mode['destructive']

    elif command == "empty":
        for container in reversed(which):
            unstack_container(container)
            empty_container(container, mem.config[container])

    elif command == "refill":
        for container in which:
            unstack_container(container)
        if Mode['destructive'] == 'destructive':
            empty_container(container, mem.config[container])
        fill_container(container, mem.config[container])

    elif command == "enter":
        # if len(which) > 1:
        #    raise(Exception("You may only enter one container at a time. Please provide container name"))

        enter_container(commands)

    elif command == "refstk":
        if len(which) > 1:
            raise (Exception("You may only refstk one container at a time. Please provide container name"))

        container = which[0]

        unstack_container(container)
        if Mode['destructive'] == 'destructive':
            empty_container(container, mem.config[container])
        fill_container(container, mem.config[container])
        stack_container(container, mem.config[container])

    elif command == "edit":
        edit_yaml()

    elif command == "editd":
        for container in which:
            if mem.config[container].has_key('build'):
                edit_dockerfile(container)

    elif command == "mode":
        MODE_USAGE = "Mode can either be 'noisy', 'quiet', 'destructive', 'conservative'"
        if len(command_list) == 1:
            print_mode()
            return
        mode = command_list[1]
        config_path = mem.ConfigPath + "/" + mem.Project

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

    elif command == "test":
        run_tests()

    else:
        raise Exception("Unknown command '" + command + "'")


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)




def find_yaml_location():
    pathname = os.path.curdir
    while pathname != '/':
        if os.path.isfile(pathname + '/grua.yaml'):
            return pathname
        pathname = os.path.abspath(os.path.join(pathname, os.pardir))

    raise (IOError("grua.yaml file not found"))


def get_mode():
    noisy = 'noisy'
    destructive = 'destructive'
    if os.path.isfile(mem.ConfigPath + "/" + mem.Project + "/quiet"):
        noisy = 'quiet'
    if os.path.isfile(mem.ConfigPath + "/" + mem.Project + "/conservative"):
        destructive = 'conservative'

    return {"noisy": noisy, "destructive": destructive}


def usage():
    Mode = get_mode()
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
