import subprocess
import os
import re
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

    try:
        command = ["ip", "addr", "show", "dev", "docker0"]
        sp = subprocess.Popen(command, stdout=subprocess.PIPE)

        output = subprocess.check_output(('grep', 'inet'), stdin=sp.stdout).strip().split()[1].split('/')[0]

        done = True

    except OSError as e:
        if e.errno == os.errno.ENOENT:
            # handle file not found error.
            print "File not found"
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


def touch(fname, times=None):
    with open(fname, 'a'):
        os.utime(fname, times)

