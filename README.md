# grua
An opinionated declarative docker composition tool with runtime dependencies between containers.

![](https://openclipart.org/image/200px/svg_to_png/176279/shipbuilding-crane-1.png)

*https://openclipart.org/detail/176279/shipbuilding-crane*


* __[Installation](#installation)__
* __[Why another composition tool?](#why-another-composition-tool)__
* __[A real example](#a-real-example)__
* __[The grua metaphor](#the-grua-metaphor)__
* __[The configuration file, grua.yaml](#the-configuration-file-gruayaml)__
* __[Container configuration](#container-configuration)__
* __[Grua templating](#grua-templating)__
* __[Grua command line](#grua-command-line)__



## Installation

`$ git clone https://github.com/marsbard/grua.git` 

Or else see the [releases page](https://github.com/marsbard/grua/releases) to see if there
are any stable releases (hint, there aren't, yet).

`$ cd grua`

`$ ./install`

If you get an error about "No module named yaml", please run `pip install pyyaml`.

## Why another composition tool?

`docker-compose` is a great tool if you want to build microservices, and you have well behaved 
containers that can tolerate depended-upon services not being readily available, but in the real 
world, when you are dockerising a complex monolithic application, you might find that if 
containers come up out of order that even when the dependencies become available, the target 
application fails to start properly.

So `grua` adds explicit dependency ordering to container composition, by use of [`before`](#attrs-deps-before) 
and [`after`](#attrs-deps-after) attributes in container configuration. Furthermore, rather than 
just firing the next container as soon as docker has started the previous one, you can wait for a 
specific message in the log output before starting the next container. This can give you confidence 
that each dependency is ready before starting your main application.

Additionally you get the capability to use any data you can find from `docker inspect` on an already 
running container within the configuration of another container, typically that looks like this:

```
postfix:
  hostname: postfix
  dns: <% INSPECT consul {{ .NetworkSettings.IPAddress }} %>
```

## A real example

Grua was developed because of a perceived lack in the currently available tools (fig, docker-compose, crowdr)
in dealing with legacy "multi-monolithic" applications consisting of disparate systems and modules
often installed on the same server. The particular application it was designed to assist dockerisation of 
is the Alfresco Enterprise Content Management System (http://alfresco.com). Alfresco consists of several 
tomcat applications, a database server, a search index server and many optional components. In the first
iteration of `docker-alfresco` we've tried to create an example of a basic, but full featured and fully 
functional application being built with the grua machinery.

Take a look at [docker-alfresco](https://github.com/marsbard/docker-alfresco) for an example that exercises 
almost all of what is available in the grua system today.


## The grua metaphor

'Grua' is Spanish for 'crane'. The metaphor used in `grua` extends the docker metaphor to imagine a crane 
on a dockside stacking containers into a composition (or, indeed, a stack). But it also uses a 'fill' 
metaphor to describe 'filling' a container with an image.

See [grua command line](#grua-command-line)



## The configuration file, `grua.yaml`

The configuration file is a YAML file. In general, (apart from [the global parameters](#global-parameters)) 
each top level attribute in the file specifies a container to be built, for example, here is a container 
that will create a consul container and when in use, will wait for the log message 
`consul: New leader elected: consul` before proceeding to stack the next container:

```
consul:
    build: consul
    upwhen: 
        logmsg: "consul: New leader elected: consul"
    options:
        - "--expose=8300"
        - "--expose=8500"
        - "--expose=53"
    ports:
        - 8300:8300
        - 8500:8500
        - "53:53"
    volumes:
        - config:/config
        - data:/data
    command: "-data-dir=/data -bootstrap-expect 1 -client 0.0.0.0"

```

Please be sure to note that if you are used to docker-compose, various things will be different, and in 
particular I have not attempted to model the whole docker command line interface, if you need something 
that isn't supplied, you can use the `options:` stanza as shown above and [also here](#attrs-stack-options).

### Global parameters

There is one top level attribute that does not represent a container, and that is the `global` section.
It can contain the following configuration items:

* <a name="global-project">__project__</a>

This should be a unique name on your system. If you do not provide this then by default the project name
is `grua` but you should be aware that if you use two projects with the same name then you are likely to 
get clashes in [mode configuration](#mode) and in the worst case you could get data corruption. For 
example two projects with the same name having a container called 'mysql' would attempt to maintain both
their databases in the same physical place on your hard drive. It should be obvious that this is a bad idea.
(In this example I am assuming the same mysql config which exposes the same volumes).

Just be sure to always specify a `global` top level element containing a `project` attribute that
doesn't exist in any other `grua` project on your system.

* <a name="global-volumepath">__volumepath__</a>

By default, this is `/var/lib/grua/volumes` but you can set a different path here, if for example you want
all volumes to be on an nfs mount.

Example of global parameters:
```
global:
  project: alf
  volumepath: /var/lib/grua/volumes
```

Any volumes you define which do not have a leading slash as part of the local location
will be placed relative to this volumepath, but when a leading `/` is found then the absolute 
path is used ([see volumes](#attrs-stack-volumes)).

### Container configuration

#### Dependency ordering attributes

* <a name="attrs-deps-before">__before__ (list)</a>

Specify that this container must be stacked (or filled) before some other container(s), for example:

```
share:
  build: share
  before: 
    - solr
```
In this instance, the `share` container will be stacked before the `solr` container is, and also
when the underlying images are filled they respect the same order.

When unstacking or emptying the containers, the ordering is respected in reverse. In the example shown
above, the `solr` container would be unstacked before the `share` container.

* <a name="attrs-deps-after">__after__ (list)</a>

Specify that this container must be stacked or filled after some other container(s), e.g.
```
registrator:
  image: gliderlabs/registrator:latest
  after:
    - consul
  before:
    - postfix
    - alfresco
    - solr
    - share
    - mysql
  link:
    - consul
  volumes:
    - /var/run/docker.sock:/tmp/docker.sock

```

Here the `registrator` container will be stacked after the `consul` container. You can also see
that `registrator` is scheduled to start before several containers that depend on it.

When unstacking or emptying the containers, the ordering is respected in reverse. In the example shown
above, the `alfresco` container would be unstacked before the `registrator` container.

#### Attributes relevant to [`grua fill`](#cli-fill)

* <a name="attrs-fill-build">__build__ (value)</a>

You must have at least one of `build` or `image` in your configuration. If you have `build`, it refers
to a folder beneath the location of `grua.yaml` which should contain a Dockerfile and any other resources
required by that Dockerfile.

Example:
```
consul:
  build: consul
```

Sometimes you want to build a base image without running it, in which case you should also specify `run: false` 
as well as adding a tag name to refer to the image, e.g.:

```
base:
    build: base
    tag: marsbard/base
    run: false
    before: 
        - tomcat
```
Also note here that `before` was specified. Normally this specifies runtime ordering but it also specifies
build ordering when `run: false` is in effect. In this case, the `tomcat` image is built using 
`FROM marsbard/base` in the Dockerfile, so it is necessary to build `marsbard/base` first before 
building the `tomcat` image.

If you specify both `build` and `image` attributes, then `build` will take preference.

* <a name="attrs-fill-image">__image__ (value)</a>

You must have at least one of `build` or `image` in your configuration. If you have `image`, it refers
to an image either available on the system or else in the default registry.

You can also include a tag on an image value. For example:

```
mysql:
  image: mysql:5.6
```

If you specify both `build` and `image` attributes, then `build` will take preference.

#### Attributes relevant to [`grua stack`](#cli-stack)

* <a name="attrs-stack-run">__run__ (boolean)</a>

Specify whether this container may be stacked. If you are building an intermediate base image, upon
which other images will be based, but will never need to be run itself, then set this to `false`.

Note that the dependency ordering is respected, so when you are building another image from this base 
it should have its [after](#attrs-after) attribute set to the name of this container, e.g.
```
base:
  build: my-base
  tag: foobar/base
  run: false
dependent: 
  build: dependent # in the Dockerfile it says 'FROM foobar/base'
  after: 
    - base
```
This will ensure that the `dependent` image is not built until after the `base` image has been.

By default `run` is `true` so you only need to specify it when you don't want the image to be
run as a container, e.g.:

```
tomcat:
  build: tomcat
  tag: marsbard/tomcat
  run: false
```

* <a name="attrs-stack-options">__options__ (list)</a>

Any docker options for which `grua` does not provide a replacement may be provided here. 

_(In fact options for which `grua` does provide a replacement may also be provided here but 
be aware that `grua` names things with the [project](#global-project) attribute from the 
[global](#global-parameters) section, for example, if the project is `foo`, and the container is 
defined as `mysql` within `grua.yaml`, then the container that docker will work with will be named 
`foo_mysql`)_

This attribute is useful for specifying ports to expose, as currently there is no grua replacement for
the `--expose` command line argument:

```
consul:
  build: consul
  options:
    - "--expose=8300"
    - "--expose=8500"
    - "--expose=53"
```

The options list will be concatenated in the order that it is specified and passed to `docker run`

* <a name="attrs-stack-hostname">__hostname__ (value)</a>

Set the hostname of this container. If this is not explicitly set then this will be the name of the 
container, which would make the following example, while illustrative, redundant.

``` 
mysql:
  hostname: mysql
```

Equivalent to `docker run -h`

* <a name="attrs-stack-dns">__dns__ (value)</a>

Set the DNS server the container should use to resolve domain queries.

It can be useful to use this in conjuction with [grua templating](#grua-templating) to determine 
the address of a particular container that will provide you with DNS services for your containers. 
For example in a setup using consul, you could specify something like this:

```
postfix:
  hostname: postfix
  dns: <% INSPECT consul {{ .NetworkSettings.IPAddress }} %>
```

Equivalent to `docker run --dns <address>`

* <a name="attrs-stack-volumes">__volumes__ (list)</a>

These work slightly differently to how docker volumes are specified normally. As usual there is a 
host location for the volume, and a location within the container, specified like 
`<host location>:<container location>`. But when `host location` does __not__ start with a `/` 
character, the location of the volume on the host will be relative to [volumepath](#global-volumepath)
and it will include the global [project](#global-project) attribute in its path.

When `host location` __does__ start with `/`, the location of the volume on the host will be absolute.

For example: 
```
global:
  project: alf
alfresco:
  volumes:
    - repo/data:/data
    - /tmp:/tmp
```
In the above example, if [volumepath](#global-volumepath) is set to its default value, the first volume, 
`/data` in the container, will be located at  `/var/lib/grua/volumes/alf/repo/data` on the host, while 
the second volume, `/tmp` in the container will be mapped to the `/tmp` directory of the host.


* <a name="attrs-stack-ports">__ports__ (list)</a>

Each element of this list will be transformed to a `-p` argument to docker.

Example:
```
solr:
  build: solr
  ports:
    - "8443:8443"
```

* <a name="attrs-stack-environment">__environment__ (hash)</a>

A hash of variable names and values, for example:
```
mysql:
  environment:
    MYSQL_DATABASE: alfresco
    MYSQL_USER: alfred
    MYSQL_PASSWORD: wutwut
    MYSQL_ROOT_PASSWORD: wutwutwut
```

Equivalent to the `-e` switch to `docker run`, this will make each element of the environment hash
available in the environment of the relevant container.

* <a name="attrs-stack-links">__links__ (list)</a>

Make a link between docker containers for each member of the list. Equivalent to `--link=<link name>` 
but it prepends the value of [project](#global-project) to the link name.

```
global:
  project: alf
registrator:
  links:
    - consul
```

By default this will prepend the value of [project](#global-project) to the link name, in this example
the link name will be `alf_consul`, you can override this by specifying the container's view of the 
link name in the usual way:
```
global:
  project: alf
registrator:
  links:
    - consul:consul
```
Now the link name (`--link=<link name>`) will be `consul` instead of `alf_consul`.

* <a name="attrs-stack-command">__command__ (value)</a>

Equivalent to the `CMD` directive in the Dockerfile, and also to the command that you would append as 
the last argument in a call such as `docker run -ti some/image /path/in/container/to/command`.

```
registrator:
  command: "-internal consul://consul:8500"
```

This will override the `CMD` directive from the Dockerfile

* <a name="attrs-stack-upwhen">__upwhen__ (hash)</a>

This attribute allows you to delay the stacking of the following container until some log message has 
been seen, or until a sleep period has passed. 

You may specify:


> <a name="attrs-stack-upwhen-sleep">__sleep__ (value)</a>
>
> Sleep for the specified number of seconds. Sleeping is always likely to be fragile and is discouraged.
> 
> If sleep is specified with any other `upwhen` directive, then the sleep will occur after the other 
> directives have been satisfied. For example if both `logmsg` and `sleep` are specified then the 
> sleep will occur after the `logmsg` has been seen.
```
mysql:
  upwhen:
    logmsg: "mysqld: ready for connections"
    sleep: 2
```
> That example sleeps for 2 extra seconds after the requisite `logmsg` has been seen.


or

> <a name="attrs-stack-upwhen-logmsg">__logmsg__ (value)</a>
>
> Runs `docker logs <grua container name>` continuously, once per second, until either the specified
> message has been found (uses python `<string>.find()`) or else the timeout has been reached.

By default the stdout of the main process will be searched, if you need instead to search within
some generated logfile, you need to first ensure the logfile is being mounted as or within a volume,
and secondly you should then add a 'logfile' parameter:

> <a name="attrs-stack-upwhen-logfile">__logfile__ (value)</a>
>
> When this attribute is present, it alters the behaviour of the 'logmsg' attribute to search within
a file, rather than the stdout of the main process. This file must have been exported as a docker 
volume, and the value given here should be that of the local path on the host side, following the
same rules as for [`volumes`](#attrs-stack-volumes), viz., if the filename begins with a `/` it is
presumed to be an absolute filename on the host, whereas if it does not it is presumed to be a local
path to the grua volumes for this project and container. For example:
```
httpd:
  upwhen:
    logmsg: "resuming normal operations"
    logfile: logs/error.log
  volumes:
    - logs:/usr/local/apache2/logs
```
> In this case, you are searching inside `/usr/local/apache2/logs/error.log` on the container, 
> which is exported as a volume `/var/lib/grua/volumes/<project>/httpd/error.log` in this case
> (assuming that [`volumepath`](#global-volumepath) has not been altered).
>
> If 'logmsg' is not present this has no effect.


By default `grua` will wait up to 30 seconds for the requirements to be met before throwing an exception 
but you can change the timeout, e.g.:

```
solr:
  upwhen:
    logmsg: "INFO: Server startup in "
    timeout: 60
```

### grua templating

#### in grua.yaml

Within the grua.yaml file, you may add a template to be replaced (at stack time, usually) with 
some information from your environment or from docker's metadata.

Here's an example of a number of templates. These use values from your _current_ environment to 
pass values through to the environment of the container:

```
mysql:
  environment:
    MYSQL_DATABASE: <% ENV MYSQL_DATABASE | alfresco %>
    MYSQL_USER: <% ENV MYSQL_USER | alfuser %>
    MYSQL_PASSWORD: <% ENV MYSQL_PASSWORD  %>
    MYSQL_ROOT_PASSWORD: <% ENV MYSQL_ROOT_PASSWORD %>
```
You can use the following template 'commands' as the first entry in the template:

__ENV__ &lt;variable name&gt;

Replace the template with the content of the named environment variable. See the examples above.

Optionally you may add a pipe character followed by some default value, which can be any number of
words.

```
solr:
  environment:
    ADMIN_NAME: <% ENV SOLR_ADMIN_NAME | Duty Administrator %>
```

__GRUA__ &lt;'subcommand'&gt;

Currently only supports two 'subcommands':

* _BRIDGE_IP_

Replace the template with the IP address of the docker bridge.

```
skydock:
  ports:
    <% GRUA BRIDGE_IP %>:53:53/udp
```
* _PROJECT_

Replace the template with the [project name](#global-project)

```
elasticsearch:
  # this example assumes entrypoint defined in docker which calls elasticsearch
  command: "-Des.node.name=<% GRUA PROJECT %>"
```

__INSPECT__ &lt;container name&gt; &lt;go template&gt;

Replace the template with some information from running `docker inspect`.

```
solr:
 dns: <% INSPECT consul {{ .NetworkSettings.IPAddress }} %>
 after: consul
```
Needless to say, the referred to container must already be running in order for `docker inspect` to
work, so you must make sure to use dependency ordering with [`before`](#attrs-deps-before) and 
[`after`](#attrs-deps-after) 

### __grua__ command line

#### without arguments

```
$ grua
                grua
                ----
              //\  ___
              Y  \/_/=|
             _L  ((|_L_|
            (/\)(__(____) cjr

   grua fill		Build requisite containers
   grua empty		Destroy all the related images
   grua refill		Empty followed by fill - rebuild image(s)

   grua stack		Run container composition
   grua unstack		Stop and remove container composition
   grua restack		Unstack and restack container composition

   grua enter		Enter container, run bash or opt args
   grua status		Show status of containers
   grua edit		Edit grua.yaml from within subfolder
   grua editd		Edit Dockerfile(s) from within subfolder

   grua mode		Set operating mode

> grua mode is currently: noisy, destructive

```

I have slightly tortured the docker container metaphor to make it fit my crane metaphor, but for the 
purpose it works quite well. I say that _filling_ a container is analagous to the `docker build` and 
`docker pull` commands, i.e. it gets a docker image on your system, and in my metaphor I say you have 
filled the grua container (that's the torture bit of the docker metaphor).

Then, instead of `docker run`, I have `grua stack`, where your containers are stacked into a 
composition. This is the same as `docker run` but because of the dependency ordering feature as well 
as the ability of waiting for a container to be completely ready before initiating the next one, 
stacking seemed like a better metaphor to me.

<a name="cli-fill">
#### fill
</a>

Fill the grua containers by creating or fetching docker images. The same dependency ordering is 
respected as for the [`stack`](#cli-stack) command, that is, the 'before' and 'after' elements
of the configuration are taken into account. 

Equivalent to running `docker build` when the configuration contains a 'build' element, or else 
equivalent to `docker run` when the configuration contains an 'image' element. 

You can pass multiple container names, e.g. `grua fill postfix alfresco mysql` and each one will 
be filled, and the ordering that is passed on the command line will be respected.

If no container names are passed, all containers that are defined will be filled.

If you fill a container that has already been filled, and has not been subsequently emptied, then
it is likely that all the layers defined in the Dockerfile will be built from cache.

<a name="cli-empty">
#### empty
</a>

Empty the grua containers. First `grua` attempts to unstack the container, if the container is
not stacked a harmless error is reported. Then the image is removed using `docker rmi`. Note that
this tends to remove all the intermediate containers from the cache too, so filling the container
again will not have any cached images to rely on and thus will take longer to fill.

You probably don't want to use this, unless you know that the images will not be used on this 
host again.

If no container names are passed, all containers will be emptied in reverse order to the dependencies
listed in the configuration, for example, this config fragment:
```
alfresco:
  after: mysql
```
which ensures that while filling or stacking, that 'mysql' is filled or stacked before 'alfresco',
means that during the 'empty' phase, the 'alfresco' container will be emptied (and therefore 
unstack attempted) before the 'mysql' container.

If some container names are passed on the command line, for example 
```
$ grua empty mysql alfresco
```
they will be processed in the order given on the command line.

<a name="cli-refill">
#### refill
</a>

First, attempt to unstack the container in case it is stacked. Then, if [`mode`](#cli-mode) has
been set `destructive`, [`empty`](#cli-empty) the container. (If [`mode`](#cli-mode)  is 
`conservative` then the container is not emptied).

Then run [`fill`](#cli-fill). If [`mode`](#cli-mode) was `conservative` and therefore the 
container was not emptied, the fill process will be much faster than if [`mode`](#cli-mode)  is
set `destructive`.

If multiple container names are passed, they will be processed in the order they are passed 
on the command line.

If no container names are given, all containers will be refilled in the order specified by 
the dependency ordering in the configuration file.

<a name="cli-stack">
#### stack
</a>

Stack the container composition. Equivalent to `docker run` but respecting the dependency 
ordering defined in the [configuration file](#the-configuration-file-gruayaml) as well 
as possibly [waiting for  containers to become ready](#attrs-stack-upwhen).

You can specify a number of containers to stack but if a container to be stacked depends
directly on a container which is not stacked (for instance it is [linked](#attrs-stack-links)),
then the stacking may fail. You're ok to start containers that are out of order with respect
to the configuration, as long as they don't have direct dependencies like [link](#attrs-stack-links)

If the config item `run: false` is set for a container, that container is not stacked.

<a name="cli-unstack">
#### unstack
</a>

Dismantle the container composition. Equivalent to running `docker stop` on all the containers
in their correct order, which is the reverse of that defined in the 
[configuration file](#the-configuration-file-gruayaml).

Unstacking also removes the container, equivalent to `docker rm --force`. I told you this 
framework was opinionated `;-)`. You should never create docker containers that store state
inside them, so this methodology keeps you honest `:-)`. Of course data that is persisted
into volumes is untouched.

If the config item `run: false` is set for a container, that container is not unstacked.

<a name="cli-restack">
#### restack
</a>

Run [`unstack`](#cli-unstack) followed by [`stack`](#cli-stack).

If no container names are passed in, then all containers which don't have `run: false` defined
in their config will be restacked in the order defined by the 
[configuration file](#the-configuration-file-gruayaml).

If container names are passed on the command line then they will be processed in the order
given on the command line/

If the config item `run: false` is set for a container, that container is not restacked.

<a name="cli-enter">
#### enter
</a>

Enter a stacked container and execute a command. By default the command is `/bin/bash` but if 
the container you are running does not have the `bash` interpreter installed you can pass any
command you like. It is equivalent to running `docker run -ti <project>_<container> /bin/bash`
in the default mode.

For example, you could run `grua enter consul sh` to run 'sh' instead of '/bin/bash'.

You can also pass one shot commands, e.g. `grua enter consul cat /proc/cpuinfo`. When combined
with [`mode`](#cli-mode) `quiet`, this can be a useful way to interrogate your stacked 
containers using scripting.

<a name="cli-status">
#### status
</a>

Show whether the containers in the composition are stacked or unstacked. This command does not
yet tell you if an unstacked container has been filled or not. 

Also shows the current setting of [`mode`](#cli-mode)

Output is similar to the following.
```
$ grua status
>> haveged: ^ stacked ^
>> consul: ^ stacked ^
>> libreoffice: ^ stacked ^
>> registrator: ^ stacked ^
>> postfix: ^ stacked ^
>> mysql: ^ stacked ^
>> httpd: ^ stacked ^
>> alfresco: ^ stacked ^
>> share: _ unstacked _
>> solr: _ unstacked _
Mode is quiet, conservative

```


<a name="cli-edit">
#### edit
</a>
Edit the [configuration file grua.yaml](#the-configuration-file-gruayaml). The advantage of 
using this grua command rather than something like `$EDITOR ../grua.yaml` is that you can 
use this from any subdirectory beneath the location of `grua.yaml` and it will automatically
find the config file for you without you needing to navigate away from your current working 
folder nor requiring you to stack up a number of `../` strings in front.

It uses the current value of `$EDITOR` in your environment. If it isn't defined, make sure
you export some value, e.g. 
```
$ export EDITOR=vim
``` 
before running `grua edit`

<a name="cli-editd">
#### editd
</a>
Edit one or more Dockerfiles. If you don't pass a container name it is going to offer you 
each file to edit one after the other. This may not be what you want. It is probably best
to explicitly pass in the container names whose Dockerfiles you wish to edit.

Similarly to `grua edit`, you can be anywhere in the directory tree below the `grua.yaml`
file and this will work to open any Dockerfile you specify, e.g. 
```
$ grua editd alfresco share
```
will edit the Dockerfiles for the `alfresco` and `share` containers in turn.

If you pass the name of a container which does not have a `build` element in its config,
it will be silently skipped, generating no errors.

It uses the current value of `$EDITOR` in your environment. If it isn't defined, make sure
you export some value, e.g. 
```
$ export EDITOR=vim
``` 
before running `grua editd`

<a name="cli-mode">
#### mode
</a>

Currently there are two configurations you can set here. They each have two possible 
values. The state of each configuration is persisted under `$HOME/.grua`

* __noisy__ / __quiet__

When `noisy` is set (with `grua mode noisy`) then `grua` will tell you various things
about what it is doing. In particular it will show each `docker` command that it runs
in its entirety.

When `quiet` is set (with `grua mode quiet`) then `grua` will suppress all its output.
This may be handy if you want to use `grua` as the target of some shell script. The output
of docker commands executed is not suppressed, see examples:

Example of 'noisy' output:
```
$ grua fill haveged

>>> Filling haveged container

>> haveged uses an image. Pulling harbur/haveged:1.7c-1
> docker pull harbur/haveged:1.7c-1
1.7c-1: Pulling from harbur/haveged
Digest: sha256:b0f5fa6c6791793d08016a31c76098a22d5cb6a234be5f1e8866ace43295681b
Status: Image is up to date for harbur/haveged:1.7c-1
```

Example of 'quiet' output:
```
$ grua fill haveged
1.7c-1: Pulling from harbur/haveged
Digest: sha256:b0f5fa6c6791793d08016a31c76098a22d5cb6a234be5f1e8866ace43295681b
Status: Image is up to date for harbur/haveged:1.7c-1
```

* __destructive__ / __conservative__

When `destructive` is set (`grua mode destructive`), then during a [`refill`](#cli-refill)
execution, the container will be emptied. 

When `conservative` is set (`grua mode conservative`), then during a [`refill`](#cli-refill)
execution, the container will not be emptied. 
