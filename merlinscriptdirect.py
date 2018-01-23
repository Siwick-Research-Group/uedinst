
import sys
from datetime import datetime
from os.path import basename, join
from time import sleep
import sys
from tqdm import tqdm

from uedinst import ILS250PP, Merlin, SC10Shutter

TIME_POINTS         = [-50, -25, 0, 25, 50, 100]
EXPERIMENT_TAG      = 'test'
FOLDER              = join('D:\\Data', EXPERIMENT_TAG)
TIME_ZERO_POSITION  = -32.0189

def diff(iterable):
    """ 
    Yields the cumulative difference, e.g.:
    >>> list(diff([-5, -4, -3, -2, -1]))
    [-5, 1, 1, 1, 1]
    """
    iterable = iter(iterable)
    prev = next(iterable)
    yield prev
    for item in iterable:
        difference = item - prev
        prev = item
        yield difference

if __name__ == '__main__':


    with Merlin() as merlin:
        merlin.set_folder(FOLDER)
        merlin.set_bit_depth(6)
        merlin.set_num_frames(100)
        merlin.set_continuous_mode(True)

        acquisition_period = 3 # merlin.acquisition_period


        with SC10Shutter('COM11') as probe_shutter:
            
            probe_shutter.set_operating_mode(probe_shutter.OperatingModes.manual)
            probe_shutter.enable(False)

            merlin.set_filename('probe_off.mib')
            merlin.start_acquisition()
            sleep(acquisition_period + 0.5)

            probe_shutter.enable(True)

        with SC10Shutter('COM13') as pump_shutter:
            pump_shutter.set_operating_mode(pump_shutter.OperatingModes.manual)
            pump_shutter.enable(False)

            with ILS250PP() as delay_stage:
                delay_stage.absolute_move(TIME_ZERO_POSITION)

                for time_delta, time in tqdm(zip(diff(TIME_POINTS), TIME_POINTS), total = len(TIME_POINTS)):

                    delay_stage.relative_time_shift(time_delta)
                    pump_shutter.enable(True)

                    merlin.set_filename('pumpon_{:.3f}ps.mib'.format(time))
                    merlin.start_acquisition()
                    sleep(acquisition_period + 0.5)

                    pump_shutter.enable(False)

                    merlin.set_filename('pumpoff_{:.3f}ps.mib'.format(time))
                    merlin.start_acquisition()
                    sleep(acquisition_period + 0.5)
