pygtrie
=======

.. image:: https://readthedocs.org/projects/pygtrie/badge/?version=latest
   :target: http://pygtrie.readthedocs.io/en/latest/
   :alt: Documentation Status (latest)

.. image:: https://readthedocs.org/projects/pygtrie/badge/?version=stable
   :target: http://pygtrie.readthedocs.io/en/stable/
   :alt: Documentation Status (stable)

pygtrie is a Python library implementing a trie data structure.

`Trie data structure <http://en.wikipedia.org/wiki/Trie>`_, also known
as radix or prefix tree, is a tree associating keys to values where
all the descendants of a node have a common prefix (associated with
that node).

The trie module contains ``Trie``, ``CharTrie`` and ``StringTrie``
classes each implementing a mutable mapping interface, i.e. ``dict``
interface.  As such, in most circumstances, ``Trie`` could be used as
a drop-in replacement for a ``dict``, but the prefix nature of the
data structure is trie’s real strength.

The module also contains ``PrefixSet`` class which uses a trie to
store a set of prefixes such that a key is contained in the set if it
or its prefix is stored in the set.

Features
--------

- A full mutable mapping implementation.

- Supports iterating over as well as deleting a subtrie.

- Supports prefix checking as well as shortest and longest prefix
  look-up.

- Extensible for any kind of user-defined keys.

- A PrefixSet supports “all keys starting with given prefix” logic.

- Can store any value including None.

Installation
------------

To install pygtrie, run::

    pip install pygtrie

Or download the sources and save ``pygtrie.py`` file with your
project.

Upgrading from 0.9.x
--------------------

The 1.0 release introduced backwards incompatibility in naming.  The
module has been renamed from ``trie`` to ``pygtrie``.  Fortunately,
updating scripts using pygtrie should boil down to replacing::

    from pytrie import trie

with::

    import pygtrie as trie
