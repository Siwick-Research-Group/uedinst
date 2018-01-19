# -*- coding: utf-8 -*-
__author__ = 'Laurent P. René de Cotret'
__email__ = 'laurent.renedecotret@mail.mcgill.ca'
__license__ = 'BSD'
__version__ = '0.0.1'

class InstrumentException(Exception):
	""" Base exception for instrument-related errors. """
	pass

from .base import GPIBBase, SerialBase, RS485Base, MetaInstrument, Singleton
from .delay_stage import ILS250PP
from .electrometer import Keithley6514
from .merlin import Merlin
from .powermeter import TekPSM4120
from .pressure import KLSeries979
from .psupply import HeinzingerPNChp
from .shutter import SC10Shutter
from .utils import is_valid_IP, timeout