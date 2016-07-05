#!/usr/bin/python

"""trie module unit tests."""

__author__ = 'Michal Nazarewicz <mina86@mina86.com>'
__copyright__ = 'Copyright 2014 Google Inc.'


import array
import collections
import functools
import pickle
import types
import unittest

import __init__ as pygtrie  # pylint: disable=relative-import


# pylint: disable=missing-docstring

def _update_trie_factory(trie_cls, *args, **kw):
    t = trie_cls()
    t.update(*args, **kw)
    return t


def _setter_trie_factory(trie_cls, d):  # pylint: disable=invalid-name
    t = trie_cls()
    for k, v in d.items():
        t[k] = v
    return t


_TRIE_FACTORIES = ((
        'TrieFromNamedArgs',
        lambda trie_cls, d: trie_cls(**d)
), (
        'TrieFromTuples',
        lambda trie_cls, d: trie_cls(d.items())
), (
        'TrieFromDict',
        lambda trie_cls, d: trie_cls(d)
), (
        'TrieFromTrie',
        lambda trie_cls, d: trie_cls(trie_cls(d))
), (
        'CopyOfTrie',
        lambda trie_cls, d: trie_cls(d).copy()
), (
        'UpdateWithNamedArgs',
        lambda trie_cls, d: _update_trie_factory(trie_cls, **d)
), (
        'UpdateWithTuples',
        lambda trie_cls, d: _update_trie_factory(trie_cls, d.iteritems())
), (
        'UpdateWithDict',
        _update_trie_factory
), (
        'Setters',
        _setter_trie_factory
))


