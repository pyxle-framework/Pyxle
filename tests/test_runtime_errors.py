"""Tests for pyxle.runtime — LoaderError and ActionError."""

from __future__ import annotations

import pytest

from pyxle.runtime import ActionError, LoaderError


# ---------------------------------------------------------------------------
# LoaderError
# ---------------------------------------------------------------------------


class TestLoaderError:
    def test_default_status_code_is_500(self):
        err = LoaderError("something broke")
        assert err.status_code == 500
        assert err.message == "something broke"
        assert str(err) == "something broke"

    def test_custom_status_code(self):
        err = LoaderError("not found", status_code=404)
        assert err.status_code == 404

    def test_custom_data(self):
        err = LoaderError("bad input", status_code=400, data={"field": "email"})
        assert err.data == {"field": "email"}

    def test_empty_data_defaults_to_empty_dict(self):
        err = LoaderError("oops")
        assert err.data == {}

    def test_is_exception(self):
        err = LoaderError("fail")
        assert isinstance(err, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(LoaderError, match="database timeout"):
            raise LoaderError("database timeout", status_code=503)

    def test_does_not_conflict_with_action_error(self):
        """LoaderError and ActionError are distinct exception types."""
        loader_err = LoaderError("loader fail")
        action_err = ActionError("action fail")
        assert type(loader_err) is not type(action_err)

        with pytest.raises(LoaderError):
            raise loader_err

        with pytest.raises(ActionError):
            raise action_err


# ---------------------------------------------------------------------------
# ActionError (existing — regression coverage)
# ---------------------------------------------------------------------------


class TestActionError:
    def test_default_status_code_is_400(self):
        err = ActionError("invalid")
        assert err.status_code == 400

    def test_custom_status_code(self):
        err = ActionError("forbidden", status_code=403)
        assert err.status_code == 403

    def test_data_field(self):
        err = ActionError("bad", data={"errors": ["field required"]})
        assert err.data == {"errors": ["field required"]}

    def test_message_is_str(self):
        err = ActionError("hello")
        assert str(err) == "hello"
        assert err.message == "hello"
