
import unittest
from contextlib import suppress
from random import random
from time import sleep

from .. import ILS250PP, InstrumentException

HAS_STAGE = False
with suppress(InstrumentException):
    ILS250PP()
    HAS_STAGE = True

def random_pos():
    """ Return a random position for the ILS250PP stage. """
    return round(random(), ndigits = 3)

@unittest.skipIf(not HAS_STAGE, 'ILS250PP delay stage not connected.')
class TestILS250PP(unittest.TestCase):
    
    def test_absolute_move(self):
        """ Test that moving the stage correctly updates its position """
        new_pos = random_pos()
        with ILS250PP() as delay_stage:
            delay_stage.absolute_move(new_pos)
            target = delay_stage.target_position()
            curr_pos = delay_stage.current_position()
        self.assertAlmostEqual(curr_pos, new_pos, places = 2)
    
    def test_relative_move(self):
        """ Test that moving the stage relatively is working correctly """
        start = random_pos()
        move = random_pos()
        with ILS250PP() as delay_stage:
            delay_stage.absolute_move(start)
            delay_stage.relative_move(move)
            curr_pos = delay_stage.current_position()
        
        self.assertAlmostEqual(curr_pos, start + move, places = 2)
    
    def test_relative_time_shift(self):
        """ Test that the relative_time_shift() method moves by an
        appropriate amount """
        # Expected distance for 30 ps
        # recall that the stage moving by x means that the
        # path length changes by 2x
        expected = -1*(30e-12) * 3e8 / 2 * 1e3 # ~ 4.5 mm
        
        with ILS250PP() as delay_stage:
            delay_stage.absolute_move(0.0)
            delay_stage.relative_time_shift(30)
            new_pos = delay_stage.current_position()
        
        self.assertAlmostEqual(new_pos, expected, places = 2)
    
    def test_absolute_time_shift(self):
        
        with ILS250PP() as delay_stage:

            with self.subTest('Absolute time -> time-zero'):
                delay_stage.absolute_move(20.0)
                delay_stage.absolute_time(0.0, tzero_position = 20.0)
                self.assertAlmostEqual(delay_stage.current_position(), 20.0, places = 2)
            
            with self.subTest('Testing movement direction'):
                # For ealier time-delay, stage should move further
                delay_stage.absolute_move(15)
                start_pos = delay_stage.current_position()
                delay_stage.absolute_time(-10, tzero_position = 15)
                stop_pos = delay_stage.current_position()
                self.assertTrue(start_pos < stop_pos)

    
    def test_static_methods(self):
        """ Test that the delay_to_distance() and distance_to_delay() methods are inverse of each other """
        dist = random_pos()

        delay = ILS250PP.distance_to_delay(dist)
        self.assertAlmostEqual(ILS250PP.delay_to_distance(delay), dist, places = 8)

if __name__ == '__main__':
    unittest.main()