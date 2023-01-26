# -*- coding: utf-8 -*-
__author__ = "Laurent P. René de Cotret"
__email__ = "laurent.renedecotret@mail.mcgill.ca"
__license__ = "Proprietary"
__version__ = "1.3.3"


class InstrumentException(Exception):
    """ Base exception for instrument-related errors. """

    pass


class InstrumentWarning(UserWarning):
    """ Base warning for instrument-related warnings. """

    pass


import os
from .base import TCPBase, GPIBBase, SerialBase, RS485Base, MetaInstrument, Singleton
from .attenuator import VariableAttenuator
from .daq import PCI6281
from .delay_stage import ILS250PP
from .electrometer import Keithley6514
from .freq_counter import RacalDana1991, TTiTF930
from .gatan import GatanUltrascan895, GatanUltrascan895WithElectrometer
from .multimeter import TekDMM4040
from .merlin import Merlin
from .powermeter import TekPSM4120
from .pressure import KLSeries979
from .psupply import HeinzingerPNChp
from .shutter import SC10Shutter
from .tempcontroller import ITC503
from .utils import is_valid_IP, timeout
from .circulator import PolySciCirc


def get_base_path():
    """
    returns package base dir
    """
    return os.path.dirname(__file__)
