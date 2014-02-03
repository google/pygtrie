from distutils.core import setup
import version

with open('README.rst') as f:
    readme = f.read()

setup(
    name='pygtrie',
    version=version.getVersion(),
    description='Trie data structure implementation.',
    long_description=readme,
    author='Michal Nazarewicz',
    author_email='mina86@mina86.com',
    url='https://github.com/google/pytrie',
    py_modules=['trie'],
    license='Apache-2.0',
    platforms='Platform Independent',
    keywords=['trie', 'prefix tree', 'data structure'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
