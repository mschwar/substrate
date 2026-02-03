from substrate.status import StatusTransitionError, validate_status_transition


def test_status_transition_allowed():
    validate_status_transition("inbox", "canonical")
    validate_status_transition("canonical", "archived")


def test_status_transition_rejected():
    try:
        validate_status_transition("tombstoned", "canonical")
    except StatusTransitionError as exc:
        assert "illegal" in exc.message
    else:
        raise AssertionError("Expected StatusTransitionError")
