from backend.lifecycle import (
    _shutdown_callbacks,
    can_shutdown,
    register_shutdown_callback,
    request_shutdown,
)


def setup_function():
    _shutdown_callbacks.clear()


def test_can_shutdown_false_by_default():
    assert can_shutdown() is False


def test_register_and_can_shutdown():
    register_shutdown_callback(lambda: None)
    assert can_shutdown() is True


def test_request_shutdown_invokes_callbacks():
    called = []
    register_shutdown_callback(lambda: called.append(1))
    register_shutdown_callback(lambda: called.append(2))
    request_shutdown()
    assert called == [1, 2]
