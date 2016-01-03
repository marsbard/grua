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

* __project__

This should be a unique name on your system. If you do not provide this then by default the project name
is `grua` but you should be aware that if you use two projects with the same name then you are likely to 
get clashes in mode configuration (SEE MODE) and in the worst case you could get data corruption, for 
example two projects with the same name having a container called 'mysql' would attempt to maintain both
their databases in the same physical place on your hard drive. It should be obvious that this is a bad idea.
(In this example I am assuming the same mysql config which exposes the same volumes).

* __volumepath__

By default, this is `/var/lib/grua/volumes` but you can set a different path here, if for example you want
all volumes to be on an nfs mount.

Example of global parameters:
```
global:
  project: alf
  volumepath: /var/lib/grua/volumes
```

Any volumes you define which do not have a leading slash as part of the local location
will be placed relative to this volumepath, but when a leading `/" is used (or "./") then the absolute 
path is used (SEE VOLUMES)


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

* [__image__ (value)](#attrs-fill-image)

You must have at least one of `build` or `image` in your configuration. If you have `image`, it refers
to an image either available on the system or else in the default registry.

You can also include a tag on an image value. For example:

```
mysql:
  image: mysql:5.6
```

If you specify both `build` and `image` attributes, then `build` will take preference.

#### Attributes relevant to `grua stack`

* [__run__ (boolean)](#attrs-stack-run)

If set to `true` then this will be a container to be run. If set to `false` then just an 
image will be created. In this case you probably want to list the container names that will
require this image using a `before` attribute, see [build](#attrs-fill-build)