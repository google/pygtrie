# -*- coding: utf-8 -*-
"""Implementation of a trie data structure.

`Trie data structure <http://en.wikipedia.org/wiki/Trie>`_, also known as radix
or prefix tree, is a tree associating keys to values where all the descendants
of a node have a common prefix (associated with that node).

The trie module contains :class:`trie.Trie`, :class:`trie.CharTrie` and
:class:`trie.StringTrie` classes each implementing a mutable mapping interface,
i.e. :class:`dict` interface.  As such, in most circumstances,
:class:`trie.Trie` could be used as a drop-in replacement for a :class:`dict`,
but the prefix nature of the data structure is trie’s real strength.

The module also contains :class:`trie.PrefixSet` class which uses a trie to
store a set of prefixes such that a key is contained in the set if it or its
prefix is stored in the set.

Features
--------

- A full mutable mapping implementation.

- Supports iterating over as well as deleting a subtrie.

- Supports prefix checking as well as shortest and longest prefix
  look-up.

- Extensible for any kind of user-defined keys.

- A PrefixSet supports “all keys starting with given prefix” logic.

- Can store any value including None.

For some simple examples see ``example.py`` file.
"""

__author__ = 'Michal Nazarewicz <mina86@mina86.com>'
__copyright__ = 'Copyright 2014 Google Inc.'


import collections


class ShortKeyError(KeyError):
  """Raised when given key is a prefix of a longer key."""
  pass


_SENTINEL = object()


class _Node(object):
  """A single node of a trie.

  Stores value associated with the node and dictionary of children.
  """
  __slots__ = ('children', 'value')

  def __init__(self):
    self.children = {}
    self.value = _SENTINEL

  def iterate(self, path, shallow=False):
    """Yields all the nodes with values associated to them in the trie.

    Args:
      path: Path leading to this node.  Used to construct the key when
          returning value of this node and as a prefix for children.
      shallow: Perform a shallow traversal, i.e. do not yield nodes if their
          prefix has been yielded.

    Yields:
      ``(path, value)`` tuples.
    """
    if self.value is not _SENTINEL:
      yield path, self.value
      if shallow:
        return
    path.append(None)
    for step, node in sorted(self.children.iteritems()):
      path[-1] = step
      for pair in node.iterate(path, shallow=shallow):
        yield pair
    path.pop()

  def traverse(self, node_factory, path_conv, path):
    """Traverses the node and returns another type of node from node_factory.

    Args:
      node_factory: Callable function to construct new nodes.
      path_conv: Callable function to convert node path to a key.
      path: Current path for this node.

    Returns:
      An object constructed by calling node_factory(path_conv, path, children,
      value=...), where children are constructed by node_factory from the
      children of this node. There doesn't need to be 1:1 correspondence between
      original nodes in the trie and constructed nodes (see
      make_test_node_and_compress in test.py).
    """
    def children():
      for step, node in sorted(self.children.iteritems()):
        yield node.traverse(node_factory, path_conv, path + [step])

    args = [path_conv, tuple(path), children()]

    if self.value is not _SENTINEL:
      args.append(self.value)

    return node_factory(*args)

  def __eq__(self, other):
    return self.value == other.value and self.children == other.children

  def __ne__(self, other):
    return not self == other  # pylint: disable=g-comparison-negation

  def __nonzero__(self):
    return bool(self.value is not _SENTINEL or self.children)

  __hash__ = None


