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
from subprocess import Popen
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
            legume, ranging from 0-1
        args['breed'] - breed of livestock, assumed to apply to the entire
            herd.  See documentation for allowable values.
        args['steepness'] - site steepness, ranging from 1 to 2
        args['DOY'] - initial day of the year, an integer ranging from 1:365
        args['start_year'] - initial year, an integer
        args['start_month'] - initial month, an integer ranging from 1:12
            corresponding to January:December
        args['num_months'] - number of months to run the simulation
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
            necessary descriptors of the herbivore herd
        args['grass_csv'] - an absolute path to a csv file containing all
            necessary descriptors of the grass available as forage
        args['supp_csv'] - an absolute path to a csv file containing all
            necessary descriptors of supplemental feed (optional)

        returns nothing."""

    FParam = FreerParam.FreerParam(forage.get_general_breed(args[u'breed']))
    forage.set_time_step('month')  # current default, enforced by CENTURY
    add_event = 1  # TODO should this ever be 0?
    steps_per_year = forage.find_steps_per_year()
    graz_file = os.path.join(args[u'century_dir'], 'graz.100')
    cent.set_century_directory(args[u'century_dir'])

    herbivore_input = (pandas.read_csv(args[u'herbivore_csv'])).to_dict(
                       orient='records')
    herbivore_list = []
    for h_class in herbivore_input:
        herd = forage.HerbivoreClass(FParam, args[u'breed'], h_class['weight'],
                                     h_class['sex'], h_class['age'],
                                     h_class['stocking_density'],
                                     label=h_class['label'], Wbirth=24,
                                     SRW=550)
        herd.update(FParam, 0, 0)
        herbivore_list.append(herd)

    grass_list = (pandas.read_csv(args[u'grass_csv'])).to_dict(
                                                              orient='records')
    forage.check_initial_biomass(grass_list)
    results_dict = {'step': [], 'year': [], 'month': []}
    for h_class in herbivore_list:
        results_dict[h_class.label + '_kg'] = []
        results_dict[h_class.label + '_gain_kg'] = []
        results_dict[h_class.label + '_offtake'] = []
        if h_class.sex == 'lac_female':
            results_dict['milk_prod_kg'] = []
    for grass in grass_list:
        results_dict[grass['label'] + '_green_kgha'] = []
        results_dict[grass['label'] + '_dead_kgha'] = []
    results_dict['total_offtake'] = []
    schedule_list = []
    for grass in grass_list:
        schedule = os.path.join(args[u'input_dir'], (grass['label'] +
                                '.sch'))
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
        supp = forage.Supplement(FParam, supp_info['digestibility'],
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
    for grass in grass_list:
        spin_up_outputs = [grass['label']+'_hist_log.txt',
                           grass['label']+'_hist.lis']
        century_outputs = [grass['label']+'_log.txt', grass['label']+'.lis',
                           grass['label']+'.bin']
        
        # move CENTURY run files to CENTURY dir
        site_file = os.path.join(args[u'input_dir'], grass['label'] + '.100')
        weather_file = os.path.join(args[u'input_dir'],
                                    grass['label'] + '.wth')
        e_schedule = os.path.join(args[u'input_dir'], grass['label'] + '.sch')
        h_schedule = os.path.join(args[u'input_dir'],
                                  grass['label'] + '_hist.sch')
        file_list = [hist_bat, extend_bat, e_schedule, h_schedule, site_file,
                     weather_file]
        for file in file_list:
            shutil.copyfile(file, os.path.join(args[u'century_dir'],
                                               os.path.basename(file)))
        # run CENTURY for spin-up for each grass type up to start_year and
        # start_month                                       
        hist_bat = os.path.join(args[u'century_dir'], (grass['label'] +
                                '_hist.bat'))
        century_bat = os.path.join(args[u'century_dir'], (grass['label'] +
                                   '.bat'))
        p = Popen(["cmd.exe", "/c " + hist_bat], cwd=args[u'century_dir'])
        stdout, stderr = p.communicate()
        p = Popen(["cmd.exe", "/c " + century_bat], cwd=args[u'century_dir'])
        stdout, stderr = p.communicate()

        # save copies of CENTURY outputs, but remove from CENTURY dir
        intermediate_dir = os.path.join(args['outdir'],
                                        'CENTURY_outputs_spin_up')
        if not os.path.exists(intermediate_dir):
            os.makedirs(intermediate_dir)
        to_move = century_outputs + spin_up_outputs
        for file in to_move:
            shutil.copyfile(os.path.join(args[u'century_dir'], file),
                            os.path.join(intermediate_dir, file))
            os.remove(os.path.join(args[u'century_dir'], file))
            
    total_SD = forage.calc_total_stocking_density(herbivore_list)
    site = forage.SiteInfo(total_SD, args[u'steepness'], args[u'latitude'])
    threshold_exceeded = 0
    try:
        for step in xrange(args[u'num_months']):
            if threshold_exceeded:
                break
            month = args[u'start_month'] + step
            if month > 12:
                year = args[u'start_year'] + 1
                month = month - 12
            else:
                year = args[u'start_year']
            # get biomass and crude protein for each grass type from CENTURY
            for grass in grass_list:
                output_file = os.path.join(intermediate_dir,
                                           grass['label'] + '.lis')
                outputs = cent.read_CENTURY_outputs(output_file,
                                                    args[u'start_year'],
                                                    args[u'start_year'] + 2)
                target_month = cent.find_prev_month(year, month)
                grass['prev_g_gm2'] = grass['green_gm2']
                grass['prev_d_gm2'] = grass['dead_gm2']
                grass['green_gm2'] = outputs.loc[target_month, 'aglivc']
                grass['dead_gm2'] = outputs.loc[target_month, 'stdedc']
                if not args[u'user_define_protein']:
                    grass['cprotein_green'] = (outputs.loc[target_month,
                                               'aglive1'] / outputs.loc[
                                               target_month, 'aglivc'])
                    grass['cprotein_dead'] = (outputs.loc[target_month,
                                              'stdede1'] / outputs.loc[
                                            target_month, 'stdedc'])
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

            site.calc_distance_walked(FParam, available_forage)
            if not args[u'user_define_digestibility']:
                for feed_type in available_forage:
                    feed_type.calc_digestibility_from_protein()

            total_biomass = forage.calc_total_biomass(available_forage)

            if step == 0:
                # threshold biomass, amount of biomass required to be left
                # standing (kg per ha)
                threshold_biomass = total_biomass * float(
                                    args[u'mgmt_threshold'])

            # Initialize containers to track forage consumed across herbivore
            # classes
            total_intake_step = 0.
            total_consumed = {}
            for feed_type in available_forage:
                label_string = ';'.join([feed_type.label,
                                        feed_type.green_or_dead])
                total_consumed[label_string] = 0.

            # TODO herb class ordering ('who eats first') goes here
            for herb_class in herbivore_list:
                max_intake = herb_class.calc_max_intake(FParam)

                if herb_class.Z < FParam.CR7:
                    ZF = 1. + (FParam.CR7 - herb_class.Z)
                else:
                    ZF = 1.
                
                adj_forage = forage.calc_adj_availability(available_forage,
                                                   herb_class.stocking_density)
                diet = forage.diet_selection_t2(ZF, args[u'prop_legume'],
                                                supp_available, supp,
                                                max_intake, FParam,
                                                adj_forage)
                diet_interm = forage.calc_diet_intermediates(FParam, diet,
                                supp, herb_class, site, args[u'prop_legume'],
                                args[u'DOY'])
                reduced_max_intake = forage.check_max_intake(FParam, diet,
                                            diet_interm, herb_class,
                                            max_intake)
                if reduced_max_intake < max_intake:
                    print "## selecting diet with reduced intake ##"
                    print "reduced max intake: %f" % reduced_max_intake
                    diet = forage.diet_selection_t2(ZF, args[u'prop_legume'],
                                                    supp_available, supp,
                                                    reduced_max_intake, FParam,
                                                    adj_forage)
                    diet_interm = forage.calc_diet_intermediates(FParam, diet,
                                    supp, herb_class, site,
                                    args[u'prop_legume'], args[u'DOY'])

                total_intake_step += (forage.convert_daily_to_step(diet.If) *
                                      herb_class.stocking_density)

                # is amount of forage removed above the management threshold?
                if (total_biomass - total_intake_step) < threshold_biomass:
                    print "Forage consumed violates management threshold"
                    threshold_exceeded = 1
                    break

                if herb_class.sex == 'lac_female':
                    milk_production = forage.check_milk_production(FParam,
                                                                   diet_interm)
                    milk_kg_day = forage.calc_milk_yield(FParam,
                                                         milk_production)

                delta_W = forage.calc_delta_weight(FParam, diet, diet_interm,
                                                   supp, herb_class)

                delta_W_step = forage.convert_daily_to_step(delta_W)
                herb_class.update(FParam, delta_W_step,
                                  forage.find_days_per_step())

                results_dict[herb_class.label + '_kg'].append(herb_class.W)
                results_dict[herb_class.label + '_gain_kg'].append(
                                                                  delta_W_step)
                results_dict[herb_class.label + '_offtake'].append(
                                                               diet.If)
                if herb_class.sex == 'lac_female':
                    results_dict['milk_prod_kg'].append(milk_kg_day * 30.)

                # after have performed max intake check, we have the final diet
                # selected
                # calculate percent live and dead removed for each grass type
                consumed_by_class = forage.calc_percent_consumed(
                                    available_forage, diet,
                                    herb_class.stocking_density)
                forage.sum_percent_consumed(total_consumed, consumed_by_class)

            results_dict['total_offtake'].append(total_intake_step)
            # send to CENTURY for this month's scheduled grazing event
            date = year + float('%.2f' % (month / 12.))
            for grass in grass_list:
                schedule = os.path.join(args[u'century_dir'], (grass['label'] +
                                        '.sch'))
                target_dict = cent.find_target_month(add_event, schedule, date,
                                                     1)
                new_code = cent.add_new_graz_level(grass, total_consumed,
                                                   graz_file,
                                                   args[u'template_level'],
                                                   args[u'outdir'], step)
                cent.modify_schedule(schedule, add_event, target_dict,
                                     new_code, args[u'outdir'], step)

                # call CENTURY from the batch file
                century_bat = os.path.join(args[u'century_dir'],
                                           (grass['label'] + '.bat'))
                p = Popen(["cmd.exe", "/c " + century_bat],
                          cwd=args[u'century_dir'])
                stdout, stderr = p.communicate()
                # save copies of CENTURY outputs, but remove from CENTURY dir
                intermediate_dir = os.path.join(args['outdir'],
                                     'CENTURY_outputs_m%d_y%d' % (month, year))
                if not os.path.exists(intermediate_dir):
                    os.makedirs(intermediate_dir)
                for file in century_outputs:
                    shutil.copyfile(os.path.join(args[u'century_dir'], file),
                                    os.path.join(intermediate_dir, file))
                    os.remove(os.path.join(args[u'century_dir'], file))
    finally:
        # replace graz params used by CENTURY with original file
        os.remove(graz_file)
        shutil.copyfile(os.path.join(args[u'century_dir'], 'graz_orig.100'),
                        graz_file)
        os.remove(os.path.join(args[u'century_dir'], 'graz_orig.100'))
        files_to_remove = [os.path.join(args[u'century_dir'], os.path.basename(
                                                       f)) for f in file_list]
        for file in files_to_remove:
            os.remove(file)
        for grass in grass_list:
            os.remove(os.path.join(args[u'century_dir'], grass['label']
                      + '_hist.bin'))
        filled_dict = forage.fill_dict(results_dict, 'NA')
        df = pandas.DataFrame(filled_dict)
        df.to_csv(os.path.join(args['outdir'], 'summary_results.csv'))
