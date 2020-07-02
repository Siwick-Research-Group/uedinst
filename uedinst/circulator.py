from .base import SerialBase
import serial


class PolySciCirc(SerialBase):
    """
	Interface to Polyscience circulator.

	Parameters
	----------
	port : str
			Device name (e.g. 'COM1')
	kwargs
		Keyword-arguments are passed to serial.Serial class.
	"""

    BAUDRATES = (57600,)

    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            timeout=1,
            **kwargs,
        )

    def gettemp(self):
        """
        Reads temperature from the circulator

        Parameters
        ----------
        n/a
        """
        self.write_str("RS\r")
        value = self.read()
        print("VALUE: ", value)
        return float(value[0:6])

    def settemp(self, T):
        """
        Adjusts set point of circulator

        Parameters
        ----------
        T: float
            desired set point in format iii.ii with i = 1,2,...,9

        Raises
        ------
        ValueError: if T > 999.99
        """
        T = float(T)
        if T > 999.99:
            raise ValueError("New set point must be less than 1000.00 C")
        if T < 100:
            T = f"{T:0>6.2f}"
        else:
            T = f"{T:.2f}"
        self.write(f"SS{T}")
