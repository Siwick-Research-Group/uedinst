
from contextlib import contextmanager
from threading import Timer, Event
from _thread import interrupt_main  # lower-level module than ``threading``
from socket import inet_aton, error

def is_valid_IP(addr):
    """ Returns True if ``addr`` is a valid IPv4, False otherwise. """
    try:
        inet_aton(addr)
    except error:
        return False
    else:
        return True

@contextmanager
def timeout(seconds, exception, exc_message = ''):
    """
    Context manager that raises an exception if a timeout
    expires.

    Parameters
    ----------
    seconds : float
        Time-out maximum.
    exception : Exception
        Exception to be raised in the case of expired timeout.
    exc_message : str, optional
        Optional message inserted in ``exception``
    
    Raises
    ------
    ValueError : if ``seconds`` is negative, or ``exc_message`` is invalid

    .. warning::

        This context manager is *NOT* re-entrant; it cannot be chained
        with other ``timeout`` contexts.

        Pausing the main thread (e.g. using :code:`time.sleep()`)
        will block this context manager.
    """
    if seconds < 0:
        raise ValueError('Invalid timeout: {}'.format(seconds))
    
    if not isinstance(exc_message, str):
        raise ValueError('Invalid error message: '.format(type(exc_message)))
    
    timer = Timer(seconds, lambda: interrupt_main())
    timer.start()
    try:
        yield
    except KeyboardInterrupt:
        raise exception(exc_message)
    finally:
        timer.cancel()