Version History
---------------

1.2: 2016/06/21

- Tries can now be pickled.

- Iterating no longer uses recursion so tries of arbitrary depth can be
  iterated over.  The ``traverse`` method, however, still uses recursion
  thus cannot be used on big structures.

1.1: 2016/01/18

- Fixed PyPi installation issues; all should work now.

1.0: 2015/12/16

- The module has been renamed from ``trie`` to ``pygtrie``.  This
  could break current users but see documentation for how to quickly
  upgrade your scripts.

- Added ``traverse`` method which goes through the nodes of the trie
  preserving structure of the tree.  This is a depth-first traversal
  which can be used to search for elements or translate a trie into
  a different tree structure.

- Minor documentation fixes.

0.9.3: 2015/05/28

- Minor documentation fixes.

0.9.2: 2015/05/28

- Added Sphinx configuration and updated docstrings to work better
  with Sphinx.

0.9.1: 2014/02/03

- New name.

0.9: 2014/02/03

- Initial release.
