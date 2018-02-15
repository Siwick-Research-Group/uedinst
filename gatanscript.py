
import sys
from os.path import join, isdir
from os import mkdir

from random import sample
from npstreams import linspace
import numpy as np
from tqdm import trange
from tifffile import imsave

from uedinst import ILS250PP, GatanUltrascan895, SC10Shutter
from faraday import FaradayClient

# TIME_POINTS         = np.concatenate((np.arange(-10, -2, step = 1), 
#                                       np.arange(-2, 15, step = 0.25), 
#                                       np.arange(15, 50, step = 1),
#                                       np.arange(50, 325, step = 25)), axis = 0).tolist()
TIME_POINTS         = list(linspace(-100, 100, num = 100, endpoint = False))
EXPERIMENT_TAG      = 'testchromium'
EXPOSURE            = 3
NSCANS              = 100
FOLDER              = join('D:\\Data\\GatanScripted', EXPERIMENT_TAG)

if __name__ == '__main__':

    if not isdir(FOLDER):
        mkdir(FOLDER)

    with GatanUltrascan895() as camera:

        with FaradayClient() as instruments:
            instruments.connect_delay_stage(True)
            instruments.connect_probe_shutter(True)
            instruments.connect_pump_shutter(True)

            instruments.probe_shutter_operating_mode('gated')
            instruments.pump_shutter_operating_mode('gated')

            # Step 1 : acquire probe off picture
            instruments.probe_shutter_enable(False)
            instruments.pump_shutter_enable(True)

            fname = join(FOLDER, 'probe_off.tif')
            im = camera.acquire_image(EXPOSURE)
            imsave(fname, im)

            # Step 2 : loop over time-points and scans randomly
            instruments.probe_shutter_enable(True)
            instruments.pump_shutter_enable(True)
            for scan in trange(NSCANS):
            
                time_points = sample(TIME_POINTS, k = len(TIME_POINTS))
                for time in time_points:

                    time_folder = join(FOLDER, '{:.3f}'.format(time))
                    if not isdir(time_folder):
                        mkdir(time_folder)
                    
                    instruments.delay_abs_time(time)

                    fname = join(time_folder, 'pumpon_{:.3f}ps_{}.tif'.format(time, scan))
                    im = camera.acquire_image(EXPOSURE)
                    imsave(fname, im)
            
            instruments.pump_shutter_enable(False)
            instruments.probe_shutter_enable(False)