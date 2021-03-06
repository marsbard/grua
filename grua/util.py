import subprocess
from subprocess import call
import os
import re
import sys
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


def warn(msg):
        sys.stderr.write(">> " + msg + "\n")


def quietcall(command):
    if mem.quiet:
        nullhandle = open(os.devnull, 'w')
        call(command, stdout=nullhandle)
        nullhandle.close()
    else:
        call(command)


def find_bridge_ip():

    done = False
    output = ""

    try:
        command = ["ip", "addr", "show", "dev", "docker0"]
        sp = subprocess.Popen(command, stdout=subprocess.PIPE)

        output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split()[1].split('/')[0]

        done = True

    except OSError as e:
        pass
    except subprocess.CalledProcessError as e:
        pass

    if not done:
        try:
            command = ["ifconfig", "docker0"]

            sp = subprocess.Popen(command, stdout=subprocess.PIPE)

            output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split(':')[1].split()[0]
            sp.wait()
            
        except OSError as e:
            pass
        except subprocess.CalledProcessError as e:
            pass

        

    if not done:
        warn("WARN: Continuing without support for BRIDGE_IP expansion")

    else:
        # ensure we have a valid ip
        p = re.compile(
                '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
        if not p.match(output):
            raise Exception(output + " is not a valid IP address for BridgeIP")

    return output


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

