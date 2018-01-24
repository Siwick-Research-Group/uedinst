
import sys
from os.path import join

from npstreams import linspace
from tqdm import tqdm

from uedinst import ILS250PP, Merlin, SC10Shutter

TIME_POINTS         = list(linspace(-50, 25, 20))
EXPERIMENT_TAG      = 'tzero-hunt-coppergrid-4'
EXPOSURE            = 400e-6        # 400 microseconds per shot
NSCANS              = 500
FOLDER              = join('D:\\Data', EXPERIMENT_TAG)
TIME_ZERO_POSITION  = -68.1823

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
        merlin.set_num_frames(NSCANS)
        merlin.set_frames_per_trigger(1)
        merlin.set_continuous_mode(False)

        with SC10Shutter('COM11') as probe_shutter:
            
            probe_shutter.set_operating_mode(probe_shutter.OperatingModes.manual)
            probe_shutter.enable(False)

            with SC10Shutter('COM13') as pump_shutter:
                pump_shutter.set_operating_mode(pump_shutter.OperatingModes.manual)
                
                # Start with 'laser' background, i.e. probe off and pump on
                pump_shutter.enable(True)
                merlin.set_folder(join(FOLDER, 'probe_off'))
                merlin.set_filename('probe_off.mib')
                merlin.start_acquisition(EXPOSURE, period = 1e-3)

                probe_shutter.enable(True)

                with ILS250PP() as delay_stage:
                    delay_stage.absolute_move(TIME_ZERO_POSITION)

                    for time_delta, time in tqdm(zip(diff(TIME_POINTS), TIME_POINTS), total = len(TIME_POINTS)):

                        # Save all time-points pictures in a new folder
                        new_folder = join(FOLDER, '{:.3f}'.format(time))
                        merlin.set_folder(join(FOLDER, '{:.3f}'.format(time)))

                        delay_stage.relative_time_shift(time_delta)
                        pump_shutter.enable(True)

                        merlin.set_filename('pumpon_{:.3f}ps_.mib'.format(time))
                        merlin.start_acquisition(EXPOSURE, period = 1e-3)

                        # No need for pumpoff pictures
                        # pump_shutter.enable(False)

                        # merlin.set_filename('pumpoff_{:.3f}ps_.mib'.format(time))
                        # merlin.start_acquisition(EXPOSURE, period = 1e-3)
