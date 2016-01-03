# grua
An opinionated docker composition tool with runtime dependencies between containers.

![](https://openclipart.org/image/200px/svg_to_png/176279/shipbuilding-crane-1.png)

*https://openclipart.org/detail/176279/shipbuilding-crane*

## Why another composition tool?

`docker-compose` is a great tool if you want to build microservices, and you have well behaved containers that 
can tolerate dependent services not being readily available, but in the real world, when you are dockerising
a complex monolithic application, you might find that if containers come up out of order that even when the 
dependencies become available, the target application fails to start properly.

So `grua` adds explicit dependency ordering to container composition, by use of  `before` and `after` attributes
in container configuration. Furthermore, rather than just firing the next container as soon as docker has started
the previous one, you can wait for a specific message in the log output before starting the next container. This 
can give you confidence that each dependency is ready before starting your main application.

## The grua metaphor

'Grua' is Spanish for 'crane'. The metaphor used in `grua` extends that to imagine a crane on a dockside
stacking containers into a composition (or, indeed, a stack). But it also uses a 'fill' metaphor to describe
'filling' a container with an image.

SEE COMMAND_LINE

## The configuration file, grua.yaml

The configuration file is a YAML file. In general each top level entry in the file specifies a container 
to be built, for example, here is a container that will create a consul container and when in use, will
wait for the log message "consul: New leader elected: consul" before proceeding:

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
that isn't supplied, you can use the 'options:' stanza as shown above.

### Global parameters

There is one top level section that does not represent a container, and that is the 'global' section.
It can contain the following configuration items:

* <a name="global-project">__project__</a>

This should be a unique name on your system. If you do not provide this then by default the project name
is `grua` but you should be aware that if you use two projects with the same name then you are likely to 
get clashes in mode configuration (SEE MODE) and in the worst case you could get data corruption, for 
example two projects with the same name having a container called 'mysql' would attempt to maintain both
their databases in the same physical place on your hard drive. It should be obvious that this is a bad idea.
(In this example I am assuming the same mysql config which exposes the same volumes).

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

#### Attributes relevant to `grua fill`

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
Also note here that 'before' was specified. Normally this specifies runtime ordering but it also specifies
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

#### Attributes relevant to `grua stack`

* <a name="attrs-stack-run">__run__ (boolean)</a>

If set to `true` then this will be a container to be run. If set to `false` then just an 
image will be created. In the latter case you probably want to list the container names that will
require this image using a `before` attribute, see example base configuration in [build](#attrs-fill-build),
which specifies that it must be built before the tomcat container. In that case, the tomcat container
has `FROM marsbard/base` at the top of its Dockerfile.

By default this is `true` so you only need to specify it when you don't want the image to be
run as a container, e.g.:

```
tomcat:
  build: tomcat
  tag: marsbard/tomcat
  run: false
```

* <a name="attrs-stack-options">__options__ (list)</a>

Any docker options for which grua does not provide a replacement may be provided here. _In fact
options for which grua does provide a replacement may also be provided here but be aware that
grua names things with the [project](#global-project) attribute from the [global](#global-parameters) section, for 
example, if the project is `foo`, and the container is defined as `mysql` within `grua.yaml`, then
the container that docker will work with will be named `foo_mysql`_

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

It can be useful to use this in conjuction with (SEE GRUA TEMPLATING) to determine the address of a 
particular container that will provide you with DNS services for your containers. For example in a 
setup using consul and registrator, you could specify something like this:

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
In the above example, if [volumepath](#global-volumepath) is set to its default value, the first volume 
will be located at 

`/var/lib/grua/volumes/alf/repo/data` 

on the host, while the second volume, `/tmp` on the container will be mapped to the `/tmp` directory of the host.


* <a name="attrs-stack-ports">__ports__ (list)</a>

Each element of this list will be transformed to a `-p` argument to docker.

Example:
```
solr:
  build: solr
  options:
    - "--expose=8443"
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
  dns: <% INSPECT consul {{ .NetworkSettings.IPAddress }} %>
  image: mysql:5.6
  options:
    - "--expose=3306"
  volumes:
    - alfresco/mysql:/var/lib/mysql
```

* <a name="attrs-stack-link">__link__ (list)</a>

Equivalent to `--link=<container name>` but it prepends the value of [project](#global-project) to
the container name.

```
global:
  project: alf
registrator:
  image: gliderlabs/registrator:latest
  link:
    - consul
```

In actual fact, from docker's point of view, in this case the container that is linked to will be `alf_consul`

* <a name="attrs-stack-command">__command__ (value)</a>

Equivalent to the `CMD` directive in the Dockerfile, and also to the command that you would append as 
the last argument in a call such as `docker run -ti some/image /path/in/container/to/command`.

```
registrator:
  image: gliderlabs/registrator:latest
  command: "-internal consul://consul:8500"
```

This will override the `CMD` directive from the Dockerfile

* <a name="attrs-stack-upwhen">__upwhen__ (hash)</a>

This attribute allows you to delay the stacking of the __next__ container until some log message has 
been seen, or until a sleep period has passed. 

You may specify:

** <a name-"attrs-stack-upwhen-logmsg">__logmsg__ (value)</a>

Runs `docker logs <grua container name>"` continuously, once per second, until either the specified
message has been found (uses python `<string>.find()`) or else the timeout has been reached.

** <a name="attrs-stack-upwhen-sleep">__sleep__ (value)</a>

Sleep for the specified number of seconds. Sleeping is always likely to be fragile and is discouraged.

If sleep is specified with any other `upwhen` directive, then the sleep will occur after the other 
directives have been satisfied. For example if both `logmsg` and `sleep` are specified then the 
sleep will occur after the `logmsg` has been seen.

```
mysql:
  upwhen:
    logmsg: "mysqld: ready for connections"
    sleep: 2
```

By default grua will wait up to 30 seconds for the requirements to be met before throwing an exception 
but you can set a timeout, e.g.:

```
solr:
  upwhen:
    logmsg: "INFO: Server startup in "
    timeout: 60
```

