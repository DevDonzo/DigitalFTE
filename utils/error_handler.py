"""Error Handler - Handle different error types gracefully"""
import logging

logger = logging.getLogger(__name__)

class TransientError(Exception):
    """Errors that can be retried"""
    pass

class AuthError(Exception):
    """Authentication errors - stop and alert"""
    pass

def handle_error(error: Exception, action: str) -> str:
    """Categorize and handle errors"""
    if isinstance(error, AuthError):
        logger.error(f'Auth error in {action}: {error}')
        return 'auth_error'
    elif isinstance(error, TransientError):
        logger.warning(f'Transient error in {action}: {error}')
        return 'transient_error'
    else:
        logger.error(f'Unknown error in {action}: {error}')
        return 'unknown_error'
