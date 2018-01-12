from . import SerialBase

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

	_valid_baud_rates = {9600, 115200}
	_trigger_modes = {'internal':0, 'external':1}
	_op_modes = {'manual':1, 'auto':2, 'single':3, 'repeat':4, 'gated':5}

	@property
	def enabled(self):
		""" True if shutter is enabled, False otherwise. """
		return bool(int(self.query('ens?')))

	@property
	def shutter_open(self):
		""" True if shutter is open, False otherwise """
		return not self.shutter_closed

	@property
	def shutter_open_time(self):
		""" Shutter open time in milliseconds """
		return int(self.query('open?'))

	@property
	def repeat_count(self):
		""" Repeat count of operating mode 'repeat' """
		return int(self.query('rep?'))

	@property
	def trigger_mode(self):
		""" Trigger mode; either 'internal' or 'external' """
		is_external = bool(int(self.query('trig?')))
		if is_external: return 'external'
		else: return 'internal'

	@property
	def operating_mode(self):
		""" Operating mode. One of {'manual', 'auto', 'single',
		'repeat', 'gated'} """
		modes = {1:'manual', 2:'auto', 3:'single', 4:'repeat', 5:'gated'}
		int_mode = int(self.query('mode?'))
		return modes[int_mode]

	@property
	def shutter_closed(self):
		""" True if shutter is closed, False otherwise """
		return bool(int(self.query('closed?')))

	@property
	def baud_rate(self):
		""" Baud rate of the device """
		baud_rate_code = int(self.query('baud?'))
		return self._valid_baud_rates[baud_rate_code]

	@property
	def identity(self):
		return self.query('id?')

	def write(self, data, **kwargs):
		"""
		Write strings to SC10 shutter. Strings are automatically
		encoded and a carriage return is also added.

		Parameters
		----------
		data : str
			Data to be sent. If data does not end in carriage return ('\r'),
			a carriage return is added. Strings are encoded in ASCII automatically.

		Returns
		-------
		sent : int
			Number of bytes successfully written.

		Raises
		------
		InstrumentException : incomplete write
		"""
		if not data.endswith('\r'):
			data += '\r'
		return super().write(data, **kwargs)

	def query(self, data, **kwargs):
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
		sent = self.write(data, **kwargs)
		bytes_answer = self.readall()
		raw = bytes_answer.decode('ascii')

		# Answer *might* have added \r, '>', or the command itself
		for char in ('\r', '>', data):
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
			self.query('ens')

	def set_trigger_mode(self, mode):
		"""
		Change trigger mode. Depending on the operating mdoe, this function may have no
		immediate effect.

		Parameters
		----------
		mode : str, {'internal', 'external'}
			Trigger mode

		Raises
		------
		ValueError: if trigger mode has an invalid value.
		"""
		# Using query instead of write
		# because SC10 sends back its command
		try:
			int_mode = self._trigger_modes[mode]
		except KeyError:
			raise ValueError('Trigger mode must be one of {}, not {}'.format(list(self._trigger_modes.keys()), mode))
		self.query('trig={}'.format(int_mode))

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
			int_mode = self._op_modes[mode]
		except KeyError:
			raise ValueError('Operating mode must be one of {}, not {}'.format(list(self._op_modes.keys()), mode))
		self.query('mode={}'.format(int_mode))

	def set_open_time(self, ms):
		"""
		Set shutter open time

		Parameters
		----------
		ms : int
			Open time in millisecond
		"""
		self.query('open={}'.format(int(ms)))

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
			raise ValueError('Repeat count must be between 1 and 99 inclusively.')
		self.query('rep={}'.format(count))