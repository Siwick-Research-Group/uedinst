
from collections.abc import Container
from contextlib import AbstractContextManager, suppress
from enum import IntEnum, unique

from scipy.constants import speed_of_light as c_vacuum
air_refractive_index = 1.0003
c_air = c_vacuum / air_refractive_index    # meters per second

from . import InstrumentException, Singleton, is_valid_IP
from .XPS_Q8_drivers import XPS

@unique
class XPSQ8Errors(IntEnum):
    """
    Enumeration of possible XPS-Q8 errors.
    """
    # TODO: Error code and error description
    #       See example: 
    #       https://docs.python.org/3/library/enum.html#planet

    NoError                                 =  0
    SocketConnectionError                   = -1
    WrongObjectTypeForCmd                   = -8
    ParameterOutOfRangeOrIncorrect          = -17
    PositionerNameDoesNotExistOrUnknownCmd  = -18
    GroupNameDoesNotExistOrUnknownCmd       = -19
    NotAllowedAction                        = -22
    FollowingError                          = -25
    EmergencySignal                         = -26
    MoveAborted                             = -27
    HomeSearchTimeout                       = -28
    MotionDoneTimeout                       = -33
    PositionOutsideLimits                   = -35
    SlaveErrorDisablingMaster               = -44
    InconsistentMechanicalZero              = -49
    MotorInitiError                         = -50
    BothEndRunsActivated                    = -113
    WarningErrorDuringMove                  = -120
    NotExpectedPositionAfterMotion          = -221

def _errcheck(returned):
    with suppress(ValueError):  # unknown error code.
        if isinstance(returned, Container):
            errcode = returned[0]
        else:
            errcode = returned
        error = XPSQ8Errors(int(errcode))
        if error != XPSQ8Errors.NoError:
            raise InstrumentException(error)
    return returned

class DelayStage(AbstractContextManager, metaclass = Singleton):
    """
    Interface to Newport XPS Q8
    Parameters
    ----------
    address : str, optional
        IP address of the XPS, e.g. '192.168.33.101'.

    Raises
    ------
    ValueError : if ``address`` is an invalid IPv4 address.
    InstrumentException : if any connection error occurs.
    """
    _driver = XPS()

    group = 'GROUP5'
    positioner = group + '.POSITIONER'

    def __init__(self, address = '192.168.254.254', **kwargs):
        # According to TCP_ConnectToServer documentation,
        # port is always 5001
        if not is_valid_IP(address):
            raise ValueError('{} is an invalid IPv4 address'.format(address))
            
        self.socket_id = _errcheck(
            self._driver.TCP_ConnectToServer(IP = address, port = 5001, timeOut = 10))
        
        # Reset state by killing the group, and initializing again
        # Note: GroupKill returns [errcode, string] for some reason
        # even though documentation doesn't say that
        _errcheck(self._driver.KillAll(self.socket_id))
        _errcheck(self._driver.GroupInitialize(self.socket_id, self.group))
        _errcheck(self._driver.GroupHomeSearch(self.socket_id, self.group))

        # Get position limits
        errcode, self.min_limit, self.max_limit = _errcheck(self._driver.PositionerUserTravelLimitsGet(self.socket_id, self.positioner))

    def disconnect(self):
        """ Disconnect from the XPS """
        with suppress(AttributeError):  # e.g. self.socket_id doesn't exist
            self._driver.TCP_CloseSocket(self.socket_id)

    def __exit__(self, *args, **kwargs):
        self.disconnect()
        super().__exit__(*args, **kwargs)

    def current_position(self):
        """
        Get current absolute position
        
        Returns
        -------
        pos : float
        """
        errcode, position = _errcheck(self._driver.GroupPositionCurrentGet(self.socket_id, self.positioner, nbElement = 1))
        return float(position)
    
    def relative_move(self, move):
        """ 
        Move the delay stage relatively to current position, by distance.
        
        Parameters
        ---------- 
        move : float
        """
        move = str(float(move))
        return _errcheck(self._driver.GroupMoveRelative(self.socket_id, self.positioner, move))
    
    def absolute_move(self, move):
        """
        Move the delay stage to a new absolute position, by distance.
        
        Parameters
        ---------- 
        move : float
        """
        move = str(float(move))
        return _errcheck(self._driver.GroupMoveAbsolute(self.socket_id, self.positioner, move))

    def relative_time_shift(self, shift):
        """
        Move the delay stage to achieve a certain time-shift.

        Parameters
        ----------
        shift : float
            Time-shift in picoseconds
        """
        # Distance to move is half because of back-and-forth motion
        # along the stage
        # TODO: units of move, meters or microns?
        move_meters = shift * c_air / 2
        return self.relative_move(move_meters)