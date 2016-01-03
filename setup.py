try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'grua',
    'author': 'Martin Cosgrave',
    'url': 'http://github.com/marsbard/grua',
    'download_url': 'http://github.com/marsbard/grua',
    'author_email': 'martin@bettercode.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['grua'],
    'scripts': [],
    'name': 'grua'
}

setup(**config)
