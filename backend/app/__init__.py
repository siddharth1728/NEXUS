"""NEXUS Backend Application Package."""

import os

# Ensure pure-Python fallback for environments with C-extension restrictions
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT", "1")
