"""A Python trie implementation.

The module contains Trie, CharTrie and StringTrie classes which implement the
trie data structure (see <http://en.wikipedia.org/wiki/Trie>).  The classes
implement a mutable mapping interface (or in other words interface of
a dictionary) with some additional functionality related to being able to
operate keys with given prefix.

For some simple examples see example.py file.
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

  def Iterate(self, path):
    """Yields all the nodes with values associated to them in the trie.

    Args:
      path: Path leading to this node.  Used to construct the key when
        returning value of this node and as a prefix for children.
    Yields:
      (path, value) tuples.
    """
    if self.value is not _SENTINEL:
      yield path, self.value
    path.append(None)
    for step, node in sorted(self.children.iteritems()):
      path[-1] = step
      for pair in node.Iterate(path):
        yield pair
    path.pop()

  def __eq__(self, other):
    return self.value == other.value and self.children == other.children

  def __ne__(self, other):
    return not self == other  # pylint: disable=g-comparison-negation

  def __nonzero__(self):
    return bool(self.value is not _SENTINEL or self.children)

  __hash__ = None


class Trie(collections.MutableMapping):
  """A trie implementation with dict interface with some extensions.

  Keys used with the Trie must be iterable yielding hashable objects.  In
  other words, for a given key, "dict.fromkeys(key)" must be valid.

  In particular, strings work perfectly fine as trie keys, however when
  getting keys back from iterkeys() method, instead of strings, tuples of
  characters will be yielded.  For that reason, CharTrie or StringTrie may be
  preferred when using Trie with string keys.
  """

  # pylint: disable=invalid-name

  def __init__(self, *args, **kwargs):
    """Initialises the trie.  Arguments are interpreted like update() does."""
    self._root = _Node()
    self.update(*args, **kwargs)

  def clear(self):
    """Removes all the values from the trie."""
    self._root = _Node()

  def update(self, *args, **kwargs):
    """Updates stored values.  Works like dict's update()."""
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
      A new trie where each key from keys has been set to the given value.
    """
    trie = cls()
    for key in keys:
      trie[key] = value
    return trie

  def _GetNode(self, key, create=False):
    """Returns node for given key.  Creates it if requested.

    Args:
      key: A key to look for.
      create: Whether to create the node if it does not exist.
    Returns:
      (node, trace) tuple where node is the node for given key and trace is
      a list specifying path to reach the node including all the encountered
      nodes.  Each element of trace is a (step, node) tuple where step is
      a step from parent node to given node, and node is node on the path.
      The first element of the path is always (None, self._root).
    Raises:
      KeyError: If there is no node for the key and create is False.
    """
    node = self._root
    trace = [(None, node)]
    for step in self.__PathFromKey(key):
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

  def iteritems(self, prefix=_SENTINEL):
    """Yields all nodes with associated values with given prefix.

    Args:
      prefix: Prefix to limit iteration to.
    Yields:
      (key, value) tuples.
    Raises:
      KeyError: If prefix does not match any node.
    """
    node, _ = self._GetNode(prefix)
    for path, value in node.Iterate(list(self.__PathFromKey(prefix))):
      yield (self._KeyFromPath(path), value)

  def iterkeys(self, prefix=_SENTINEL):
    """Yields all keys with associated values with given prefix.

    Args:
      prefix: Prefix to limit iteration to.
    Yields:
      All the keys (with given prefix) with associated values in the trie.
    Raises:
      KeyError: If prefix does not match any node.
    """
    for key, _ in self.iteritems(prefix=prefix):
      yield key

  def itervalues(self, prefix=_SENTINEL):
    """Yields all values associates with keys with given prefix.

    Args:
      prefix: Prefix to limit iteration to.
    Yields:
      All the values associated with keys (with given prefix) in the trie.
    Raises:
      KeyError: If prefix does not match any node.
    """
    node, _ = self._GetNode(prefix)
    for _, value in node.Iterate(list(self.__PathFromKey(prefix))):
      yield value

  def keys(self, prefix=_SENTINEL):
    """Returns a list of all the keys, with given prefix, in the trie."""
    return list(self.iterkeys(prefix=prefix))

  def values(self, prefix=_SENTINEL):
    """Returns a list of values in given subtrie."""
    return list(self.itervalues(prefix=prefix))

  def items(self, prefix=_SENTINEL):
    """Returns a list of (key, value) pairs in given subtrie."""
    return list(self.iteritems(prefix=prefix))

  def __len__(self):
    """Returns number of values in a trie.

    This method is expensive as it iterates over the whole trie.

    Returns:
      Number of keys with values associated with it in the trie.
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
      A bitwise or of HAS_VALUE and HAS_SUBTRIE values indicating that node has
      a value associated with it and that it is a prefix of another existing
      key respectively.
    """
    try:
      node, _ = self._GetNode(key)
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

  def _SliceMaybe(self, key_or_slice):
    """Checks whether argument is a slice or a plain key.

    Args:
      key_or_slice: A key or a slice to test.
    Returns:
      (key, is_slice) tuple.  is_slice indicates whether key_or_slice is
      a slice and key is either key_or_slice itself (if it's not a slice) or
      slice's start position.
    Raises:
      TypeError: If key_or_slice is a slice whose stop or step are not None.
        In other words, only [key:] slices are valid.
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
      If a single key is passed, a value associated with given key.  If
      a slice is passed, a generator of values in specified subtrie.
    Raises:
      ShortKeyError: If the key has no value associated with it but is
        a prefix of some key with a value.
      KeyError: If key has no value associated with it nor is a prefix of an
        existing key.
      TypeError: If key_or_slice is a slice but it's stop or step are not None.
    """
    if self._SliceMaybe(key_or_slice)[1]:
      return self.itervalues(key_or_slice.start)
    node, _ = self._GetNode(key_or_slice)
    if node.value is _SENTINEL:
      raise ShortKeyError(key_or_slice)
    return node.value

  def _Set(self, key, value, only_if_missing=False, clear_children=False):
    """Sets value for a given key.

    Args:
      key: Key to set value of.
      value: Value to set to.
      only_if_missing: If True, value won't be changed if the key is
        already associated with a value.
      clear_children: If True, all children of the node, if any, will
        be removed.
    Returns:
      Value of the node.
    """
    node, _ = self._GetNode(key, create=True)
    if not only_if_missing or node.value is _SENTINEL:
      node.value = value
    if clear_children:
      node.children.clear()
    return node.value

  def __setitem__(self, key_or_slice, value):
    """Sets value associated with given key.

    Args:
      key_or_slice: A key to look for, or a slice.  If it is a slice, the
        whole subtrie (if present) will be replaced by a single node with
        given value set.
      value: Value to set.
    Raises:
      ShortKeyError: If the key has no value associated with it but is
        a prefix of some key with a value.
      KeyError: If key has no value associated with it nor is a prefix of an
        existing key.
      TypeError: If key is a slice whose stop or step are not None.
    """
    key, is_slice = self._SliceMaybe(key_or_slice)
    self._Set(key, value, clear_children=is_slice)

  def setdefault(self, key, value):
    """Sets value of a given node if not set already.  Returns it afterwards."""
    return self._Set(key, value, only_if_missing=True)

  def _CleanupTrace(self, trace):
    """Removes empty nodes going on specified trace.

    Args:
      trace: Trace to the node to cleanup as returned by _GetNode().
    """
    i = len(trace) - 1  # len(path) >= 1 since root is always there
    step, node = trace[i]
    while i and not node:
      i -= 1
      parent_step, parent = trace[i]
      del parent.children[step]
      step, node = parent_step, parent

  def _PopFromNode(self, node, trace, default=_SENTINEL):
    """Remove a value from given node.

    Args:
      node: Node to get value of.
      trace: Trace to that node as returned by _GetNode().
      default: A default value to return if node has no value set.
    Returns:
      Value of the node or default.
    Raises:
      ShortKeyError: If the key has no value associated with it but is
        a prefix of some key with a value.
    """
    if node.value is not _SENTINEL:
      value = node.value
      node.value = _SENTINEL
      self._CleanupTrace(trace)
      return value
    elif default is _SENTINEL:
      raise ShortKeyError()
    else:
      return default

  def pop(self, key, default=_SENTINEL):
    """Deletes value associated with given key and returns it.

    Args:
      key: A key to look for.  Must be iterable.
      default: If specified value that will be returned if given key has no
        value associated with it.  If not specified, method will throw
        KeyError in such cases.
    Returns:
      Removed value, if key had value associated with it, or default value
      (if given).
    Raises:
      ShortKeyError: If default has not been specified and the key has no
        value associated with it but is a prefix of some key with a value.
      KeyError: If default has not been specified and key has no value
        associated with it nor is a prefix of an existing key.
    """
    try:
      return self._PopFromNode(*self._GetNode(key))
    except KeyError:
      if default is not _SENTINEL:
        return default
      raise

  def popitem(self):
    """Deletes a value from the trie.

    Returns:
      (key, value) tuple indicating deleted key.
    Raises:
      KeyError: If trie is empty.
    """
    if not self:
      raise KeyError()
    node = self._root
    trace = [(None, node)]
    while node.value is _SENTINEL:
      step = next(node.children.iterkeys())
      node = node.children[step]
      trace.append((step, node))
    return (self._KeyFromPath((step for step, _ in trace[1:])),
            self._PopFromNode(node, trace))

  def __delitem__(self, key_or_slice):
    """Deletes value associated with given key or raises KeyError.

    Args:
      key_or_slice: A key to look for, or a slice.  If key is a slice, the
        whole subtrie will be removed.
    Raises:
      ShortKeyError: If the key has no value associated with it but is
        a prefix of some key with a value.  This is not thrown is key_or_slice
        is a slice -- in such cases, the whole subtrie is removed.
      KeyError: If key has no value associated with it nor is a prefix of an
        existing key.
      TypeError: If key is a slice whose stop or step are not None.
    """
    key, is_slice = self._SliceMaybe(key_or_slice)
    node, trace = self._GetNode(key)
    if is_slice:
      node.children.clear()
    elif node.value is _SENTINEL:
      raise ShortKeyError(key)
    node.value = _SENTINEL
    self._CleanupTrace(trace)

  def _WalkPath(self, key):
    """Walks towards the node specified by key and yields all found values.

    Args:
      key: Key to look for.
    Yields:
      (path, value) where path is a path to a node and value is value
      associated with that node.
    """
    node = self._root
    path = self.__PathFromKey(key)
    pos = 0
    while True:
      if node.value is not _SENTINEL:
        yield (path[:pos], node.value)
      if pos == len(path):
        break
      node = node.children.get(path[pos])
      if not node:
        break
      pos += 1

  class FindPrefixResult(collections.namedtuple('FindPrefixResult',
                                                'key value')):

    def __nonzero__(self):
      return self.key is not None

  def FindShortestPrefix(self, key):
    """Finds a shortest prefix of key with a value.

    Args:
      key: Key to look for.
    Returns:
      FindPrefixResult(k, value) where k is the shortest prefix of key (it may
      be equal key) and value is value associated with that key.  If no node
      is found, FindPrefixResult(None, None) is returned, which evaluates to
      False in boolean context by the way.
    """
    for path, value in self._WalkPath(key):
      return self.FindPrefixResult(self._KeyFromPath(path), value)
    return self.FindPrefixResult(None, None)

  def FindLongestPrefix(self, key):
    """Finds a longest prefix of key with a value.

    Args:
      key: Key to look for.
    Returns:
      FindPrefixResult(k, value) where k is the longest prefix of key (it may
      be equal key) and value is value associated with that key.  If no node
      is found, FindPrefixResult(None, None) is returned, which evaluates to
      False in boolean context by the way.
    """
    ret = None
    for ret in self._WalkPath(key):
      pass
    if ret:
      return self.FindPrefixResult(self._KeyFromPath(ret[0]), ret[1])
    else:
      return self.FindPrefixResult(None, None)

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

  def __PathFromKey(self, key):
    """Converts a user visible key object to internal path representation.

    Args:
      key: User supplied key or _SENTINEL.
    Returns:
      () if key was _SENTINEL, otherwise whatever _PathFroMKey returns.
    Raises:
      TypeError: If key is of invalid type.
    """
    return () if key is _SENTINEL else self._PathFromKey(key)

  def _PathFromKey(self, key):
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

  def _KeyFromPath(self, path):
    """Converts an internal path into a user visible key object.

    The default implementation creates a tuple from the path.

    Args:
      path: Internal path representation.
    Returns:
      A user visible key object.
    """
    return tuple(path)


class CharTrie(Trie):
  """A variant of a Trie which accepts strings as keys.

  The only difference between CharTrie and Trie is that when CharTrie returns
  keys back to the client (for instance in keys() method is called), those
  keys are returned as strings.
  """

  def _KeyFromPath(self, path):
    return ''.join(path)


class StringTrie(Trie):
  """A variant of a Trie which accepts strings with a separator as keys.

  The trie accepts stings as keys which are split into components using
  a separator specified during initialisation ("/" by default).
  """

  def __init__(self, *args, **kwargs):
    # pylint: disable=g-doc-args
    """Initialises the trie.

    Except for a "separator" named argument, all other arguments are
    interpreted like update() does.

    Args:
      *args: Passed to update().
      **kwargs: Passed to update().
      separator: A separator to use when separating key into a path used by
        the trie.  "/" is used if this argument is not specified.  This named
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

  def _PathFromKey(self, key):
    return key.split(self._separator)

  def _KeyFromPath(self, path):
    return self._separator.join(path)
