"""Make the kok/ root importable so the production modules resolve as top-level.

The prototypes live directly in kok/ (e.g. adoption_econ.py) and have no
package marker, so tests import them by bare name. This conftest prepends the
parent directory to sys.path once, before collection.
"""

import os
import sys

_KOK_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _KOK_ROOT not in sys.path:
    sys.path.insert(0, _KOK_ROOT)
