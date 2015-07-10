# Tier 2 forage model
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
# Freer, M, A. D Moore, and J. R Donnelly. The GRAZPLAN Animal Biology Model for
# Sheep and Cattle and the GrazFeed Decision Support Tool. Canberra, ACT
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
    
    FParam = FreerParam.FreerParam(forage.get_general_breed(args[u'breed']))
    forage.set_time_step(args[u'time_step'])
    steps_per_year = forage.find_steps_per_year()
    graz_file = os.path.join(args[u'century_dir'], 'graz.100')
    cent.set_century_directory(args[u'century_dir'])

    herbivore_input = (pandas.read_csv(args[u'herbivore_csv'])).to_dict(orient = 'records')
    herbivore_list = []
    for h_class in herbivore_input:
        herd = forage.HerbivoreClass(FParam, args[u'breed'], h_class['weight'], h_class['sex'],
                             h_class['age'], h_class['stocking_density'],
                             h_class['label'])
        herd.update(FParam, 0, 0)
        herbivore_list.append(herd)

    grass_list = (pandas.read_csv(args[u'grass_csv'])).to_dict(orient = 'records')
    forage.check_initial_biomass(grass_list)
    schedule_list = []
    for grass in grass_list:
        schedule = os.path.join(args[u'century_dir'], (grass['label'] + '.sch'))
        if os.path.exists(schedule):
            schedule_list.append(schedule)
        else:
            er = "Error: schedule file not found"
            print er
            sys.exit(er)
        # write CENTURY bat for spin-up simulation
        hist_bat = os.path.join(args[u'century_dir'], (grass['label'] + '_hist.bat'))
        hist_schedule = grass['label'] + '_hist.sch'
        hist_output = grass['label'] + '_hist'
        cent.write_century_bat(args[u'century_dir'], hist_bat, hist_schedule, hist_output,
            args[u'fix_file'], args[u'outvars'])
        # write CENTURY bat for extend simulation
        extend_bat = os.path.join(args[u'century_dir'], (grass['label'] + '.bat'))
        schedule = grass['label'] + '.sch'
        output = grass['label']
        extend = grass['label'] + '_hist'
        cent.write_century_bat(args[u'century_dir'], extend_bat, schedule, output, args[u'fix_file'],
            args[u'outvars'], extend)
            
    # make a copy of the original graz params and schedule file
    shutil.copyfile(graz_file, os.path.join(args[u'century_dir'], 'graz_orig.100'))
    for schedule in schedule_list:
        label = os.path.basename(schedule)[:-4]
        copy_name = label + '_orig.100'
        shutil.copyfile(schedule, os.path.join(args[u'century_dir'], copy_name))

    # run CENTURY for spin-up for each grass type up to start_year and start_month
    for grass in grass_list:
        hist_bat = os.path.join(args[u'century_dir'], (grass['label'] + '_hist.bat'))
        century_bat = os.path.join(args[u'century_dir'], (grass['label'] + '.bat'))
        p = Popen(["cmd.exe", "/c " + hist_bat], cwd = args[u'century_dir'])
        stdout, stderr = p.communicate()
        p = Popen(["cmd.exe", "/c " + century_bat], cwd = args[u'century_dir'])
        stdout, stderr = p.communicate()

    total_SD = forage.calc_total_stocking_density(herbivore_list)
    site = forage.SiteInfo(total_SD, args[u'steepness'], args[u'latitude'])
    supp = forage.Supplement(FParam, 0.643, 0, 8.87, 0.031, 0.181, 0.5)  # Rubanza et al 2005
    if supp.DMO > 0.:
        supp_available = 1
    else:
        supp_available = 0
        
    try:
        for step in xrange(args[u'num_months']):
            month = args[u'start_month'] + step
            if month > 12:
                year = args[u'start_year'] + 1
                month = month - 12
            else:
                year = args[u'start_year']
            # get biomass and crude protein for each grass type from CENTURY
            for grass in grass_list:
                output_file = os.path.join(args[u'century_dir'], (grass['label'] + '.lis'))
                outputs = cent.read_CENTURY_outputs(output_file, args[u'start_year'],
                                                    args[u'start_year'] + 2)
                target_month = cent.find_prev_month(year, month)
                grass['prev_g_gm2'] = grass['green_gm2']
                grass['prev_d_gm2'] = grass['dead_gm2']
                grass['green_gm2'] = outputs.loc[target_month, 'aglivc']
                grass['dead_gm2'] = outputs.loc[target_month, 'stdedc']
                if not args[u'user_define_protein']:
                    grass['cprotein_green'] = (outputs.loc[target_month, 'aglive1']
                        / outputs.loc[target_month, 'aglivc'])
                    grass['cprotein_dead'] = (outputs.loc[target_month, 'stdede1']
                        / outputs.loc[target_month, 'stdedc'])
            if step == 0:
                available_forage = forage.calc_feed_types(grass_list)
            else:
                available_forage = forage.update_feed_types(grass_list,
                                                            available_forage)
            site.calc_distance_walked(FParam, available_forage)
            if args[u'calc_DMD_from_protein']:
                for feed_type in available_forage:
                    feed_type.calc_digestibility_from_protein()
                
            total_biomass = forage.calc_total_biomass(available_forage)

            if step == 0:
                # threshold biomass, amount of biomass required to be left standing
                # in kg per ha
                threshold_biomass = total_biomass * float(args[u'mgmt_threshold'])
                
            print "##### starting simulation #####"
            
            # Initialize containers to track forage consumed across herbivore classes
            total_intake_step = 0.
            total_consumed = {}
            for feed_type in available_forage:
                label_string = ';'.join([feed_type.label, feed_type.green_or_dead])
                total_consumed[label_string] = 0.

            # TODO herb class ordering ('who eats first') goes here
            for herb_class in herbivore_list:
                max_intake = herb_class.calc_max_intake(FParam)

                if herb_class.Z < FParam.CR7:
                    ZF = 1. + (FParam.CR7 - herb_class.Z)
                else:
                    ZF = 1.

                diet = forage.diet_selection_t2(ZF, args[u'prop_legume'], supp_available, supp,
                                max_intake, FParam, available_forage)
                diet_interm = forage.calc_diet_intermediates(FParam, diet, supp,
                                herb_class, site, args[u'prop_legume'], args[u'DOY'])
                reduced_max_intake = forage.check_max_intake(FParam, diet,
                                diet_interm, herb_class, max_intake)
                if reduced_max_intake < max_intake:
                    print "## selecting diet with reduced intake ##"
                    print "reduced max intake: %f" % reduced_max_intake
                    diet = forage.diet_selection_t2(ZF, args[u'prop_legume'], supp_available,
                                supp, reduced_max_intake, FParam, available_forage)
                    diet_interm = forage.calc_diet_intermediates(FParam, diet, supp,
                                herb_class, site, args[u'prop_legume'], args[u'DOY'])
                
                total_intake_step += (forage.convert_daily_to_step(diet.If) * 
                                      herb_class.stocking_density)

                # is amount of forage removed above the management threshold?
                if (total_biomass - total_intake_step) < threshold_biomass:
                    er = "Forage consumed violates management threshold"
                    print er
                    sys.exit(er)  # for now
                    
                if herb_class.sex == 'lac_female':
                    milk_production = forage.check_milk_production(FParam, diet_interm)
                    milk_kg_day = forage.calc_milk_yield(FParam, milk_production)
                
                delta_W = forage.calc_delta_weight(FParam, diet, diet_interm, supp,
                                herb_class)
                print "weight change in one day: %f" % delta_W

                delta_W_step = forage.convert_daily_to_step(delta_W)
                herb_class.update(FParam, delta_W_step, forage.find_days_per_step())
        
                # TODO track model outputs: 
                    # weight gain for herbivore classes that will be sold for meat
                    # milk yield for lactating females

                # after have performed max intake check, we have the final diet selected
                # calculate percent live and dead removed for each grass type
                consumed_by_class = forage.calc_percent_consumed(available_forage,
                                diet, herb_class.stocking_density)
                forage.sum_percent_consumed(total_consumed, consumed_by_class)

            # send to CENTURY for this month's scheduled grazing event
            date = year + float('%.2f' % (month / 12.))
            for grass in grass_list:
                schedule = os.path.join(args[u'century_dir'], (grass['label'] + '.sch'))
                target_dict = cent.find_target_month(args[u'add_event'], schedule, date, 1)
                new_code = cent.add_new_graz_level(grass, total_consumed, graz_file,
                    args[u'template_level'], args[u'outdir'], step)
                cent.modify_schedule(schedule, args[u'add_event'], target_dict, new_code,
                    args[u'outdir'], step)
                
                # call CENTURY from the batch file
                century_bat = os.path.join(args[u'century_dir'], (grass['label'] + '.bat'))
                p = Popen(["cmd.exe", "/c " + century_bat], cwd = args[u'century_dir'])
                stdout, stderr = p.communicate()
            
    finally:
        # replace graz params used by CENTURY with original file      
        os.remove(graz_file)
        shutil.copyfile(os.path.join(args[u'century_dir'], 'graz_orig.100'), graz_file)
        os.remove(os.path.join(args[u'century_dir'], 'graz_orig.100'))
        for schedule in schedule_list:
            # replace schedule files used by CENTURY with original files
            os.remove(schedule)
            label = os.path.basename(schedule)[:-4]
            copy_name = label + '_orig.100'
            shutil.copyfile(os.path.join(args[u'century_dir'], copy_name), schedule)
            os.remove(os.path.join(args[u'century_dir'], copy_name))

