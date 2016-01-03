try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'My Project',
    'author': 'Martin Cosgrave',
    'url': 'URL to get it at.',
    'download_url': 'Where to download it.',
    'author_email': 'martin@bettercode.com',
    'version': '0.1',
    'install_requires': ['nose'],
    'packages': ['grua'],
    'scripts': [],
    'name': 'projectname'
}

setup(**config)
