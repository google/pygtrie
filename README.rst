pytrie is a Python library implementing a trie data structure.

Trie data structure, also known as radix or prefix tree, is an ordered
tree associating keys to values where all the descendants of a node
have a common prefix (associated with that node).

The trie module contains Trie, CharTrie and StringTrie classes each
implementing a mutable mapping interface, i.e. interface of the
dictionary.  As such, in most circumstances, Trie could be used as
a drop-in replacement for a dict.  Obviously the prefix nature of the
data structure is what gives it its strengths.

Features
--------

- A full mutable mapping implementation.

- Supports iterating over as well as deleting a subtrie.

- Supports prefix checking as well as shortest and longest prefix
  look-up.

- Extensible for any kind of user-defined keys.

Version History
---------------

0.9: 2014/02/03

- Initial release.
