import random
import unittest
from unittests.base_test import BaseTest
from maths_engine.isaac_rng import Isaac, mix


class IsaacTest(BaseTest, unittest.TestCase):

    def setUp(self):
        # Set up any state needed for the tests here
        self.seed_vector = [random.getrandbits(32) for _ in range(256)]
        self.isaac = Isaac(seed_vector=self.seed_vector)

    def test_initialization(self):
        # Test if the ISAAC object initializes correctly
        self.assertEqual(self.isaac.randcnt, 256)
        self.assertEqual(len(self.isaac.mm), 256)
        self.assertEqual(len(self.isaac.randrsl), 256)

    def test_rand_output_range(self):
        # Test if the random number generated is within the specified range
        result = self.isaac.rand(42)
        self.assertTrue(0 <= result < 42)

    def test_rand_reseeding(self):
        # Test if reseeding produces different outputs
        first_run = [self.isaac.rand(100) for _ in range(10)]
        self.isaac.__init__(seed_vector=self.seed_vector)  # Reseed
        second_run = [self.isaac.rand(100) for _ in range(10)]
        self.assertNotEqual(first_run, second_run)

    def test_mix_function(self):
        # Test the internal mix function (could be a mock test if mix is private)
        a, b, c, d, e, f, g, h = self.isaac.mm[:8]
        mixed_values = mix(a, b, c, d, e, f, g, h)
        self.assertEqual(len(mixed_values), 8)

    # complete other cases 

    def run_test(self):

        # do some testing
        try:
            self.setUp()
            self.test_initialization()
            self.test_rand_output_range()
            self.test_rand_reseeding()
            self.test_mix_function()
            # Add any other tests here...
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
        return {
            'success': True,
        }


def run_test():
    test = IsaacTest()
    return test.run_test()

