# -*- coding: utf-8 -*-
__author__ = 'Laurent P. René de Cotret'
__email__ = 'laurent.renedecotret@mail.mcgill.ca'
__license__ = 'BSD'
__version__ = '1.0.0'

class InstrumentException(Exception):
	""" Base exception for instrument-related errors. """
	pass

class InstrumentWarning(UserWarning):
	""" Base warning for instrument-related warnings. """
	pass

from .base 			import (TCPBase, GPIBBase, SerialBase, RS485Base, 
							MetaInstrument, Singleton)
from .delay_stage 	import ILS250PP
from .electrometer 	import Keithley6514
from .freq_counter 	import RacalDana1991
from .gatan 		import GatanUltrascan895
from .merlin 		import Merlin
from .powermeter 	import TekPSM4120
from .pressure 		import KLSeries979
from .psupply 		import HeinzingerPNChp
from .shutter 		import SC10Shutter
from .temperature   import ITC503
from .utils 		import is_valid_IP, timeout