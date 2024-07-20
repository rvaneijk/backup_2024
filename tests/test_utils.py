import unittest
import time
from core.utils import timer

class TestTimer(unittest.TestCase):
    def test_timer_start(self):
        # Test that timer() returns a float when called without arguments
        start_time = timer()
        self.assertIsInstance(start_time, float)

    def test_timer_elapsed(self):
        # Test that timer() returns a formatted string when called with a start time
        start_time = time.time()
        time.sleep(1)  # Sleep for 1 second
        elapsed_time = timer(start_time)
        
        # Check that the elapsed time is a string in the format HH:MM:SS
        self.assertIsInstance(elapsed_time, str)
        self.assertRegex(elapsed_time, r'^\d{2}:\d{2}:\d{2}$')
        
        # Check that the elapsed time is at least 1 second
        hours, minutes, seconds = map(int, elapsed_time.split(':'))
        total_seconds = hours * 3600 + minutes * 60 + seconds
        self.assertGreaterEqual(total_seconds, 1)

if __name__ == '__main__':
    unittest.main()