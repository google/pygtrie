from distutils.core import setup
import os
import re
import sys
import codecs
import version

release = version.get_version()

if len(sys.argv) == 2 and sys.argv[1] == 'builddoc':
    os.execlp('sphinx-build',
              '-Drelease=' + release,
              '-Dversion=' + '.'.join(release.split('.', 2)[0:2]),
              '.', 'html')

with codecs.open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()
with codecs.open('version-history.rst', 'r', 'utf-8') as f:
    readme += '\n' + f.read()

kwargs = {
    'name': 'pygtrie',
    'version': release,
    'description': 'Trie data structure implementation.',
    'long_description': readme,
    'author': 'Michal Nazarewicz',
    'author_email': 'mina86@mina86.com',
    'url': 'https://github.com/google/pygtrie',
    'py_modules': ['pygtrie'],
    'license': 'Apache-2.0',
    'platforms': 'Platform Independent',
    'keywords': ['trie', 'prefix tree', 'data structure'],
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
}

if re.search(r'(?:\d+\.)*\d+', release):
    kwargs['download_url'] = kwargs['url'] + '/tarball/v' + release

setup(**kwargs)
