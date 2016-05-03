#!/usr/bin/env python
from collections import deque
from util import find_bridge_ip, touch
from docker import *


mem.BridgeIp = find_bridge_ip()


def edit_yaml():
    announce("Editing " + mem.yaml_path)
    command = [os.environ['EDITOR'], mem.yaml_path + '/grua.yaml']
    note(" ".join(command))
    call(command)


def edit_dockerfile(container):
    announce("Editing dockerfile for " + container)
    command = [os.environ['EDITOR'], mem.yaml_path + '/' + container + "/Dockerfile"]
    note(" ".join(command))
    call(command)


def print_mode():
    Mode = get_mode()
    print Mode['noisy'] + ", " + Mode['destructive']




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


def run_tests():

    # create new volumepath for this test run

    orig_path = mem.VolumePath

    mem.VolumePath += "_tests"

    shutil.rmtree(mem.VolumePath, True)
    os.mkdir(mem.VolumePath)

    # TODO - Actually run some tests here with the cleared down volume_path

    # reset volume path
    mem.VolumePath = orig_path


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
