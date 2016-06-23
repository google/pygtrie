#!/usr/bin/python

"""trie module example code."""

__author__ = 'Michal Nazarewicz <mina86@mina86.com>'
__copyright__ = 'Copyright 2014 Google Inc.'

# pylint: disable=invalid-name

import os
import stat
import sys

import pygtrie


print 'Storing file information in the trie'
print '===================================='
print

ROOT_DIR = '/usr/local'
SUB_DIR = os.path.join(ROOT_DIR, 'lib')
SUB_DIRS = tuple(os.path.join(ROOT_DIR, d)
                 for d in ('lib', 'lib32', 'lib64', 'share'))

t = pygtrie.StringTrie(separator=os.path.sep)

# Read sizes regular files into a Trie
for dirpath, unused_dirnames, filenames in os.walk(ROOT_DIR):
    for filename in filenames:
        filename = os.path.join(dirpath, filename)
        try:
            filestat = os.stat(filename)
        except OSError:
            continue
        if stat.S_IFMT(filestat.st_mode) == stat.S_IFREG:
            t[filename] = filestat.st_size

# Size of all files we've scanned
print 'Size of %s: %d' % (ROOT_DIR, sum(t.itervalues()))

# Size of all files of a sub-directory
print 'Size of %s: %d' % (SUB_DIR, sum(t.itervalues(prefix=SUB_DIR)))

# Check existence of some directories
for directory in SUB_DIRS:
    print directory, 'exists' if t.has_subtrie(directory) else 'does not exist'

# Drop a subtrie
print 'Dropping', SUB_DIR
del t[SUB_DIR:]
print 'Size of %s: %d' % (ROOT_DIR, sum(t.itervalues()))
for directory in SUB_DIRS:
    print directory, 'exists' if t.has_subtrie(directory) else 'does not exist'


print
print 'Storing URL handlers map'
print '========================'
print

t = pygtrie.CharTrie()
t['/'] = lambda url: sys.stdout.write('Root handler: %s\n' % url)
t['/foo'] = lambda url: sys.stdout.write('Foo handler: %s\n' % url)
t['/foobar'] = lambda url: sys.stdout.write('FooBar handler: %s\n' % url)
t['/baz'] = lambda url: sys.stdout.write('Baz handler: %s\n' % url)

for url in ('/', '/foo', '/foot', '/foobar', 'invalid', '/foobarbaz', '/ba'):
    key, handler = t.longest_prefix(url)
    if key is not None:
        handler(url)
    else:
        print 'Unable to handle', repr(url)


if not os.isatty(0):
    sys.exit(0)


try:
    import termios
    import tty

    def getch():
        """Reads single character from standard input."""
        attr = termios.tcgetattr(0)
        try:
            tty.setraw(0)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(0, termios.TCSADRAIN, attr)

except ImportError:
    try:
        from msvcrt import getch  # pylint: disable=import-error
    except ImportError:
        sys.exit(0)


print
print 'Prefix set'
print '=========='
print

ps = pygtrie.PrefixSet(factory=pygtrie.StringTrie)

ps.add('/etc/rc.d')
ps.add('/usr/local/share')
ps.add('/usr/local/lib')
ps.add('/usr')  # Will handle the above two as well
ps.add('/usr/lib')  # Does not change anything

print 'Path prefixes:', ', '.join(iter(ps))
for path in ('/etc', '/etc/rc.d', '/usr', '/usr/local', '/usr/local/lib'):
    print 'Is', path, 'in the set:', ('yes' if path in ps else 'no')


print
print 'Dictionary test'
print '==============='
print

t = pygtrie.CharTrie()
t['cat'] = True
t['caterpillar'] = True
t['car'] = True
t['bar'] = True
t['exit'] = False

print 'Start typing a word, "exit" to stop'
print '(Other words you might want to try: %s)' % ', '.join(sorted(
    k for k in t if k != 'exit'))
print

text = ''
while True:
    ch = getch()
    if ord(ch) < 32:
        print 'Exiting'
        break

    text += ch
    value = t.get(text)
    if value is False:
        print 'Exiting'
        break
    if value is not None:
        print repr(text), 'is a word'
    if t.has_subtrie(text):
        print repr(text), 'is a prefix of a word'
    else:
        print repr(text), 'is not a prefix, going back to empty string'
        text = ''
