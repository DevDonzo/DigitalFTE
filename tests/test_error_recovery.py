"""Unit tests for error recovery"""
import pytest

def test_retry_decorator():
    """Test retry decorator"""
    from utils.retry_handler import with_retry
    
    attempts = []
    
    @with_retry(max_attempts=3, base_delay=0.01)
    def failing_then_success():
        attempts.append(1)
        if len(attempts) < 3:
            raise Exception("Transient error")
        return "success"
    
    result = failing_then_success()
    assert result == "success"
    assert len(attempts) == 3
