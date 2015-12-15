pygtrie
=======

.. automodule:: pygtrie

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

Trie classes
------------

.. autoclass:: pygtrie.Trie
   :members:

.. autoclass:: pygtrie.CharTrie
   :members:

.. autoclass:: pygtrie.StringTrie
   :members:


PrefixSet class
---------------

.. autoclass:: pygtrie.PrefixSet
   :members:

.. include:: version-history.rst
