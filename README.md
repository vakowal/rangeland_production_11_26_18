# Introduction #

The rangeland production model is a simulation that represents dynamic growth of grass and consumption of grass by herbivores to predict productivity in terms of herbivore diet sufficiency, or the predicted intake of protein and energy relative to maintenance requirements.  The model is built by coupling the Century ecosystem model (Parton et al. 1993) with a basic physiology submodel adapted from GRAZPLAN (Freer et al. 2012).  The rangeland production model functions as a handler that launches the Century executable, collects output from Century describing forage biomass and nutrient content, simulates diet selection and growth by herbivores, and formats the diet selected into inputs for Century before launching Century again.  This process is completed at each model time step.  Because the Century model is is protected by a United States copyright to Colorado State University, users of the rangeland production model must obtain their own copy from its developers.

### Running the rangeland production model ###
A folder of sample inputs is provided in the repository as a zip file ("rangeland_production_sample_inputs.zip").  Required user inputs to launch the model with these sample inputs are:

* sample_input_dir (filepath to directory containing sample inputs)
* century_dir (filepath to directory containing Century executable and supporting files)
* out_dir (filepath to directory where model outputs will be written)

An example script is also provided to allow users to launch the rangeland production model using these sample inputs ("run_forage_example.py").  To run the model with sample inputs, clone the entire repository and unzip the sample inputs.  Open a command window, navigate to the folder where you have placed the rangeland production repository, and type:

    $ Python run_forage_example.py <sample_input_dir> <century_dir> <out_dir>

Replace the bracketed inputs with the input filepaths described above.


### Getting Century ###
Users of the rangeland production model must install a copy of Century 4.6 on their machine.  Century can be obtained by writing to Century Support at century@colostate.edu and requesting a copy of the Century 4.6 executable, documentation, and example files.

Users should place the Century executable in a designated folder on their computer, and supply the filepath to this folder as the input “century_dir” (see "Running the rangeland production model", above).  That folder must also contain the following executables (distributed with Century): list100_46.exe, file100_46.exe, event100_46.exe; and the following files: graz.100, crop.100, outvars.txt, fire.100.  It is expected that all of these files should be distributed with the Century executable.

### Viewing results ###
After the model completes successfully, the following outputs can be located in the folder specified by the user as the “out_dir” filepath:

* Log file: a text file with all inputs supplied to the model.  The filename of this file includes the date and time that the model was launched; for example, the log file named forage-log-2017-01-31--12_06_45.txt gives all inputs to the model that was launched on 12:06 pm on January 31 2017.
* “summary_results.csv”: a csv file containing the main outputs of the model.  These consist of the following quantities, for each step that the model was run: 
    * Step: model step.  Step = -1 gives initial conditions following model spin-up
    * Year: year, for that step
    * Month: month of the year, for that step
    * <herbivore>_E_req: daily maintenance energy requirements for an individual of the specified herbivore type for the model step, including costs of pregnancy or lactation for breeding females
    * <herbivore>_P_req: daily maintenance protein requirements for an individual of the specified herbivore type for the model step, including costs of pregnancy or lactation for breeding females
    * <herbivore>_MEItotal: daily metabolizable energy intake for an individual of the specified herbivore type for the model step
    * <herbivore>_DPLS: daily digestible protein leaving the stomach, i.e. usable protein intake, for an individual of the specified herbivore type for the model step
    * <herbivore>_intake_forage_per_indiv_kg: kg of forage eaten by an individual herbivore during that time step
    * total_offtake: total biomass removed by herbivores during that time step, accounting for herbivore density (kg/ha)
    * <grass>_green_kgha: live biomass of the grass type <grass> prior to diet selection for that step, where <grass> is replaced by the label given for the grass type in the grass_csv input by the user (kg/ha)
    * <grass>_dead_kgha: standing dead biomass of the grass type <grass> prior to diet selection for that step
* Many files of the form “graz_<step>.100”: these are the grazing parameter definition files that were supplied to Century for each model step, and they can be examined in a text editor.
* Many files of the form “<grass>_<step>.sch”: these are the schedule files that were supplied to Century for each grass type, for each model step, and they can be examined in a text editor.
Century output folders: these folders contain all outputs of the Century model for a given Century model run, which constitutes a model step of the rangeland production model.  The Century output file with the “*.lis” file extension may be examined in a text editor.
* “CENTURY_outputs_spin_up”: this folder contains all outputs of the Century model for the spin-up period.
* Many folders of the form “CENTURY_outputs_m<month>_y<year>”: these folders contain all outputs of the Century model for the given month and year of the rangeland production model.

### References ###
Freer, M, A. D Moore, and J. R Donnelly. “The GRAZPLAN Animal Biology Model for Sheep and Cattle and the  GrazFeed Decision Support Tool.” Canberra, ACT Australia: CSIRO Plant Industry, 2012.

Parton, W. J., J. M. O. Scurlock, D. S. Ojima, T. G. Gilmanov, R. J. Scholes, D. S. Schimel, T. Kirchner, et al. “Observations and Modeling of Biomass and Soil Organic Matter Dynamics for the Grassland Biome Worldwide.” Global Biogeochemical Cycles 7, no. 4 (December 1, 1993): 785–809. doi:10.1029/93GB02042.