class Trie(collections.MutableMapping):
  """A trie implementation with dict interface plus some extensions.

  Keys used with the :class:`trie.Trie` must be iterable, yielding hashable
  objects.  In other words, for a given key, ``dict.fromkeys(key)`` must be
  valid.

  In particular, strings work fine as trie keys, however when getting keys back
  from iterkeys() method for example, instead of strings, tuples of characters
  are produced.  For that reason, :class:`trie.CharTrie` or
  :class:`trie.StringTrie` may be preferred when using :class:`trie.Trie` with
  string keys.
  """

  # pylint: disable=invalid-name

  def __init__(self, *args, **kwargs):
    """Initialises the trie.

    Arguments are interpreted the same way :func:`Trie.update` interprets them.
    """
    self._root = _Node()
    self.update(*args, **kwargs)

  def clear(self):
    """Removes all the values from the trie."""
    self._root = _Node()

  def update(self, *args, **kwargs):
    """Updates stored values.  Works like :func:`dict.update`."""
    if len(args) > 1:
      raise ValueError('update() takes at most one positional argument, '
                       '%d given.' % len(args))
    # We have this here instead of just letting MutableMapping.update() handle
    # things because it will iterate over keys and for each key retrieve the
    # value.  With Trie, this may be expensive since the path to the node
    # would have to be walked twice.  Instead, we have our own implementation
    # where iteritems() is used avoiding the unnecessary value look-up.
    if args and isinstance(args[0], Trie):
      for key, value in args[0].iteritems():
        self[key] = value
      args = ()
    super(Trie, self).update(*args, **kwargs)

  def copy(self):
    """Returns a shallow copy of the trie."""
    return self.__class__(self)

  @classmethod
  def fromkeys(cls, keys, value=None):
    """Creates a new trie with given keys set.

    Args:
      keys: An iterable of keys that should be set in the new trie.
      value: Value to associate with given keys.

    Returns:
      A new trie where each key from ``keys`` has been set to the given value.
    """
    trie = cls()
    for key in keys:
      trie[key] = value
    return trie

  def _get_node(self, key, create=False):
    """Returns node for given key.  Creates it if requested.

    Args:
      key: A key to look for.
      create: Whether to create the node if it does not exist.

    Returns:
      ``(node, trace)`` tuple where ``node`` is the node for given key and
      ``trace`` is a list specifying path to reach the node including all the
      encountered nodes.  Each element of trace is a ``(step, node)`` tuple
      where ``step`` is a step from parent node to given node, and ``node`` is
      node on the path.  The first element of the path is always ``(None,
      self._root)``.

    Raises:
      KeyError: If there is no node for the key and ``create`` is ``False``.
    """
    node = self._root
    trace = [(None, node)]
    for step in self.__path_from_key(key):
      if create:
        node = node.children.setdefault(step, _Node())
      else:
        node = node.children.get(step)
        if not node:
          raise KeyError(key)
      trace.append((step, node))
    return node, trace

  def __iter__(self):
    return self.iterkeys()

  def iteritems(self, prefix=_SENTINEL, shallow=False):
    """Yields all nodes with associated values with given prefix.

    Args:
      prefix: Prefix to limit iteration to.
      shallow: Perform a shallow traversal, i.e. do not yield items if their
          prefix has been yielded.

    Yields:
      ``(key, value)`` tuples.

    Raises:
      KeyError: If ``prefix`` does not match any node.
    """
    node, _ = self._get_node(prefix)
    for path, value in node.iterate(list(self.__path_from_key(prefix)),
                                    shallow=shallow):
      yield (self._key_from_path(path), value)

  def iterkeys(self, prefix=_SENTINEL, shallow=False):
    """Yields all keys having associated values with given prefix.

    Args:
      prefix: Prefix to limit iteration to.
      shallow: Perform a shallow traversal, i.e. do not yield keys if their
          prefix has been yielded.

    Yields:
      All the keys (with given prefix) with associated values in the trie.

    Raises:
      KeyError: If ``prefix`` does not match any node.
    """
    for key, _ in self.iteritems(prefix=prefix, shallow=shallow):
      yield key

  def itervalues(self, prefix=_SENTINEL, shallow=False):
    """Yields all values associated with keys with given prefix.

    Args:
      prefix: Prefix to limit iteration to.
      shallow: Perform a shallow traversal, i.e. do not yield values if their
          prefix has been yielded.

    Yields:
      All the values associated with keys (with given prefix) in the trie.

    Raises:
      KeyError: If ``prefix`` does not match any node.
    """
    node, _ = self._get_node(prefix)
    for _, value in node.iterate(list(self.__path_from_key(prefix)),
                                 shallow=shallow):
      yield value

  def keys(self, prefix=_SENTINEL, shallow=False):
    """Returns a list of all the keys, with given prefix, in the trie."""
    return list(self.iterkeys(prefix=prefix, shallow=shallow))

  def values(self, prefix=_SENTINEL, shallow=False):
    """Returns a list of values in given subtrie."""
    return list(self.itervalues(prefix=prefix, shallow=shallow))

  def items(self, prefix=_SENTINEL, shallow=False):
    """Returns a list of ``(key, value)`` pairs in given subtrie."""
    return list(self.iteritems(prefix=prefix, shallow=shallow))

  def __len__(self):
    """Returns number of values in a trie.

    This method is expensive as it iterates over the whole trie.
    """
    return sum(1 for _ in self.itervalues())

  def __nonzero__(self):
    return bool(self._root)

  HAS_VALUE = 1
  HAS_SUBTRIE = 2

  def has_node(self, key):
    """Returns whether given node is in the trie.

    Args:
      key: A key to look for.

    Returns:
      A bitwise or of ``HAS_VALUE`` and ``HAS_SUBTRIE`` values indicating that
      node has a value associated with it and that it is a prefix of another
      existing key respectively.
    """
    try:
      node, _ = self._get_node(key)
    except KeyError:
      return 0
    return ((self.HAS_VALUE * int(node.value is not _SENTINEL)) |
            (self.HAS_SUBTRIE * int(bool(node.children))))

  def has_key(self, key):
    """Indicates whether given key has value associated with it."""
    return bool(self.has_node(key) & self.HAS_VALUE)

  def has_subtrie(self, key):
    """Returns whether given key is a prefix of another key in the trie."""
    return bool(self.has_node(key) & self.HAS_SUBTRIE)

  def _slice_maybe(self, key_or_slice):
    """Checks whether argument is a slice or a plain key.

    Args:
      key_or_slice: A key or a slice to test.

    Returns:
      ``(key, is_slice)`` tuple.  ``is_slice`` indicates whether
      ``key_or_slice`` is a slice and ``key`` is either ``key_or_slice`` itself
      (if it's not a slice) or slice's start position.

    Raises:
      TypeError: If ``key_or_slice`` is a slice whose stop or step are not
        ``None`` In other words, only ``[key:]`` slices are valid.
    """
    if isinstance(key_or_slice, slice):
      if key_or_slice.stop is not None or key_or_slice.step is not None:
        raise TypeError(key_or_slice)
      return key_or_slice.start, True
    return key_or_slice, False

  def __getitem__(self, key_or_slice):
    """Returns value associated with given key or raises KeyError.

    Args:
      key_or_slice: A key or a slice to look for.

    Returns:
      If a single key is passed, a value associated with given key.  If a slice
      is passed, a generator of values in specified subtrie.

    Raises:
      ShortKeyError: If the key has no value associated with it but is a prefix
          of some key with a value.  Note that :class:`ShortKeyError` is
          subclass of :class:`KeyError`.
      KeyError: If key has no value associated with it nor is a prefix of an
          existing key.
      TypeError: If ``key_or_slice`` is a slice but it's stop or step are not
          ``None``.
    """
    if self._slice_maybe(key_or_slice)[1]:
      return self.itervalues(key_or_slice.start)
    node, _ = self._get_node(key_or_slice)
    if node.value is _SENTINEL:
      raise ShortKeyError(key_or_slice)
    return node.value

  def _set(self, key, value, only_if_missing=False, clear_children=False):
    """Sets value for a given key.

    Args:
      key: Key to set value of.
      value: Value to set to.
      only_if_missing: If ``True``, value won't be changed if the key is already
          associated with a value.
      clear_children: If ``True``, all children of the node, if any, will be
          removed.

    Returns:
      Value of the node.
    """
    node, _ = self._get_node(key, create=True)
    if not only_if_missing or node.value is _SENTINEL:
      node.value = value
    if clear_children:
      node.children.clear()
    return node.value

  def __setitem__(self, key_or_slice, value):
    """Sets value associated with given key.

    Args:
      key_or_slice: A key to look for, or a slice.  If it is a slice, the whole
          subtrie (if present) will be replaced by a single node with given
          value set.
      value: Value to set.

    Raises:
      ShortKeyError: If the key has no value associated with it but is a prefix
          of some key with a value.  Note that :class:`ShortKeyError` is
          subclass of :class:`KeyError`.
      KeyError: If key has no value associated with it nor is a prefix of an
          existing key.
      TypeError: If key is a slice whose stop or step are not None.
    """
    key, is_slice = self._slice_maybe(key_or_slice)
    self._set(key, value, clear_children=is_slice)

  def setdefault(self, key, value):
    """Sets value of a given node if not set already.  Returns it afterwards."""
    return self._set(key, value, only_if_missing=True)

  def _cleanup_trace(self, trace):
    """Removes empty nodes present on specified trace.

    Args:
      trace: Trace to the node to cleanup as returned by :func:`Trie._get_node`.
    """
    i = len(trace) - 1  # len(path) >= 1 since root is always there
    step, node = trace[i]
    while i and not node:
      i -= 1
      parent_step, parent = trace[i]
      del parent.children[step]
      step, node = parent_step, parent

  def _pop_from_node(self, node, trace, default=_SENTINEL):
    """Removes a value from given node.

    Args:
      node: Node to get value of.
      trace: Trace to that node as returned by :func:`Trie._get_node`.
      default: A default value to return if node has no value set.

    Returns:
      Value of the node or ``default``.

    Raises:
      ShortKeyError: If the node has no value associated with it and ``default``
          has not been given.
    """
    if node.value is not _SENTINEL:
      value = node.value
      node.value = _SENTINEL
      self._cleanup_trace(trace)
      return value
    elif default is _SENTINEL:
      raise ShortKeyError()
    else:
      return default

  def pop(self, key, default=_SENTINEL):
    """Deletes value associated with given key and returns it.

    Args:
      key: A key to look for.  Must be iterable.
      default: If specified, value that will be returned if given key has no
          value associated with it.  If not specified, method will throw
          KeyError in such cases.

    Returns:
      Removed value, if key had value associated with it, or ``default`` (if
      given).

    Raises:
      ShortKeyError: If ``default`` has not been specified and the key has no
          value associated with it but is a prefix of some key with a value.
          Note that :class:`ShortKeyError` is subclass of :class:`KeyError`.
      KeyError: If default has not been specified and key has no value
          associated with it nor is a prefix of an existing key.
    """
    try:
      return self._pop_from_node(*self._get_node(key))
    except KeyError:
      if default is not _SENTINEL:
        return default
      raise

  def popitem(self):
    """Deletes a value from the trie.

    Returns:
      ``(key, value)`` tuple indicating deleted key.

    Raises:
      KeyError: If the trie is empty.
    """
    if not self:
      raise KeyError()
    node = self._root
    trace = [(None, node)]
    while node.value is _SENTINEL:
      step = next(node.children.iterkeys())
      node = node.children[step]
      trace.append((step, node))
    return (self._key_from_path((step for step, _ in trace[1:])),
            self._pop_from_node(node, trace))

  def __delitem__(self, key_or_slice):
    """Deletes value associated with given key or raises KeyError.

    Args:
      key_or_slice: A key to look for, or a slice.  If key is a slice, the
          whole subtrie will be removed.

    Raises:
      ShortKeyError: If the key has no value associated with it but is a prefix
          of some key with a value.  This is not thrown is key_or_slice is
          a slice -- in such cases, the whole subtrie is removed.  Note that
          :class:`ShortKeyError` is subclass of :class:`KeyError`.
      KeyError: If key has no value associated with it nor is a prefix of an
          existing key.
      TypeError: If key is a slice whose stop or step are not ``None``.
    """
    key, is_slice = self._slice_maybe(key_or_slice)
    node, trace = self._get_node(key)
    if is_slice:
      node.children.clear()
    elif node.value is _SENTINEL:
      raise ShortKeyError(key)
    node.value = _SENTINEL
    self._cleanup_trace(trace)

  def prefixes(self, key):
    """Walks towards the node specified by key and yields all found values.

    Args:
      key: Key to look for.

    Yields:
      ``(k, value)`` pairs denoting keys with associated values encountered on
      the way towards the specified key.
    """
    node = self._root
    path = self.__path_from_key(key)
    pos = 0
    while True:
      if node.value is not _SENTINEL:
        yield self._key_from_path(path[:pos]), node.value
      if pos == len(path):
        break
      node = node.children.get(path[pos])
      if not node:
        break
      pos += 1

  def shortest_prefix(self, key):
    """Finds the shortest prefix of a key with a value.

    Args:
      key: Key to look for.

    Returns:
      ``(k, value)`` where ``k`` is the shortest prefix of ``key`` (it may equal
      ``key``) and ``value`` is a value associated with that key.  If no node is
      found, ``(None, None)`` is returned.
    """
    for ret in self.prefixes(key):
      return ret
    return (None, None)

  def longest_prefix(self, key):
    """Finds the longest prefix of a key with a value.

    Args:
      key: Key to look for.

    Returns:
      ``(k, value)`` where ``k`` is the longest prefix of ``key`` (it may equal
      ``key``) and ``value`` is a value associated with that key.  If no node is
      found, ``(None, None)`` is returned.
    """
    ret = (None, None)
    for ret in self.prefixes(key):
      pass
    return ret

  def __eq__(self, other):
    return self._root == other._root  # pylint: disable=protected-access

  def __ne__(self, other):
    return self._root != other._root  # pylint: disable=protected-access

  def __str__(self):
    return 'Trie(%s)' % (
        ', '.join('%s: %s' % item for item in self.iteritems()))

  def __repr__(self):
    if self:
      return  'Trie((%s,))' % (
          ', '.join('(%r, %r)' % item for item in self.iteritems()))
    else:
      return 'Trie()'

  def __path_from_key(self, key):
    """Converts a user visible key object to internal path representation.

    Args:
      key: User supplied key or ``_SENTINEL``.

    Returns:
      An empty tuple if ``key`` was ``_SENTINEL``, otherwise whatever
      :func:`Trie._path_from_key` returns.

    Raises:
      TypeError: If ``key`` is of invalid type.
    """
    return () if key is _SENTINEL else self._path_from_key(key)

  def _path_from_key(self, key):
    """Converts a user visible key object to internal path representation.

    The default implementation simply returns key.

    Args:
      key: User supplied key.

    Returns:
      A path, which is an iterable of steps.  Each step must be hashable.

    Raises:
      TypeError: If key is of invalid type.
    """
    return key

  def _key_from_path(self, path):
    """Converts an internal path into a user visible key object.

    The default implementation creates a tuple from the path.

    Args:
      path: Internal path representation.
    Returns:
      A user visible key object.
    """
    return tuple(path)

  def traverse(self, node_factory, prefix=_SENTINEL):
    """Traverses the tree using node_factory object.

    node_factory is a callable function which accepts (path_conv, path,
    children, value=...) arguments, where path_conv is a lambda converting path
    representation to key, path is the path to this node, children is an
    iterable of children nodes constructed by node_factory, optional value is
    the value associated with the path.

    Note: node_factory's children argument is a generator which has a few
    consequences:
    * To traverse into node's children, the generator must be iterated over.
      This can by accomplished by a simple "children = list(children)"
      statement.
    * Ignoring the argument allows node_factory to stop the traversal from going
      into the children of the node.  In other words, whole subtrie can be
      removed from traversal if node_factory chooses so.
    * If children is stored as is (i.e. as a generator) when it is iterated over
      later on it will see state of the trie as it is during the iteration and
      not when traverse method was called.

    Args:
      node_factory: Makes opaque objects from the keys and values of the trie.
      prefix: Prefix for node to start traversal, by default starts at root.

    Returns:
      Node object constructed by node_factory corresponding to the root node.
    """
    node, _ = self._get_node(prefix)
    return node.traverse(node_factory, self._key_from_path,
                         list(self.__path_from_key(prefix)))

