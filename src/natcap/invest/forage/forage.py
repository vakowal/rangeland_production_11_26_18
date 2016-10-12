# Tier 2 rangeland production model
# Ginger Kowal for the Natural Capital Project

# forage production by CENTURY
# more info: www.nrel.colostate.edu/projects/century/
# Parton, W. J., J. M. O. Scurlock, D. S. Ojima, T. G. Gilmanov, R. J. Scholes,
# D. S. Schimel, T. Kirchner, et al. "Observations and Modeling of Biomass and
# Soil Organic Matter Dynamics for the Grassland Biome Worldwide." Global
# Biogeochemical Cycles 7, no. 4 (December 1, 1993): 785-809.
# doi:10.1029/93GB02042.

# livestock equations adapted from GRAZPLAN
# more info:
# Freer, M, A. D Moore, and J. R Donnelly. The GRAZPLAN Animal Biology Model
# for Sheep and Cattle and the GrazFeed Decision Support Tool. Canberra, ACT
# Australia: CSIRO Plant Industry, 2012.

import os
import sys
import shutil
import time
from datetime import datetime
import pandas

import forage_utils as forage
import forage_century_link_utils as cent
import freer_param as FreerParam

def execute(args):
    """This function invokes the forage model given user inputs.

        args - a python dictionary with the following required entries:
        args['latitude'] - site latitude in degrees.  If south of the equator,
            this should be negative
        args['prop_legume'] - proportion of the pasture by weight that is
            legume, ranging from 0:1
        args['steepness'] - site steepness, ranging from 1:2
        args['DOY'] - initial day of the year, an integer ranging from 1:365
        args['start_year'] - initial year, an integer
        args['start_month'] - initial month, an integer ranging from 1:12
            corresponding to January:December
        args['num_months'] - number of months to run the simulation
        args['grz_months'] - months when grazing should be applied, where month
            0 is the first month of the simulation
        args['density_series'] - stocking density by month, where month 0 is
            the first month of the simulation
        args['mgmt_threshold'] - management threshold, the percent of initial
            biomass that must remain (0:1)
        args['input_dir'] - local file directory containing inputs to run
            CENTURY
        args['century_dir'] - local file directory containing the executable
            and global parameter files to run the CENTURY ecosystem model
        args['outdir'] - local file directory where intermediate and output
            files will be saved
        args['template_level'] - template grazing level.  # TODO replace this
        args['fix_file'] - file basename of CENTURY fix file, which resides in
            the directory args['century_dir']
        args['user_define_protein'] - boolean (0: false, 1: true).  Should
            crude protein of forage be drawn from forage input supplied by the
            user?  If false, it is calculated from CENTURY outputs
        args['user_define_digestibility'] - boolean (0: false, 1: true). Should
            digestibility of forage be drawn from forage input supplied by the
            user?  If false, it is calculated from CENTURY outputs
        args['herbivore_csv'] - an absolute path to a csv file containing all
            necessary descriptors of each herbivore type
        args['grass_csv'] - an absolute path to a csv file containing all
            necessary descriptors of the grass available as forage
        args['supp_csv'] - an absolute path to a csv file containing all
            necessary descriptors of supplemental feed (optional)
        args['restart_yearly'] - re-initialize the animal herd every year?
            hack-y option for CGIAR Peru integration with SWAT.
        args['diet_verbose'] - save details of diet selection?

        returns nothing."""
    # TODO fill in optional arguments that are empty with 'na' so that we
    # don't get key errors when they are missing
    now_str = datetime.now().strftime("%Y-%m-%d--%H_%M_%S")
    if not os.path.exists(args['outdir']):
        os.makedirs(args['outdir'])
    intermediate_dir = os.path.join(args['outdir'],
                                    'CENTURY_outputs_spin_up')
    if not os.path.exists(intermediate_dir):
        os.makedirs(intermediate_dir)
    forage.write_inputs_log(args, now_str)
    forage.set_time_step('month')  # current default, enforced by CENTURY
    add_event = 1  # TODO should this ever be 0?
    steps_per_year = forage.find_steps_per_year()
    graz_file = os.path.join(args[u'century_dir'], 'graz.100')
    cent.set_century_directory(args[u'century_dir'])
    if args['diet_verbose']:
        master_diet_dict = {}
        diet_segregation_dict = {'step': [], 'segregation': []}
    herbivore_list = []
    if args[u'herbivore_csv'] is not None:
        herbivore_input = (pandas.read_csv(args[u'herbivore_csv'])).to_dict(
                           orient='records')
        for h_class in herbivore_input:
            herd = forage.HerbivoreClass(h_class)
            herd.update()
            BC = 1  # TODO get optional BC from user
            # if BC:
                # herd.check_BC(BC)
            
            herbivore_list.append(herd)

    grass_list = (pandas.read_csv(args[u'grass_csv'])).to_dict(
                                                              orient='records')
    forage.check_initial_biomass(grass_list)
    results_dict = {'step': [], 'year': [], 'month': []}
    for h_class in herbivore_list:
        results_dict[h_class.label + '_kg'] = []
        results_dict[h_class.label + '_gain_kg'] = []
        results_dict[h_class.label + '_intake_forage_per_indiv_kg'] = []
        if h_class.sex == 'lac_female':
            results_dict['milk_prod_kg'] = []
    for grass in grass_list:
        results_dict[grass['label'] + '_green_kgha'] = []
        results_dict[grass['label'] + '_dead_kgha'] = []
    results_dict['total_offtake'] = []
    schedule_list = []
    for grass in grass_list:
        schedule = os.path.join(args[u'input_dir'], (grass['label'] + '.sch'))
        if os.path.exists(schedule):
            schedule_list.append(schedule)
        else:
            er = "Error: schedule file not found"
            raise Exception(er)
        # write CENTURY batch file for spin-up simulation
        hist_bat = os.path.join(args[u'input_dir'], (grass['label'] +
                                '_hist.bat'))
        hist_schedule = grass['label'] + '_hist.sch'
        hist_output = grass['label'] + '_hist'
        cent.write_century_bat(args[u'input_dir'], hist_bat, hist_schedule,
                               hist_output, args[u'fix_file'],
                               'outvars.txt')
        # write CENTURY bat for extend simulation
        extend_bat = os.path.join(args[u'input_dir'],
                                  (grass['label'] + '.bat'))
        schedule = grass['label'] + '.sch'
        output = grass['label']
        extend = grass['label'] + '_hist'
        cent.write_century_bat(args[u'input_dir'], extend_bat, schedule,
                               output, args[u'fix_file'], 'outvars.txt',
                               extend)
    supp_available = 0
    if 'supp_csv' in args.keys():
        supp_list = (pandas.read_csv(args[u'supp_csv'])).to_dict(
            orient='records')
        assert len(supp_list) == 1, "Only one supplement type is allowed"
        supp_info = supp_list[0]
        supp = forage.Supplement(FreerParam.FreerParamCattle('indicus'),
                                 supp_info['digestibility'],
                                 supp_info['kg_per_day'], supp_info['M_per_d'],
                                 supp_info['ether_extract'],
                                 supp_info['crude_protein'],
                                 supp_info['rumen_degradability'])
        if supp.DMO > 0.:
            supp_available = 1

    # make a copy of the original graz params and schedule file
    shutil.copyfile(graz_file, os.path.join(args[u'century_dir'],
                    'graz_orig.100'))
    for schedule in schedule_list:
        label = os.path.basename(schedule)[:-4]
        copy_name = label + '_orig.sch'
        shutil.copyfile(schedule, os.path.join(args[u'input_dir'],
                        copy_name))
    file_list = []
    for grass in grass_list:
        move_outputs = [grass['label']+'_hist_log.txt',
                        grass['label']+'_hist.lis', grass['label']+'_log.txt',
                        grass['label']+'.lis', grass['label']+'.bin']
        
        # move CENTURY run files to CENTURY dir
        hist_bat = os.path.join(args[u'input_dir'], (grass['label'] +
                                '_hist.bat'))
        extend_bat = os.path.join(args[u'input_dir'],
                                  (grass['label'] + '.bat'))
        e_schedule = os.path.join(args[u'input_dir'], grass['label'] + '.sch')
        h_schedule = os.path.join(args[u'input_dir'],
                                  grass['label'] + '_hist.sch')
        site_file, weather_file = cent.get_site_weather_files(
                                                e_schedule, args[u'input_dir'])
        grass_files = [hist_bat, extend_bat, e_schedule, h_schedule,
                         site_file]
        for file_name in grass_files:
            file_list.append(file_name)
        if weather_file != 'NA':
            file_list.append(weather_file)
        for file_name in file_list:
            shutil.copyfile(file_name, os.path.join(args[u'century_dir'],
                                               os.path.basename(file_name)))
        # run CENTURY for spin-up for each grass type up to start_year and
        # start_month                                       
        hist_bat = os.path.join(args[u'century_dir'], (grass['label'] +
                                '_hist.bat'))
        century_bat = os.path.join(args[u'century_dir'], (grass['label'] +
                                   '.bat'))
        cent.launch_CENTURY_subprocess(hist_bat)
        cent.launch_CENTURY_subprocess(century_bat)
        
        # save copies of CENTURY outputs, but remove from CENTURY dir
        for file_name in move_outputs:
            shutil.move(os.path.join(args[u'century_dir'], file_name),
                            os.path.join(intermediate_dir, file_name))
            
    stocking_density_dict = forage.populate_sd_dict(herbivore_list)
    total_SD = forage.calc_total_stocking_density(herbivore_list)
    site = forage.SiteInfo(args[u'steepness'], args[u'latitude'])
    threshold_exceeded = 0
    
    # add starting conditions to summary file
    step = -1
    step_month = args[u'start_month'] + step
    if step_month == 0:
        month = 12
        year = args[u'start_year'] - 1
    else:
        month = step_month
        year = args[u'start_year']
    results_dict['step'].append(step)
    results_dict['year'].append(year)
    results_dict['month'].append(month)
    for herb_class in herbivore_list:
        results_dict[herb_class.label + '_kg'].append(herb_class.W)
        results_dict[herb_class.label + '_gain_kg'].append('NA')
        results_dict[herb_class.label +
                     '_intake_forage_per_indiv_kg'].append('NA')
        results_dict['total_offtake'].append('NA')
    try:
        for step in xrange(args[u'num_months']):
            step_month = args[u'start_month'] + step
            if step_month > 12:
                mod = step_month % 12
                if mod == 0:
                    month = 12
                    year = (step_month / 12) + args[u'start_year'] - 1
                else:
                    month = mod
                    year = (step_month / 12) + args[u'start_year']
            else:
                month = step_month
                year = (step / 12) + args[u'start_year']
            if args['restart_monthly']:
                threshold_exceeded = 0
            if month == 1 and args['restart_yearly'] and \
                                            args[u'herbivore_csv'] is not None:
                threshold_exceeded = 0
                herbivore_list = []
                for h_class in herbivore_input:
                    herd = forage.HerbivoreClass(h_class)
                    herd.update()
                    herbivore_list.append(herd)
            try:
                if args['restart_monthly']:
                    threshold_exceeded = 0
            except KeyError:
                continue
            # get biomass and crude protein for each grass type from CENTURY
            for grass in grass_list:
                output_file = os.path.join(intermediate_dir,
                                           grass['label'] + '.lis')
                outputs = cent.read_CENTURY_outputs(output_file,
                                                    year - 1,
                                                    year + 1)
                outputs.drop_duplicates(inplace=True)
                target_month = cent.find_prev_month(year, month)
                grass['prev_g_gm2'] = grass['green_gm2']
                grass['prev_d_gm2'] = grass['dead_gm2']
                try:
                    grass['green_gm2'] = outputs.loc[target_month, 'aglivc']
                except KeyError:
                    raise Exception("CENTURY outputs not as expected")
                grass['dead_gm2'] = outputs.loc[target_month, 'stdedc']
                if not args[u'user_define_protein']:
                    try:
                        N_mult = grass['N_multiplier']
                    except KeyError:
                        N_mult = 1
                    grass['cprotein_green'] = (outputs.loc[target_month,
                                               'aglive1'] / outputs.loc[
                                               target_month, 'aglivc']
                                               * N_mult)
                                               
                    grass['cprotein_dead'] = (outputs.loc[target_month,
                                              'stdede1'] / outputs.loc[
                                              target_month, 'stdedc']
                                              * N_mult)
            if step == 0:
                available_forage = forage.calc_feed_types(grass_list)
            else:
                available_forage = forage.update_feed_types(grass_list,
                                                            available_forage)
            results_dict['step'].append(step)
            results_dict['year'].append(year)
            results_dict['month'].append(month)
            for feed_type in available_forage:
                results_dict[feed_type.label + '_' + feed_type.green_or_dead +
                             '_kgha'].append(feed_type.biomass)

            if not args[u'user_define_digestibility']:
                for feed_type in available_forage:
                    feed_type.calc_digestibility_from_protein()

            total_biomass = forage.calc_total_biomass(available_forage)
            if step == 0:
                # threshold biomass, amount of biomass required to be left
                # standing (kg per ha)
                threshold_biomass = total_biomass * float(
                                    args[u'mgmt_threshold'])
            diet_dict = {}        
            for herb_class in herbivore_list:
                if args['grz_months'] is not None and step not in \
                                                            args['grz_months']:
                    diet = forage.Diet()
                    diet.fill_intake_zero(available_forage)
                    diet_dict[herb_class.label] = diet
                    continue
                if args['density_series'] is not None and step in \
                                                 args['density_series'].keys():
                    herb_class.stocking_density = args['density_series'][step]
                    stocking_density_dict = forage.populate_sd_dict(
                                                                herbivore_list)
                    total_SD = forage.calc_total_stocking_density(
                                                                herbivore_list)
                herb_class.calc_distance_walked(total_SD, site.S,
                                                available_forage)
                max_intake = herb_class.calc_max_intake()

                ZF = herb_class.calc_ZF()
                HR = forage.calc_relative_height(available_forage)
                diet = forage.diet_selection_t2(ZF, HR, args[u'prop_legume'],
                                                supp_available, supp,
                                                max_intake, herb_class.FParam,
                                                available_forage,
                                                herb_class.f_w, herb_class.q_w)
                diet_interm = forage.calc_diet_intermediates(
                                diet, supp, herb_class, site,
                                args[u'prop_legume'], args[u'DOY'])
                if herb_class.type != 'hindgut_fermenter':
                    reduced_max_intake = forage.check_max_intake(diet,
                                                                 diet_interm,
                                                                 herb_class,
                                                                 max_intake)
                    if reduced_max_intake < max_intake:
                        diet = forage.diet_selection_t2(ZF, HR,
                                                        args[u'prop_legume'],
                                                        supp_available, supp,
                                                        reduced_max_intake,
                                                        herb_class.FParam,
                                                        available_forage)
                diet_dict[herb_class.label] = diet
            forage.reduce_demand(diet_dict, stocking_density_dict,
                                 available_forage)
            if args['diet_verbose']:
                # save diet_dict across steps to be written out later
                master_diet_dict[step] = diet_dict
                diet_segregation = forage.calc_diet_segregation(diet_dict)
                diet_segregation_dict['step'].append(step)
                diet_segregation_dict['segregation'].append(diet_segregation)
            total_intake_step = forage.calc_total_intake(diet_dict,
                                                         stocking_density_dict)
            if (total_biomass - total_intake_step) < threshold_biomass:
                print "Forage consumed violates management threshold"
                threshold_exceeded = 1
                total_intake_step = 0
            for herb_class in herbivore_list:
                if threshold_exceeded:
                    a_diet = forage.Diet()
                    a_diet.fill_intake_zero(available_forage)
                    diet_dict[herb_class.label] = a_diet
                diet = diet_dict[herb_class.label]
                # if herb_class.type != 'hindgut_fermenter':
                diet_interm = forage.calc_diet_intermediates(
                                        diet, supp, herb_class, site,
                                        args[u'prop_legume'], args[u'DOY'])
                if herb_class.sex == 'lac_female':
                    milk_production = forage.check_milk_production(
                                                         herb_class.FParam,
                                                         diet_interm)
                    milk_kg_day = herb_class.calc_milk_yield(
                                                           milk_production)
                if threshold_exceeded:
                    if args['restart_monthly']:
                        delta_W = 0
                    else:
                        delta_W = -(forage.convert_step_to_daily(herb_class.W))
                else:
                    delta_W = forage.calc_delta_weight(diet_interm,
                                                       herb_class)
                if args['grz_months'] is not None and step not in \
                                                            args['grz_months']:
                    delta_W_step = 0
                else:
                    delta_W_step = forage.convert_daily_to_step(delta_W)
                try:
                    if not args['restart_monthly']:
                        herb_class.update(delta_weight=delta_W_step,
                                        delta_time=forage.find_days_per_step())
                    else:
                        herb_class.update(delta_weight=delta_W_step,
                                      delta_time=forage.find_days_per_step())
                except KeyError:
                    herb_class.update(delta_weight=delta_W_step,
                                      delta_time=forage.find_days_per_step())
                results_dict[herb_class.label + '_kg'].append(herb_class.W)
                results_dict[herb_class.label + '_gain_kg'].append(
                                                                  delta_W_step)
                results_dict[herb_class.label +
                             '_intake_forage_per_indiv_kg'].append(
                                         forage.convert_daily_to_step(diet.If))
                if herb_class.sex == 'lac_female':
                    results_dict['milk_prod_kg'].append(
                                     forage.convert_daily_to_step(milk_kg_day))

            # calculate percent live and dead removed for each grass type
            consumed_dict = forage.calc_percent_consumed(available_forage,
                                                         diet_dict,
                                                         stocking_density_dict)

            results_dict['total_offtake'].append(total_intake_step)
            # send to CENTURY for this month's scheduled grazing event
            date = year + float('%.2f' % (month / 12.))
            for grass in grass_list:
                g_label = ';'.join([grass['label'], 'green'])
                d_label = ';'.join([grass['label'], 'dead'])
                # only modify schedule if any of this grass was grazed
                if consumed_dict[g_label] > 0 or consumed_dict[d_label] > 0:
                    schedule = os.path.join(args[u'century_dir'],
                                            (grass['label'] + '.sch'))
                    target_dict = cent.find_target_month(add_event, schedule,
                                                         date, 1)
                    new_code = cent.add_new_graz_level(grass, consumed_dict,
                                                       graz_file,
                                                       args[u'template_level'],
                                                       args[u'outdir'], step)
                    cent.modify_schedule(schedule, add_event, target_dict,
                                         new_code, args[u'outdir'], step)

                # call CENTURY from the batch file
                century_bat = os.path.join(args[u'century_dir'],
                                           (grass['label'] + '.bat'))
                cent.launch_CENTURY_subprocess(century_bat)
                
                # save copies of CENTURY outputs, but remove from CENTURY dir
                century_outputs = [grass['label']+'_log.txt',
                                   grass['label']+'.lis',
                                   grass['label']+'.bin']
                intermediate_dir = os.path.join(args['outdir'],
                                     'CENTURY_outputs_m%d_y%d' % (month, year))
                if not os.path.exists(intermediate_dir):
                    os.makedirs(intermediate_dir)
                for file_name in century_outputs:
                    n_tries = 6
                    while True:
                        if n_tries == 0: 
                            break
                        try:
                            n_tries -= 1
                            shutil.move(os.path.join(args[u'century_dir'],
                                                     file_name),
                                        os.path.join(intermediate_dir,
                                                     file_name))
                            break
                        except OSError:
                            print 'OSError in moving %s, trying again' % \
                                    file_name
                            time.sleep(1.0)
        # add final standing biomass to summary file
        step = args[u'num_months'] + 1
        step_month = args[u'start_month'] + step
        if step_month > 12:
            mod = step_month % 12
            if mod == 0:
                month = 12
                year = (step_month / 12) + args[u'start_year'] - 1
            else:
                month = mod
                year = (step_month / 12) + args[u'start_year']
        else:
            month = step_month
            year = (step / 12) + args[u'start_year']
        for grass in grass_list:
            output_file = os.path.join(intermediate_dir,
                                       grass['label'] + '.lis')
            outputs = cent.read_CENTURY_outputs(output_file,
                                                year - 1,
                                                year + 1)
            outputs.drop_duplicates(inplace=True)
            target_month = cent.find_prev_month(year, month)
            grass['prev_g_gm2'] = grass['green_gm2']
            grass['prev_d_gm2'] = grass['dead_gm2']
            try:
                grass['green_gm2'] = outputs.loc[target_month, 'aglivc']
            except KeyError:
                raise Exception("CENTURY outputs not as expected")
            grass['dead_gm2'] = outputs.loc[target_month, 'stdedc']
        available_forage = forage.update_feed_types(grass_list,
                                                    available_forage)
        for feed_type in available_forage:
            results_dict[feed_type.label + '_' + feed_type.green_or_dead +
                         '_kgha'].append(feed_type.biomass)
    except:
        raise
    finally:
        ### Cleanup files
        # replace graz params used by CENTURY with original file
        os.remove(graz_file)
        shutil.copyfile(os.path.join(args[u'century_dir'], 'graz_orig.100'),
                        graz_file)
        os.remove(os.path.join(args[u'century_dir'], 'graz_orig.100'))
        file_list = set(file_list)
        files_to_remove = [os.path.join(args[u'century_dir'], os.path.basename(
                                                       f)) for f in file_list]
        for file_name in files_to_remove:
            os.remove(file_name)
        for grass in grass_list:
            os.remove(os.path.join(args[u'century_dir'], grass['label']
                      + '_hist.bin'))
        for schedule in schedule_list:
            label = os.path.basename(schedule)[:-4]
            orig_copy = os.path.join(args[u'input_dir'], label + '_orig.sch')
            os.remove(orig_copy)
        for grass in grass_list:
            os.remove(os.path.join(args[u'input_dir'], (grass['label'] +
                                   '_hist.bat')))
            os.remove(os.path.join(args[u'input_dir'], (grass['label'] +
                                   '.bat')))
            for ext in ['.lis', '.bin', '_log.txt']:
                obj = os.path.join(args[u'century_dir'], grass['label'] + ext)
                if os.path.isfile(obj):
                    os.remove(obj)
        if args['diet_verbose']:
            df = pandas.DataFrame(diet_segregation_dict)
            save_as = os.path.join(args['outdir'], 'diet_segregation.csv')
            df.to_csv(save_as, index=False)
            for h_label in master_diet_dict[0].keys():
                new_dict = {}
                new_dict['step'] = master_diet_dict.keys()
                new_dict['DMDf'] = [master_diet_dict[step][h_label].DMDf for
                                    step in master_diet_dict.keys()]
                new_dict['CPIf'] = [master_diet_dict[step][h_label].CPIf for
                                    step in master_diet_dict.keys()]
                grass_labels = master_diet_dict[0][h_label].intake.keys()
                for g_label in grass_labels:
                    new_dict['intake_' + g_label] = \
                          [master_diet_dict[step][h_label].intake[g_label] for
                           step in master_diet_dict.keys()]
                df = pandas.DataFrame(new_dict)
                save_as = os.path.join(args['outdir'], h_label + '_diet.csv')
                df.to_csv(save_as, index=False)
        filled_dict = forage.fill_dict(results_dict, 'NA')
        df = pandas.DataFrame(filled_dict)
        df.to_csv(os.path.join(args['outdir'], 'summary_results.csv'))
