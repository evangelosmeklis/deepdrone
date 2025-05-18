"""
Compatibility fix for 'collections.MutableMapping' error in Python 3.10+

This script patches the collections module to provide MutableMapping
for libraries that import it directly from collections rather than collections.abc
"""

import sys
import collections
import collections.abc

# Only apply the patch for Python 3.10 and above
if sys.version_info >= (3, 10):
    # Add MutableMapping to collections for backward compatibility
    collections.MutableMapping = collections.abc.MutableMapping
    print("Applied compatibility patch for collections.MutableMapping") 