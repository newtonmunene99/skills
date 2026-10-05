import pytest

from orders.commands import handle_command


@pytest.mark.parametrize(
    ("name", "payload", "action"),
    [
        ("cancel", {"order_id": "o1"}, "cancel"),
        ("deliver", {"order_id": "o1"}, "deliver"),
        ("release", {"order_id": "o1"}, "release"),
    ],
)
def test_handle_command(name, payload, action):
    assert handle_command(name, payload)["action"] == action


def test_unknown_command():
    with pytest.raises(ValueError):
        handle_command("teleport", {})
