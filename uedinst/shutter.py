
from .base import SerialBase
from .utils import timeout
from enum import IntEnum

# TODO: modes as enum



class SC10Shutter(SerialBase):
	"""
	Interface to Thorlabs SC10 shutters.

	Parameters
	----------
	port : str
			Device name (e.g. 'COM1')
	kwargs
		Keyword-arguments are passed to serial.Serial class.
	"""

	class TriggerModes(IntEnum):
		internal = 0
		external = 1

	class OperatingModes(IntEnum):
		manual 	= 1
		auto 	= 2
		single  = 3
		repeat  = 4
		gated   = 5
	
	def __init__(self, port, **kwargs):
		kwargs.update({'port':     port,
					   'baudrate': 9600, 
					   'timeout':  1.0})
		super().__init__(**kwargs)
		# Clear buffer which might not be empty due to errors
		self.reset_input_buffer()
		self.reset_output_buffer()

	@property
	def enabled(self):
		""" True if shutter is enabled, False otherwise. """
		return bool(int(self.query_str('ens?')))

	@property
	def shutter_open(self):
		""" True if shutter is open, False otherwise """
		return not self.shutter_closed

	@property
	def shutter_open_time(self):
		""" Shutter open time in milliseconds """
		return int(self.query_str('open?'))

	@property
	def repeat_count(self):
		""" Repeat count of operating mode 'repeat' """
		return int(self.query_str('rep?'))

	@property
	def trigger_mode(self):
		""" Trigger mode; either 'internal' or 'external' """
		return self.TriggerModes(int(self.query_str('trig?')))

	@property
	def operating_mode(self):
		""" Operating mode. One of {'manual', 'auto', 'single',
		'repeat', 'gated'} """
		return self.OperatingModes(int(self.query_str('mode?')))

	@property
	def shutter_closed(self):
		""" True if shutter is closed, False otherwise """
		return bool(int(self.query_str('closed?')))

	@property
	def identity(self):
		return self.query_str('id?')
	
	def query_str(self, data, **kwargs):
		"""
		Write and read the response. Carriage returns and '>' symbols
		are removed from the response.

		Parameters
		----------
		data : str
			Data to be sent. If data does not end in carriage return ('\r'),
			a carriage return is added.

		Returns
		-------
		response : str
			Query response with carriage returns and '>' symbols removed.
		"""
		if not data.endswith('\r'):
			data += '\r'
		sent = self.write_str(data, **kwargs)
		bytes_answer = self.readall()
		raw = bytes_answer.decode('ascii')

		# Answer *might* have added \r, '>', or the command itself
		# data.strip() is data without the '\r' at the end
		for char in ('\r', '>', data.strip()):
			raw = raw.replace(char, '')
		return raw

	def enable(self, en):
		"""
		Enable/disable shutter.

		Parameters
		----------
		en : bool
			Enable flag. If False, the shutter will be disabled;
			if True, the shutter will be enabled.
		"""
		# Unfortunately there is no way to directly enable
		# or disable the shutter. Only a toggle is made available.
		# Therefore, we check the current status first.
		current = self.enabled
		if current != en:
			# Since the SC10 shutters returns the command,
			# we query for 'ens', not only write.
			self.query_str('ens')

	def set_trigger_mode(self, mode):
		"""
		Change trigger mode. Depending on the operating mdoe, this function may have no
		immediate effect.

		Parameters
		----------
		mode : str, {'internal', 'external'} or TriggerModes member
			Trigger mode

		Raises
		------
		ValueError: if trigger mode has an invalid value.
		"""
		# Using query instead of write
		# because SC10 sends back its command
		try:
			int_mode = int(mode)
		except ValueError:	#
			int_mode = getattr(self.TriggerModes, mode)
		except AttributeError:
			raise ValueError('Trigger mode must be one of {}, not {}'.format(list(self.TriggerModes), mode))
		self.query_str('trig={}'.format(int_mode))

	def set_operating_mode(self, mode):
		"""
		Set operating mode.

		Parameters
		----------
		mode : str, {'manual', 'auto', 'single', 'repeat', 'gated'}
			Operating mode.

		Raises
		------
		ValueError : if ``mode`` has invalid value.
		"""
		# Using query instead of write
		# because SC10 sends back its command
		try:
			int_mode = int(mode)
		except ValueError:	#
			int_mode = getattr(self.OperatingModes, mode)
		except AttributeError:
			raise ValueError('Operating mode must be one of {}, not {}'.format(list(self.OperatingModes), mode))
		self.query_str('mode={}'.format(int_mode))

	def set_open_time(self, ms):
		"""
		Set shutter open time

		Parameters
		----------
		ms : int
			Open time in millisecond
		"""
		self.query_str('open={}'.format(int(ms)))

	def set_repeat_count(self, count):
		"""
		Set repeat count in 'repeat' operating mode.

		Parameters
		----------
		count : int
			Repeat count between 1 and 99.

		Raises
		------
		ValueError : if ``count`` is not between 1 and 99 (inclusive)
		"""
		count = int(count)
		if count > 99 or count < 1:
			raise ValueError('Repeat count {} not in [1, 99] range'.format(count))
		self.query_str('rep={}'.format(count))