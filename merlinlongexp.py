
import sys
from os.path import join

from random import sample
from npstreams import linspace
import numpy as np
from tqdm import trange

from uedinst import ILS250PP, Merlin, SC10Shutter
from faraday import FaradayClient

# TIME_POINTS         = np.concatenate((np.arange(-10, -2, step = 1), 
#                                       np.arange(-2, 15, step = 0.25), 
#                                       np.arange(15, 50, step = 1),
#                                       np.arange(50, 325, step = 25)), axis = 0).tolist()
TIME_POINTS         = list(linspace(-100, 100, num = 100, endpoint = False))
EXPERIMENT_TAG      = 'graphite-again-25mj'
EXPOSURE            = 3
NSCANS              = 100
FOLDER              = join('D:\\Data', EXPERIMENT_TAG)

if __name__ == '__main__':

    with Merlin() as merlin:
        merlin.set_folder(FOLDER)
        merlin.set_bit_depth(12)
        merlin.set_num_frames(1)
        merlin.set_frames_per_trigger(1)
        merlin.set_continuous_mode(False)

        with FaradayClient() as instruments:
            instruments.connect_delay_stage(True)
            instruments.connect_probe_shutter(True)
            instruments.connect_pump_shutter(True)

            # Step 1 : acquire probe off picture
            instruments.probe_shutter_enable(False)
            instruments.pump_shutter_enable(True)

            merlin.set_folder(join(FOLDER, 'probe_off'))
            merlin.set_filename('probe_off.mib')
            merlin.start_acquisition(EXPOSURE, period = EXPOSURE + 0.01)

            # Step 2 : loop over time-points and scans randomly
            instruments.probe_shutter_enable(True)
            instruments.pump_shutter_enable(True)
            for scan in trange(NSCANS):

                time_points = sample(TIME_POINTS, k = len(TIME_POINTS))
                for time in time_points:
                    
                    instruments.delay_abs_time(time)

                    merlin.set_folder(join(FOLDER, '{:.3f}'.format(time)))
                    merlin.set_filename('pumpon_{:.3f}ps_{}.mib'.format(time, scan))

                    merlin.start_acquisition(EXPOSURE, period = EXPOSURE + 0.01)
            
            instruments.pump_shutter_enable(False)
            instruments.probe_shutter_enable(False)