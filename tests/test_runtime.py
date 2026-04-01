"""Tests for pyxle.runtime decorators and error types."""

from __future__ import annotations

import pytest

from pyxle.runtime import ActionError, action, server


class TestServerDecorator:
    def test_tags_function(self) -> None:
        @server
        async def load(request): ...

        assert getattr(load, "__pyxle_loader__") is True

    def test_returns_same_function(self) -> None:
        async def load(request): ...

        result = server(load)
        assert result is load

    def test_does_not_wrap(self) -> None:
        async def load(request):
            return 42

        decorated = server(load)
        assert decorated.__name__ == "load"


class TestActionDecorator:
    def test_tags_function(self) -> None:
        @action
        async def save(request): ...

        assert getattr(save, "__pyxle_action__") is True

    def test_returns_same_function(self) -> None:
        async def save(request): ...

        result = action(save)
        assert result is save

    def test_does_not_wrap(self) -> None:
        async def save(request):
            return {"ok": True}

        decorated = action(save)
        assert decorated.__name__ == "save"

    def test_async_coroutine_preserved(self) -> None:
        import asyncio

        @action
        async def do_thing(request):
            return {"done": True}

        assert asyncio.iscoroutinefunction(do_thing)

    def test_no_pyxle_loader_tag(self) -> None:
        @action
        async def save(request): ...

        assert not getattr(save, "__pyxle_loader__", False)


class TestActionError:
    def test_default_status_code(self) -> None:
        err = ActionError("something failed")
        assert err.status_code == 400
        assert err.message == "something failed"
        assert err.data == {}

    def test_custom_status_code(self) -> None:
        err = ActionError("forbidden", status_code=403)
        assert err.status_code == 403

    def test_data_payload(self) -> None:
        err = ActionError("validation failed", data={"field": "email"})
        assert err.data == {"field": "email"}

    def test_is_exception(self) -> None:
        with pytest.raises(ActionError, match="oops"):
            raise ActionError("oops")

    def test_str_representation(self) -> None:
        err = ActionError("bad request")
        assert "bad request" in str(err)

    def test_none_data_defaults_to_empty_dict(self) -> None:
        err = ActionError("no data", data=None)
        assert err.data == {}
