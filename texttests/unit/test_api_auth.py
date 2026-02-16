from substrate.api import ApiError, api_inbox
from pathlib import Path


def test_api_auth_rejects():
    try:
        api_inbox(
            Path("/tmp"),
            limit=1,
            offset=0,
            sort="updated_desc",
            status=None,
            privacy=None,
            token_required="secret",
            token_provided="wrong",
        )
    except ApiError as exc:
        assert exc.status == 401
    else:
        raise AssertionError("Expected ApiError")
