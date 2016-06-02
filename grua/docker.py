import subprocess, os, shutil, time, shlex
from subprocess import call
from mem import mem
from util import announce, mention, note, quietcall
from templater import get_value, parse_template


def get_image(config):
    if config.has_key('image'):
        image = get_value(config, 'image')  # .split(':')[0]
    elif config.has_key('tag'):
        image = get_value(config, 'tag')
    else:
        image = mem.Project + '/' + get_value(config, 'build')

    return image


def get_container(name):
    return mem.Project + "_" + name


def fill_container(container, config):
    announce("Filling " + container + " container")
    if config.has_key('build'):
        build = get_value(config, 'build')
        tag = mem.Project + "/" + build

        if config.has_key('tag'):
            tag = get_value(config, 'tag')

        target = build
        if build[:4] == 'git:':
            if not config.has_key('tag'):
                raise Exception("If you are using a git repo for 'build' you must also specify 'tag'")
            tag = get_value(config, 'tag')

            url = build[4:]
            print "Cloning " + tag + " from " + url
            dir = "_grua_" + tag.replace("/", "_")

            if os.path.isdir(dir):
                shutil.rmtree(dir)

            command = ['git', 'clone', url, dir]
            note(" ".join(command))
            call(command)
            target = dir

        mention("building " + container + " ( " + target + " ) " + " with tag '" + tag + "'")

        command = ['docker', 'build', '-t', tag, target]

        note(" ".join(command))

        quietcall(command)

    else:
        mention(container + " uses an image. Pulling " + get_value(config, 'image'))
        command = ['docker', 'pull', get_value(config, 'image')]
        note(" ".join(command))
        quietcall(command)


def empty_container(container, config):
    announce("Emptying image " + container)
    command = ['docker', 'rmi', get_image(config)]
    note(" ".join(command))
    quietcall(command)


def stack_container(container, config):
    announce("Stacking " + container + " container")
    if config.has_key('run') and not config['run']:
        note("container has 'run' key set to " + str(config['run']) + ", skipping")
        return

    command = ['docker', 'run', '-d', '--name', get_container(container)]

    if config.has_key('options'):
        for option in config['options']:
            command = command + [parse_template(option)]

    if config.has_key('hostname'):
        command = command + ['--hostname', get_value(config, 'hostname')]
    # else:
    #    command = command + ['--hostname', container]

    if config.has_key('dns'):
        command = command + ['--dns', get_value(config, 'dns')]

    if config.has_key('volumes'):
        for volumespec in config['volumes']:
            volumespec_parsed = parse_template(volumespec)
            if volumespec_parsed.startswith("/"):
                command = command + ['-v', volumespec_parsed]
            elif volumespec_parsed.startswith('./'):
                # docker complains if path starts with "." so expand CWD here
                cwd = os.path.dirname(os.path.realpath(volumespec_parsed.split(':')[0]))
                realpath = cwd + '/' + volumespec_parsed.strip('./')
                command = command + ['-v', realpath]
            else:
                command = command + ['-v', mem.VolumePath + '/' + mem.Project +
                                     '/' + container + '/' + volumespec_parsed]

    if config.has_key('ports'):
        for portspec in config['ports']:
            command = command + ['-p', parse_template(portspec)]

    if config.has_key('environment'):
        for envvar in config['environment']:
            command = command + ['-e', parse_template(envvar) + '=' + parse_template(config['environment'][envvar])]

    if config.has_key('links'):
        for link in config['links']:
            command = command + ["--link=" + get_container(parse_template(link))]

    command.append(get_image(config))

    if config.has_key('command'):
        command = command + shlex.split(get_value(config, 'command'))

    note(" ".join(command))
    quietcall(command)

    if config.has_key('upwhen'):
        wait_for_up(container, config)


def unstack_container(container):
    announce("Unstacking " + container + " container")
    command = ['docker', 'stop', get_container(container)]
    note(" ".join(command))
    quietcall(command)

    command = ['docker', 'rm', '--force', get_container(container)]
    note(" ".join(command))
    quietcall(command)


def inspect_container(container, go_template):
    command = ['docker', 'inspect', '-f', " ".join(go_template), get_container(container)]

    # 1  note(" ".join(command))
    return subprocess.check_output(command, stderr=subprocess.STDOUT).strip()


def enter_container(commands):
    which = commands.popleft()
    run = ["/bin/bash"]
    if len(commands) > 0:
        run = list(commands)
    announce("Entering '" + which + "' container and running: " + str(run))
    command = ['docker', 'exec', '-ti', get_container(which)] + run
    note(" ".join(command))
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

    ignore_quiet = True
    mention(container + ": " + output, ignore_quiet),


def wait_for_up(container, config):
    upwhen = config['upwhen']
    timeout = 30
    if upwhen.has_key('timeout'):
        timeout = get_value(upwhen, 'timeout')

    if upwhen.has_key('logmsg'):
        logmsg = get_value(upwhen, 'logmsg')

        if upwhen.has_key('logfile'):
            logfile = mem.VolumePath + "/" + mem.Project + "/" + container + "/" + get_value(upwhen, 'logfile')
            mention("Waiting up to " + str(
                    timeout) + " seconds for '" + logmsg + "' in '" + logfile + "' to indicate that " + container + " is stacked")

        else:
            mention("Waiting up to " + str(
                    timeout) + " seconds for '" + logmsg + "' to indicate that " + container + " is stacked")

        waited = 0
        ok = False

        while waited <= timeout:
            if not 'logfile' in locals():
                command = ["docker", "logs", get_container(container)]
            else:
                if logfile.startswith('/'):
                    command = ["tail", logfile]

                else:
                    # there's a chance we try to tail it before it exists... just ignore that time
                    if os._exists(logfile):
                        command = ["tail", logfile]

            # command may not have been set yet if the file didn't exist
            if 'command' in locals():
                try:
                    output = subprocess.check_output(command, stderr=subprocess.STDOUT)
                except:
                    pass
            # print output

            if 'output' in locals() and output.find(logmsg) > -1:
                ok = True
                break
            else:
                time.sleep(1)
                waited = waited + 1

        if not ok:
            raise Exception("Timed out waiting for " + container + " to start")

    if upwhen.has_key('sleep'):
        mention("Sleeping " + str(upwhen['sleep']) + " extra seconds as configured")
        time.sleep(int(upwhen['sleep']))
