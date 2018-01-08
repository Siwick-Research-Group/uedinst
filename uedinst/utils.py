
from socket import inet_aton, error

def is_valid_IP(addr):
    """ Returns True if ``addr`` is a valid IPv4, False otherwise. """
    try:
        inet_aton(addr)
    except error:
        return False
    else:
        return True