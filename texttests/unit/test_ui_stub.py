from substrate.ui_stub import launch_ui_stub


def test_ui_stub_returns_status():
    status = launch_ui_stub()
    assert status.mode == "stub"
    assert "UI" in status.message
