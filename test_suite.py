"""Rangeland Production test suite."""
import tempfile
import shutil
import unittest
import os

CENTURY_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'Century46_PC_Jan-2014')
SAMPLE_INPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', 'rangeland_production_sample_inputs')


class RangelandProductionTests(unittest.TestCase):
    """Regression tests for Rangeland Production scripts."""

    def setUp(self):
        """Initialize SDRRegression tests."""
        self.workspace_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up remaining files."""
        shutil.rmtree(self.workspace_dir)

    def test_base_regression(self):
        """Rangeland production Forage Example Regression test."""
        if not os.path.exists(CENTURY_DIR):
            self.fail(
                "Century binary directory not found at %s" % CENTURY_DIR)

        if not os.path.exists(SAMPLE_INPUT_DIR):
            self.fail(
                "Sample input directory not found at %s" % SAMPLE_INPUT_DIR)

        import forage
        forage_args = {
            'prop_legume': 0.0,
            'steepness': 1.,
            'DOY': 1,
            'start_year': 2014,
            'start_month': 1,
            'num_months': 24,
            'mgmt_threshold': 0.1,
            'century_dir': CENTURY_DIR,
            'template_level': 'GH',
            'fix_file': 'drytrpfi.100',
            'user_define_protein': 0,
            'user_define_digestibility': 0,
            'supp_csv': os.path.join(SAMPLE_INPUT_DIR,
                                     "Rubanza_et_al_2005_supp.csv"),
            'input_dir': SAMPLE_INPUT_DIR,
            'herbivore_csv': os.path.join(SAMPLE_INPUT_DIR,
                                          "herd_avg_uncalibrated.csv"),
            'restart_monthly': 1,
            'grass_csv': os.path.join(SAMPLE_INPUT_DIR, "0.csv"),
            'latitude': 0.13167,
            'outdir': self.workspace_dir,
        }

        forage.execute(forage_args)
