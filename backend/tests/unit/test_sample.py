"""Sample unit test to verify pytest configuration."""

import pytest


def test_sample_unit():
    """Sample unit test to verify pytest is working."""
    assert True


def test_sample_with_fixture(test_config):
    """Test using configuration fixture."""
    assert test_config["testing"] is True


@pytest.mark.unit
def test_marked_unit():
    """Unit test with explicit marker."""
    assert 1 + 1 == 2


@pytest.mark.integration
def test_marked_integration():
    """Integration test with explicit marker."""
    assert True


@pytest.mark.slow
def test_slow_operation():
    """Test marked as slow."""
    # Simulate slow operation
    import time
    time.sleep(0.1)
    assert True