
from contextlib import AbstractContextManager, suppress
from enum import IntEnum, unique
from time import sleep

from scipy.constants import speed_of_light as c_vacuum
air_refractive_index = 1.0003
c_air = c_vacuum / air_refractive_index    # meters per second

from .base import InstrumentException
from .utils import is_valid_IP, timeout
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
    PositionOutsideTravelLimits             = -35
    SlaveErrorDisablingMaster               = -44
    InconsistentMechanicalZero              = -49
    MotorInitiError                         = -50
    BothEndRunsActivated                    = -113
    WarningErrorDuringMove                  = -120
    NotExpectedPositionAfterMotion          = -221

def _errcheck(returned):
    """
    This function checks that any error code is 0 (success)
    Otherwise, raise an InstrumentException with the correct
    error code. The ``returned`` value is either an error code
    or a list (in which case the error code is the first value) 
    """
    if returned is None:
        raise ValueError('None has been returned')
    with suppress(ValueError):  # unknown error code.
        if isinstance(returned, list):
            errcode = returned[0]
        else:
            errcode = returned
        error = XPSQ8Errors(int(errcode))
        if error != XPSQ8Errors.NoError:
            raise InstrumentException(error)
    return returned

class DelayStage(AbstractContextManager):
    """
    Abstract interface to one delay-stage
    connected to a Newport XPS Q8.

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

    # group and positioner must be overriden in subclasses
    group = ''
    positioner = group + ''

    def __init__(self, address, **kwargs):
        #self.socket_id = None

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

    def __exit__(self, *args, **kwargs):
        self.disconnect()
        super().__exit__(*args, **kwargs)
    
    @staticmethod
    def delay_to_distance(delay):
        """ Calculate the distance by which to move [mm] for light round-trip
        of ``delay`` picoseconds """
        # Distance to move is half because of back-and-forth motion
        # along the stage
        move_meters = (delay / 1e12) * (c_air / 2)
        return move_meters * 1e3

    def disconnect(self):
        """ Disconnect from the XPS """
        self._driver.TCP_CloseSocket(self.socket_id)
    
    def _wait_end_of_move(self, tout = 10, tol = 5e-3):
        """ 
        Wait for end of move, i.e. when the current position is close
        enough to the target.

        Parameters
        ----------
        tout : float, optional
            Time-out time in seconds
        tol : float, optional
            Position tolerance.
        """
        with timeout(tout, InstrumentException, exc_message = 'Movement timeout'):
            while abs(self.current_position() - self.target_position()) > tol:
                sleep(0.1)
    
    def target_position(self):
        """
        Get the current absolute position setpoint

        Returns
        -------
        pos : float
        """
        errcode, position = _errcheck(self._driver.GroupPositionTargetGet(self.socket_id, self.positioner, nbElement = 1))
        return float(position)

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
        Move the delay stage relatively to current position, by distance. This
        function returns when move is completed.
        
        Parameters
        ---------- 
        move : float
            Relative move [mm]
        """
        move = float(move)
        # For some reason, the targetDisplacement parameter
        # to GroupMoveRelative should be an iterable...
        _errcheck(self._driver.GroupMoveRelative(self.socket_id, self.positioner, [move]))
        return self._wait_end_of_move()
    
    def absolute_move(self, move):
        """
        Move the delay stage to a new absolute position, by distance. This
        function returns when move is completed.
        
        Parameters
        ---------- 
        move : float
            Absolute move [mm]
        """
        move = float(move)
        # For some reason, the targetDisplacement parameter
        # to GroupMoveAbsolute should be an iterable...
        _errcheck(self._driver.GroupMoveAbsolute(self.socket_id, self.positioner, [move]))
        return self._wait_end_of_move()

    def relative_time_shift(self, shift):
        """
        Move the delay stage to achieve a certain time-shift. This
        function returns when move is completed.

        Parameters
        ----------
        shift : float
            Time-shift in picoseconds
        """
        shift = float(shift)
        return self.relative_move(self.delay_to_distance(shift))

class ILS250PP(DelayStage):
    """
    Interface to an ILS250PP delay-stage connected
    to a Newport XPS Q8 positioner.
    """

    group = 'GROUP5'
    positioner = group + '.POSITIONER'

    def __init__(self, address = '192.168.254.254', **kwargs):
        super().__init__(address, **kwargs)