class TrieTestCase(unittest.TestCase):
    # The below need to be overwritten by subclasses

    # A Trie class being tested
    _TRIE_CLS = pygtrie.Trie

    # A key to set
    _SHORT_KEY = 'foo'
    # Another key to set such that _SHORT_KEY is it's prefix
    _LONG_KEY = _SHORT_KEY + 'bar'
    # A key that is not set but _LONG_KEY is it's prefix
    _VERY_LONG_KEY = _LONG_KEY + 'baz'
    # A key that is not set and has no relation to other keys
    _OTHER_KEY = 'qux'
    # A list of prefixes of _SHORT_KEY
    _SHORT_PREFIXES = ('', 'f', 'fo')
    # A list of prefixes of _LONG_KEY which are not prefixes of _SHORT_KEY nor
    # _SHORT_KEY itself
    _LONG_PREFIXES = ('foob', 'fooba')

    @classmethod
    def path_from_key(cls, key):
        """Turns key into a path as used by Trie class being tested."""
        return key

    @classmethod
    def key_from_path(cls, path):
        """Turns path as used by Trie class being tested into a key."""
        return tuple(path)

    # End of stuff that needs to be overwritten by subclasses

    def key_from_key(self, key):
        """Turns a key into a form that the Trie will return e.g. in keys()."""
        return self.key_from_path(self.path_from_key(key))

    # pylint: disable=invalid-name

    def assertNodeState(self, t, key, prefix=False, value=None):
        """Asserts a state of given node in a trie.

        Args:
            t: Trie to check the node in.
            key: A key for the node.
            prefix: Whether the node is a prefix of a longer key that is in the
              trie.
            value: If given, value associated with the key.  If missing, node
                has no value associated with it.
        Raises:
            AssertionError: If any assumption is not met.
        """
        if prefix:
            self.assertTrue(t.has_subtrie(key))
            self.assertTrue(bool(t.has_node(key) & pygtrie.Trie.HAS_SUBTRIE))
        else:
            self.assertFalse(t.has_subtrie(key))
            self.assertFalse(bool(t.has_node(key) & pygtrie.Trie.HAS_SUBTRIE))
        if value is None:
            o = object()
            self.assertNotIn(key, t)
            key_error_exception = pygtrie.ShortKeyError if prefix else KeyError
            self.assertRaises(key_error_exception, lambda: t[key])
            self.assertRaises(key_error_exception, t.pop, key)
            self.assertIsNone(t.get(key))
            self.assertIs(o, t.get(key, o))
            self.assertIs(o, t.pop(key, o))
            self.assertFalse(t.has_key(key))
            self.assertNotIn(self.key_from_key(key), list(t.iterkeys()))
            self.assertNotIn(self.key_from_key(key), t.keys())
            self.assertEquals(pygtrie.Trie.HAS_SUBTRIE if prefix else 0,
                                                t.has_node(key))
        else:
            self.assertIn(key, t)
            self.assertEquals(value, t[key])
            self.assertEquals(value, t.get(key))
            self.assertEquals(value, t.get(key, object()))
            self.assertTrue(t.has_key(key))
            self.assertTrue(bool(t.has_node(key) & pygtrie.Trie.HAS_VALUE))
            self.assertIn(self.key_from_key(key), list(t.iterkeys()))
            self.assertIn(self.key_from_key(key), t.keys())

    def assertFullTrie(self, t, value=42):
        """Asserts a trie has _SHORT_KEY and _LONG_KEY set to value."""
        self.assertEquals(2, len(t))
        for prefix in self._SHORT_PREFIXES + self._LONG_PREFIXES:
            self.assertNodeState(t, prefix, prefix=True)
        self.assertNodeState(t, self._SHORT_KEY, prefix=True, value=value)
        self.assertNodeState(t, self._LONG_KEY, value=value)
        self.assertNodeState(t, self._VERY_LONG_KEY)
        self.assertNodeState(t, self._OTHER_KEY)

    def assertShortTrie(self, t, value=42):
        """Asserts a trie has only _SHORT_KEY set to value."""
        self.assertEquals(1, len(t))
        for prefix in self._SHORT_PREFIXES:
            self.assertNodeState(t, prefix, prefix=True)
        for key in self._LONG_PREFIXES + (
                self._LONG_KEY, self._VERY_LONG_KEY, self._OTHER_KEY):
            self.assertNodeState(t, key)
        self.assertNodeState(t, self._SHORT_KEY, value=value)

    def assertEmptyTrie(self, t):
        """Asserts a trie is empty."""
        self.assertEquals(0, len(t), '%r should be empty: %d' % (t, len(t)))

        for key in self._SHORT_PREFIXES + self._LONG_PREFIXES + (
                self._SHORT_KEY, self._LONG_KEY, self._VERY_LONG_KEY,
                self._OTHER_KEY):
            self.assertNodeState(t, key)

        self.assertRaises(KeyError, t.popitem)

        self.assertEquals('Trie()', str(t))
        self.assertEquals('Trie()', repr(t))

    # pylint: enable=invalid-name

    def do_test_basics(self, trie_factory):
        """Basic trie tests."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        self.assertFullTrie(t)

        self.assertEquals(42, t.pop(self._LONG_KEY))
        self.assertShortTrie(t)

        self.assertEquals(42, t.setdefault(self._SHORT_KEY, 24))
        self.assertShortTrie(t)

        t[self._SHORT_KEY] = 24
        self.assertShortTrie(t, 24)

        self.assertEquals(24, t.setdefault(self._LONG_KEY, 24))
        self.assertFullTrie(t, 24)

        del t[self._LONG_KEY]
        self.assertShortTrie(t, 24)

        self.assertEquals((self.key_from_key(self._SHORT_KEY), 24), t.popitem())
        self.assertEmptyTrie(t)

    def do_test_iterator(self, trie_factory):
        """Trie iterator tests."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        self.assertEquals([42, 42], t.values())
        self.assertEquals([42, 42], list(t.itervalues()))

        short_key = self.key_from_key(self._SHORT_KEY)
        long_key = self.key_from_key(self._LONG_KEY)

        expected_items = [(short_key, 42), (long_key, 42)]
        self.assertEquals(expected_items, sorted(t.items()))
        self.assertEquals(expected_items, sorted(t.iteritems()))

        self.assertEquals([short_key, long_key], sorted(t))
        self.assertEquals([short_key, long_key], sorted(t.keys()))
        self.assertEquals([short_key, long_key], sorted(t.iterkeys()))

    def do_test_subtrie_iterator(self, trie_factory):
        """Subtrie iterator tests."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        long_key = self.key_from_key(self._LONG_KEY)
        prefix = self._LONG_PREFIXES[0]

        self.assertEquals([42, 42], t.values(prefix=self._SHORT_KEY))
        self.assertEquals([42, 42], list(t.itervalues(prefix=self._SHORT_KEY)))
        self.assertEquals([42], t.values(prefix=prefix))
        self.assertEquals([42], list(t.itervalues(prefix=prefix)))

        expected_items = [(long_key, 42)]
        self.assertEquals(expected_items, sorted(t.items(prefix=prefix)))
        self.assertEquals(expected_items, sorted(t.iteritems(prefix=prefix)))

        self.assertEquals([long_key], sorted(t.keys(prefix=prefix)))
        self.assertEquals([long_key], sorted(t.iterkeys(prefix=prefix)))

    def do_test_shallow_iterator(self, trie_factory):
        """Shallow iterator test."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        self.assertEquals([42], t.values(shallow=True))
        self.assertEquals([42], list(t.itervalues(shallow=True)))

        short_key = self.key_from_key(self._SHORT_KEY)

        expected_items = [(short_key, 42)]
        self.assertEquals(expected_items, sorted(t.items(shallow=True)))
        self.assertEquals(expected_items, sorted(t.iteritems(shallow=True)))

        self.assertEquals([short_key], sorted(t.keys(shallow=True)))
        self.assertEquals([short_key], sorted(t.iterkeys(shallow=True)))

    def do_test_splice_operations(self, trie_factory):
        """Splice trie operations tests."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        self.assertEquals([42, 42], list(t[self._SHORT_KEY:]))
        self.assertEquals([42], list(t[self._LONG_PREFIXES[0]:]))

        t[self._SHORT_KEY:] = 24
        self.assertShortTrie(t, 24)

        self.assertEquals([24], list(t[self._SHORT_KEY:]))
        self.assertRaises(KeyError, lambda: list(t[self._LONG_PREFIXES[0]:]))

        t[self._LONG_KEY:] = 24
        self.assertFullTrie(t, 24)

        del t[self._SHORT_KEY:]
        self.assertEmptyTrie(t)

    def do_test_find_prefix(self, trie_factory):
        """Prefix finding methods tests."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        short_pair = (self.key_from_key(self._SHORT_KEY), 42)
        long_pair = (self.key_from_key(self._LONG_KEY), 42)
        none_pair = (None, None)

        self.assertEquals(short_pair, t.shortest_prefix(self._VERY_LONG_KEY))
        self.assertEquals(short_pair, t.shortest_prefix(self._LONG_KEY))
        self.assertEquals(short_pair, t.shortest_prefix(self._VERY_LONG_KEY))
        self.assertEquals(short_pair,
                          t.shortest_prefix(self._LONG_PREFIXES[-1]))
        self.assertEquals(short_pair, t.shortest_prefix(self._SHORT_KEY))
        self.assertEquals(none_pair,
                          t.shortest_prefix(self._SHORT_PREFIXES[-1]))

        self.assertEquals(long_pair, t.longest_prefix(self._VERY_LONG_KEY))
        self.assertEquals(long_pair, t.longest_prefix(self._LONG_KEY))
        self.assertEquals(long_pair, t.longest_prefix(self._VERY_LONG_KEY))
        self.assertEquals(short_pair,
                          t.shortest_prefix(self._LONG_PREFIXES[-1]))
        self.assertEquals(short_pair, t.longest_prefix(self._SHORT_KEY))
        self.assertEquals(none_pair,
                          t.shortest_prefix(self._SHORT_PREFIXES[-1]))

        self.assertEquals([], list(t.prefixes(self._SHORT_PREFIXES[-1])))
        self.assertEquals([short_pair], list(t.prefixes(self._SHORT_KEY)))
        self.assertEquals([short_pair],
                          list(t.prefixes(self._LONG_PREFIXES[-1])))
        self.assertEquals([short_pair, long_pair],
                          list(t.prefixes(self._LONG_KEY)))
        self.assertEquals([short_pair, long_pair],
                          list(t.prefixes(self._VERY_LONG_KEY)))

    def do_test_pickle(self, trie_factory):
        """https://github.com/google/pygtrie/issues/7"""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY, self._VERY_LONG_KEY,
                                             self._OTHER_KEY), 42)
        t = trie_factory(self._TRIE_CLS, d)

        pickled = pickle.dumps(t)
        u = pickle.loads(pickled)

        self.assertEquals(t, u)

    def test_prefix_set(self):
        """PrefixSet test."""
        ps = pygtrie.PrefixSet(factory=self._TRIE_CLS)

        short_key = self.key_from_key(self._SHORT_KEY)
        long_key = self.key_from_key(self._LONG_KEY)
        very_long_key = self.key_from_key(self._VERY_LONG_KEY)
        other_key = self.key_from_key(self._OTHER_KEY)

        for key in (self._LONG_KEY, self._VERY_LONG_KEY):
            ps.add(key)
            self.assertEquals(1, len(ps))
            self.assertEquals([long_key], list(ps.iter()))
            self.assertEquals([long_key], list(iter(ps)))
            self.assertEquals([long_key], list(ps.iter(self._SHORT_KEY)))
            self.assertEquals([long_key], list(ps.iter(self._LONG_KEY)))
            self.assertEquals([very_long_key],
                              list(ps.iter(self._VERY_LONG_KEY)))
            self.assertEquals([], list(ps.iter(self._OTHER_KEY)))

        ps.add(self._SHORT_KEY)
        self.assertEquals(1, len(ps))
        self.assertEquals([short_key], list(ps.iter()))
        self.assertEquals([short_key], list(iter(ps)))
        self.assertEquals([short_key], list(ps.iter(self._SHORT_KEY)))
        self.assertEquals([long_key], list(ps.iter(self._LONG_KEY)))
        self.assertEquals([], list(ps.iter(self._OTHER_KEY)))

        ps.add(self._OTHER_KEY)
        self.assertEquals(2, len(ps))
        self.assertEquals(sorted((short_key, other_key)),
                          sorted(ps.iter()))
        self.assertEquals([short_key], list(ps.iter(self._SHORT_KEY)))
        self.assertEquals([long_key], list(ps.iter(self._LONG_KEY)))
        self.assertEquals([other_key], list(ps.iter(self._OTHER_KEY)))

    def test_equality(self):
        """Tests equality comparison."""
        d = dict.fromkeys((self._SHORT_KEY, self._LONG_KEY), 42)
        # pylint: disable=redefined-outer-name
        tries = [factory(self._TRIE_CLS, d) for _, factory in _TRIE_FACTORIES]

        for i in range(1, len(tries)):
            self.assertEquals(tries[i-1], tries[i],
                              '%r (factory: %s) should equal %r (factory: %s)' %
                              (tries[i-1], _TRIE_FACTORIES[i-1][0],
                               tries[i], _TRIE_FACTORIES[i][0]))

        for i in range(1, len(tries)):
            tries[i-1][self._OTHER_KEY] = 42
            self.assertNotEquals(
                    tries[i-1], tries[i],
                    '%r (factory: %s) should not be equal %r (factory: %s)' %
                    (tries[i-1], _TRIE_FACTORIES[i-1][0],
                     tries[i], _TRIE_FACTORIES[i][0]))