class CharTrie(Trie):
  """A variant of a :class:`trie.Trie` which accepts strings as keys.

  The only difference between :class:`trie.CharTrie` and :class:`trie.Trie` is
  that when :class:`trie.CharTrie` returns keys back to the client (for instance
  in keys() method is called), those keys are returned as strings.
  """

  def _key_from_path(self, path):
    return ''.join(path)


class StringTrie(Trie):
  """A variant of :class:`trie.Trie` accepting strings with a separator as keys.

  The trie accepts strings as keys which are split into components using
  a separator specified during initialisation ("/" by default).
  """

  def __init__(self, *args, **kwargs):
    """Initialises the trie.

    Except for a ``separator`` named argument, all other arguments are
    interpreted the same way :func:`Trie.update` interprets them.

    Args:
      *args: Passed to super class initialiser.
      **kwargs: Passed to super class initialiser.
      separator: A separator to use when splitting keys into paths used by the
          trie.  "/" is used if this argument is not specified.  This named
          argument is not specified on the function's prototype because of
          Python's limitations.
    """
    self._separator = kwargs.pop('separator', '/')
    super(StringTrie, self).__init__(*args, **kwargs)

  @classmethod
  def fromkeys(cls, keys, value=None, separator='/'):
    trie = cls(separator=separator)
    for key in keys:
      trie[key] = value
    return trie

  def _path_from_key(self, key):
    return key.split(self._separator)

  def _key_from_path(self, path):
    return self._separator.join(path)


