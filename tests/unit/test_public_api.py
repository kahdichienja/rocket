"""Everything `__all__` promises must actually be importable.

`__all__` is the package's public surface, and a name listed there that does not exist is not a typo with
no consequences: `from sha_claim import *` raises `AttributeError` on it, and anyone reading the list —
or a tool generating documentation from it — is told about an export that is not there.

`FileId` sat in `__all__` from before 0.1.49 without being imported into `__init__.py`, while
`files.download_link()` took it as a parameter type. So the one name a caller needed in order to type
that call was the one name they could not import.

Checked as a whole rather than name by name, because the next one will be added the same way this one
was: by hand, in a list of two hundred.
"""

from __future__ import annotations

import sha_claim


def test_every_exported_name_exists() -> None:
    missing = [name for name in sha_claim.__all__ if not hasattr(sha_claim, name)]
    assert not missing, (
        f"__all__ promises {missing}, which `from sha_claim import *` cannot deliver. "
        "Import the name in __init__.py, or take it out of __all__."
    )


def test_star_import_succeeds() -> None:
    """The failure the above prevents, reproduced the way a caller would meet it."""
    namespace: dict[str, object] = {}
    # `exec` because a star import is only legal at module level, and this has to run as a caller's would.
    exec("from sha_claim import *", namespace)

    assert "AsyncSHAClient" in namespace


def test_nothing_is_promised_twice() -> None:
    """A duplicate is harmless to import and a reliable sign the list was edited in two places."""
    duplicates = sorted({n for n in sha_claim.__all__ if sha_claim.__all__.count(n) > 1})

    assert not duplicates, f"__all__ lists {duplicates} more than once"