for method_name in TrieTestCase.__dict__.keys():
    if method_name.startswith('do_test_'):
        original_method = getattr(TrieTestCase, method_name)
        method_name = method_name[3:]
        for factory_name, factory in _TRIE_FACTORIES:
            method = functools.partial(original_method, trie_factory=factory)
            method.__doc__ = '%s using %s trie factory.' % (
                    original_method.__doc__[:-2], factory_name)
            method = types.MethodType(method, None, TrieTestCase)
            setattr(TrieTestCase, '%s__%s' % (method_name, factory_name),
                    method)

class CharTrieTestCase(TrieTestCase):
    _TRIE_CLS = pygtrie.CharTrie

    @classmethod
    def key_from_path(cls, path):
        return ''.join(path)


class StringTrieTestCase(TrieTestCase):
    _TRIE_CLS = pygtrie.StringTrie

    _SHORT_KEY = '/home/foo'
    _LONG_KEY = _SHORT_KEY + '/bar/baz'
    _VERY_LONG_KEY = _LONG_KEY + '/qux'
    _OTHER_KEY = '/hom'
    _SHORT_PREFIXES = ('', '/home')
    _LONG_PREFIXES = ('/home/foo/bar',)

    @classmethod
    def path_from_key(cls, key):
        return key.split('/')

    @classmethod
    def key_from_path(cls, path):
        return '/'.join(path)