class PrefixSet(collections.MutableSet):
  """A set of prefixes.

  :class:`trie.PrefixSet` works similar to a normal set except it is said to
  contain a key if the key or it's prefix is stored in the set.  For instance,
  if "foo" is added to the set, the set contains "foo" as well as "foobar".

  The set supports addition of elements but does *not* support removal of
  elements.  This is because there's no obvious consistent and intuitive
  behaviour for element deletion.
  """

  def __init__(self, iterable=None, factory=Trie, **kwargs):
    """Initialises the prefix set.

    Args:
      iterable: A sequence of keys to add to the set.
      factory: A function used to create a trie used by the
          :class:`trie.PrefixSet`.
      kwargs: Additional keyword arguments passed to the factory function.
    """
    trie = factory(**kwargs)
    if iterable:
      trie.update((key, True) for key in iterable)
    self._trie = trie

  def copy(self):
    """Returns a copy of the prefix set."""
    return self.__class__(self._trie)

  def clear(self):
    """Removes all keys from the set."""
    self._trie.clear()

  def __contains__(self, key):
    """Checks whether set contains key or its prefix."""
    return bool(self._trie.shortest_prefix(key)[1])

  def __iter__(self):
    """Return iterator over all prefixes in the set.

    See :func:`PrefixSet.iter` method for more info.
    """
    return self._trie.iterkeys()

  def iter(self, prefix=_SENTINEL):
    """Iterates over all keys in the set optionally starting with a prefix.

    Since a key does not have to be explicitly added to the set to be an element
    of the set, this method does not iterate over all possible keys that the set
    contains, but only over the shortest set of prefixes of all the keys the set
    contains.

    For example, if "foo" has been added to the set, the set contains also
    "foobar", but this method will *not* iterate over "foobar".

    If ``prefix`` argument is given, method will iterate over keys with given
    prefix only.  The keys yielded from the function if prefix is given does not
    have to be a subset (in mathematical sense) of the keys yielded when there
    is not prefix.  This happens, if the set contains a prefix of the given
    prefix.

    For example, if only "foo" has been added to the set, iter method called
    with no arguments will yield "foo" only.  However, when called with
    "foobar" argument, it will yield "foobar" only.
    """
    if prefix is _SENTINEL:
      return iter(self)
    elif self._trie.has_node(prefix):
      return self._trie.iterkeys(prefix=prefix)
    elif prefix in self:
      # Make sure the type of returned keys is consistent.
      return (self._trie._key_from_path(self._trie._path_from_key(prefix)),)
    else:
      return ()

  def __len__(self):
    """Returns number of keys stored in the set.

    Since a key does not have to be explicitly added to the set to be an element
    of the set, this method does not count over all possible keys that the set
    contains (since that would be infinity), but only over the shortest set of
    prefixes of all the keys the set contains.

    For example, if "foo" has been added to the set, the set contains also
    "foobar", but this method will *not* count "foobar".
    """
    return len(self._trie)

  def add(self, key):
    """Adds given key to the set.

    If the set already contains prefix of the key being added, this operation
    has no effect.  If the key being added is a prefix of some existing keys
    in the set, those keys are deleted and replaced by a single entry for the
    key being added.

    For example, if the set contains key "foo" adding a key "foobar" does not
    change anything.  On the other hand, if the set contains keys "foobar" and
    "foobaz", adding a key "foo" will replace those two keys with a single key
    "foo".

    This makes a difference when iterating over the keys or counting number of
    keys.  Counter intuitively, adding of a key can *decrease* size of the set.

    Args:
      key: Key to add.
    """
    if key not in self:
      self._trie[key:] = True

  def discard(self, key):
    raise NotImplementedError(
      'Removing keys from PrefixSet is not implemented.')

  def remove(self, key):
    raise NotImplementedError(
      'Removing keys from PrefixSet is not implemented.')

  def pop(self):
    raise NotImplementedError(
      'Removing keys from PrefixSet is not implemented.')
