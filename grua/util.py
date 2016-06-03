import subprocess
from subprocess import call
import os
import re
from mem import mem


def announce(msg, ignore_quiet=False):
    if mem.Mode['noisy'] == 'noisy' or ignore_quiet:
        if not mem.quiet:
            print "\n>>> " + msg + "\n"


def mention(msg, ignore_quiet=False):
    if mem.Mode['noisy'] == 'noisy' or ignore_quiet:
        if not mem.quiet:
            print ">> " + msg


def note(msg, ignore_quiet=False):
    if mem.Mode['noisy'] == 'noisy' or ignore_quiet:
        if not mem.quiet:
            print "> " + msg


def quietcall(command):
    if mem.quiet:
        nullhandle = open(os.devnull, 'w')
        call(command, stdout=nullhandle)
        nullhandle.close()
    else:
        call(command)


def find_bridge_ip():

    done = False
    try:
        command = ["ip", "addr", "show", "dev", "docker0"]
        sp = subprocess.Popen(command, stdout=subprocess.PIPE)

        output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split()[1].split('/')[0]

        done = True

    except OSError as e:
        print ("WARN: OSError Could not use 'ip addr | grep inet' to find bridge ip " + e.message)
    except subprocess.CalledProcessError as e:
        print ("WARN: CalledProcessError Could not use 'ip addr | grep inet' to find bridge ip " + e.message)

    if not done:
        try:
            command = ["ifconfig", "docker0"]

            sp = subprocess.Popen(command, stdout=subprocess.PIPE)

            output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split(':')[1].split()[0]

        except OSError as e:
            print("WARN: OSError Could not use 'ifconfig to find bridge ip " + e.message)
        except subprocess.CalledProcessError as e:
            print("WARN: CalledProcessError Could not use 'ifconfig to find bridge ip " + e.message)

    if not done:
        print("WARN: Continuing without support for BRIDGE_IP expansion")

    sp.wait()

    # ensure we have a valid ip
    p = re.compile(
            '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
    if not p.match(output):
        raise Exception(output + " is not a valid IP address for BridgeIP")

    return output


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