args = {     
    'latitude': 0.083,  # degrees (if south of equator, this should be negative)
    'time_step': 'month',
    'prop_legume': 0.0,
    'breed': 'Brahman',  # see documentation for allowable breeds; assumed to apply to all animal classes
    'steepness': 1.,  # steepness of site: between 1 and 2
    'DOY': 1,  # initial day of the year
    'start_year': 2013,
    'start_month': 1,   # 1:12, corresponding to January:December
    'num_months': 12,
    'mgmt_threshold': 0.5,  # % of all initial biomass that must remain
    'century_dir': 'C:\Users\Ginger\Dropbox\NatCap_backup\Forage_model\CENTURY4.6\Century46_PC_Jan-2014',
    'outdir': "C:\\Users\\Ginger\\Documents\\Python\\Output",
    'template_level': 'GL',
    'add_event': 1,
    'fix_file': 'drytrpfi.100',
    'outvars': 'outvars.txt',
    'user_define_protein': 0,  # get crude protein from user, or calculate via CENTURY?
    'user_define_digestibility': 0,  # get digestibility from user, or calculate from crude protein?
    'calc_DMD_from_protein': 1,  # calculate digestibility from protein?
    'herbivore_csv': "C:\Users\Ginger\Dropbox\NatCap_backup\Forage_model\Forage_model\model_inputs\herbivores.csv",
    'grass_csv': "C:\Users\Ginger\Dropbox\NatCap_backup\Forage_model\Forage_model\model_inputs\grass.csv",
}

if __name__ == "__main__":
    execute(args)