class SortTest(unittest.TestCase):

    def test_enable_sorting(self):
        keys = sorted(chr(x) for x in range(32, 128) if x != ord('/'))
        t = pygtrie.StringTrie.fromkeys(keys)

        # Unless dict's hash function is weird, trie's keys should not be
        # returned in order.
        self.assertNotEquals(keys, t.keys())
        self.assertEquals(keys, sorted(t.keys()))

        t.enable_sorting()
        self.assertEquals(keys, t.keys())

        t.enable_sorting(False)
        self.assertNotEquals(keys, t.keys())


class TraverseTest(unittest.TestCase):
    _SENTINEL = object()
    _TestNode = collections.namedtuple('TestNode', 'key children value')

    @classmethod
    def _make_test_node(cls, path_conv, path, children, value=_SENTINEL):
        return cls._TestNode(path_conv(path), sorted(children), value)

    def assertNode(self, node, key, children=0, value=_SENTINEL):  # pylint: disable=invalid-name
        self.assertTrue(node)
        self.assertEquals(key, node.key)
        self.assertEquals(children, len(node.children))
        self.assertEquals(value, node.value)
        return node

    def test_traverse_empty_tree(self):
        t = pygtrie.CharTrie()
        r = t.traverse(self._make_test_node)
        self.assertNode(r, '', 0)

    def test_traverse_singleton_tree(self):
        t = pygtrie.CharTrie()
        t.update({'a': 10})

        r = t.traverse(self._make_test_node)
        self.assertNode(r, '', 1)
        self.assertNode(r.children[0], 'a', 0, 10)

    def test_traverse(self):
        t = pygtrie.CharTrie()
        t.update({'aaa': 1, 'aab': 2, 'aac': 3, 'bb': 4})

        r = t.traverse(self._make_test_node)
        # Result:
        #  <>
        #    a
        #      aa
        #        aaa:1
        #        aab:2
        #        aac:3
        #    b
        #      bb:4
        self.assertNode(r, '', 2)

        # For some reason pylint thinks a_node et al. are strings.
        # pylint: disable=no-member

        a_node = self.assertNode(r.children[0], 'a', 1)
        aa_node = self.assertNode(a_node.children[0], 'aa', 3)
        self.assertNode(aa_node.children[0], 'aaa', 0, 1)
        self.assertNode(aa_node.children[2], 'aac', 0, 3)

        b_node = self.assertNode(r.children[1], 'b', 1)
        self.assertNode(b_node.children[0], 'bb', 0, 4)

    def test_traverse_compressing(self):
        t = pygtrie.CharTrie()
        t.update({'aaa': 1, 'aab': 2, 'aac': 3, 'bb': 4})

        def make(path_conv, path, children, value=self._SENTINEL):
            children = sorted(children)
            if value is self._SENTINEL and len(children) == 1:
                # There is only one prefix.
                return children[0]
            else:
                return self._TestNode(path_conv(path), children, value)

        r = t.traverse(make)
        # Result:
        # <>
        #  aa
        #    aaa:1
        #    aab:2
        #    aac:3
        #  bb:4
        self.assertNode(r, '', 2)

        # For some reason pylint thinks a_node et al. are strings.
        # pylint: disable=no-member

        aa_node = self.assertNode(r.children[0], 'aa', 3)
        self.assertNode(aa_node.children[0], 'aaa', 0, 1)
        self.assertNode(aa_node.children[1], 'aab', 0, 2)
        self.assertNode(aa_node.children[2], 'aac', 0, 3)

        self.assertNode(r.children[1], 'bb', 0, 4)

    def test_traverse_ignore_subtrie(self):
        t = pygtrie.CharTrie()
        t.update({'aaa': 1, 'aab': 2, 'aac': 3, 'b': 4})

        cnt = [0]

        def make(path_conv, path, children, value=self._SENTINEL):
            cnt[0] += 1
            if path and path[0] == 'a':
                return None
            else:
                return self._TestNode(
                    path_conv(path), filter(None, children), value)

        r = t.traverse(make)
        # Result:
        # <>
        #  b:4
        self.assertNode(r, '', 1)
        self.assertNode(r.children[0], 'b', 0, 4)
        self.assertEquals(3, cnt[0])


class RecursionTest(unittest.TestCase):
    """Test for deep recursion.

    https://github.com/google/pygtrie/issues/8
    """

    @staticmethod
    def create_trie():
        trie = pygtrie.Trie()
        for x in range(100):
            y = array.array('h', range(x, 1000)).tostring()
            trie.update([(y, x)])
        return trie

    def test_iterator(self):
        for _ in self.create_trie().iteritems():
            pass

    def test_copy(self):
        self.create_trie().copy()


if __name__ == '__main__':
    unittest.main()
