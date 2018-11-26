"""Example script to launch the Rangeland Production model with sample inputs.

This script launches the InVEST beta Rangeland Production model assuming that
the locations of model inputs are supplied via command line arguments.
Author: Ginger Kowal 11.26.18
"""

import os
import sys
import forage


def run_sample_inputs(sample_input_dir, century_dir, outdir):
    """Launch the Rangeland Production model.

    Run the Rangeland Production model with sample inputs. Outputs are created
    inside the outdir folder.

    Parameters:
        sample_input_dir (string): path to directory containing sample inputs
        century_dir (string): path to directory containing Century executable
            and fix file
        outdir (string): path to directory where results should be stored

    Returns:
        None

    """
    forage_args = {
        'prop_legume': 0.0,
        'steepness': 1.,
        'DOY': 1,
        'start_year': 2014,
        'start_month': 1,
        'num_months': 12,
        'mgmt_threshold': 300,
        'century_dir': century_dir,
        'template_level': 'GL',
        'fix_file': 'drytrpfi.100',
        'user_define_protein': 0,
        'user_define_digestibility': 0,
        'supp_csv': os.path.join(sample_input_dir,
                                 "Rubanza_et_al_2005_supp.csv"),
        'input_dir': sample_input_dir,
        'herbivore_csv': os.path.join(sample_input_dir,
                                      "Ol_pej_herd.csv"),
        'grass_csv': os.path.join(sample_input_dir, "0.csv"),
        'latitude': 0.13167,
        'outdir': outdir,
        }

    forage.execute(forage_args)


if __name__ == "__main__":
    # path to sample input folder
    sample_input_dir = sys.argv[1]

    # path to directory containing century executable and files
    century_dir = sys.argv[2]

    # path to directory to store results (ok if it doesn't exist)
    outdir = sys.argv[3]

    run_sample_inputs(sample_input_dir, century_dir, outdir)
