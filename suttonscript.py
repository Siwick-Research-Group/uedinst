
from os.path import join

from tqdm import trange

from uedinst import Merlin, SC10Shutter

EXPERIMENT_TAG      = 'beam-only-stack-vs-int-2'
EXPOSURE            = 400e-6        # 400 microseconds per shot
NRUNS               = 100
FOLDER              = join('D:\\Data', EXPERIMENT_TAG)

if __name__ == '__main__':

    with Merlin() as merlin:
        merlin.set_folder(FOLDER)
        merlin.set_continuous_mode(False)

        with SC10Shutter('COM11') as probe_shutter:
            probe_shutter.set_operating_mode(probe_shutter.OperatingModes.manual)
            probe_shutter.enable(True)

            with SC10Shutter('COM13') as pump_shutter:
                pump_shutter.set_operating_mode(pump_shutter.OperatingModes.manual)
                pump_shutter.enable(False)

                # Step 1 : electron beam only for 100 000 sequential shots
                #          and 1000 probe off shots
                merlin.set_bit_depth(6)
                merlin.set_folder(join(FOLDER, 'single-shots'))

                # Take 1000 probe off shots
                probe_shutter.enable(False)
                merlin.set_num_frames(1000)
                merlin.set_filename('probe_off.mib')
                merlin.start_acquisition(EXPOSURE, period = 1e-3)

                # Take 100 000 probe on shots
                merlin.set_num_frames(100000)
                probe_shutter.enable(True)
                merlin.set_filename('single_shot.mib')
                merlin.set_frames_per_trigger(1)
                merlin.start_acquisition(EXPOSURE, period = 1e-3)

                # Step 2 : electron beam for 3 seconds stacking vs integrating
                #          many times
                for index in trange(NRUNS):
                    merlin.set_folder(join(FOLDER, 'comparison-{}'.format(index)))

                    # Acquire single-shot probe-off picture
                    merlin.set_bit_depth(6)
                    merlin.set_filename('probe_off.mib')
                    probe_shutter.enable(False)
                    merlin.set_num_frames(1)
                    merlin.start_acquisition(EXPOSURE, period = 1e-3)

                    # acquire manu single-shot probe-on pictures
                    merlin.set_bit_depth(6)
                    merlin.set_filename('single_shot.mib')
                    probe_shutter.enable(True)
                    merlin.set_num_frames(3000)
                    merlin.start_acquisition(EXPOSURE, period = 1e-3)

                    # Integrate the equivalent number of time
                    merlin.set_bit_depth(24)
                    merlin.set_filename('integrated.mib')
                    merlin.set_num_frames(1)
                    merlin.start_acquisition(3, period = 4)
                
            probe_shutter.enable(False)