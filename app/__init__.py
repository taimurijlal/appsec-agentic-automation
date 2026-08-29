"""GlobalTech Customer Account Service (training demo).

A deliberately tiny package used to demonstrate an AI-augmented AppSec
pull-request workflow. All data is fictional and every operation runs against
a local SQLite database. This is a *defensive* code-review teaching lab.
"""

from . import accounts, database

__all__ = ["accounts", "database"]
__version__ = "1.0.0"
