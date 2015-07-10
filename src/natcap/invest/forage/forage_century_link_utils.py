"""Helper functions: link CENTURY model with livestock model."""

import os
import sys
import math
import pandas
from tempfile import mkstemp
import shutil
import random
import string

global _century_dir

# disable setting with copy warning
pandas.options.mode.chained_assignment = None

def set_century_directory(century_dir):
    global _century_dir
    _century_dir = century_dir
    
def check_CENTURY_log(filename):
    """Check that CENTURY completed successfully. If not, raise an exception."""

    success = 0
    error = []
    with open(filename, 'r') as file:
        for line in file:
            if 'Execution success.' in line:
                success = 1
                break
    if not success:
        with open(filename, 'r') as file:
            error = [line.strip() for line in file]
            raise Exception(error)
            
def read_graz_params(graz_file):
    """Tabulate the values for flgrem (fraction live above-ground biomass
    removed) and fdgrem (fraction standing dead above-ground biomass removed)
    for different grazing level codes.  The grazing parameter definition file
    supplied as argument here should be the same definition file used for the
    CENTURY run."""
    
    glevel_list = []
    flgrem_list = []
    fdgrem_list = []
    with open(graz_file, 'r') as file:
        for line in file:
            if 'GM ' in line or 'G ' in line or 'GCS ' in line or 'W ' in line \
                or 'GL ' in line or 'GH ' in line or 'P ' in line:
                glevel_list.append(line[:3].strip())
                line = file.next()
                if 'FLGREM' in line:
                    flgrem = line[:8].strip()
                else:
                    er = "Error: FLGREM expected"
                    raise Exception(er)
                line = file.next()
                if 'FDGREM' in line:
                    fdgrem = line[:8].strip()
                else:
                    er = "Error: FDGREM expected"
                    raise Exception(er)
                flgrem_list.append(flgrem)
                fdgrem_list.append(fdgrem)
    dict = {'glevel': glevel_list, 'flgrem': flgrem_list, 'fdgrem': fdgrem_list}
    gparams_df = pandas.DataFrame(dict)
    gparams_indexed = gparams_df.set_index('glevel')
    return gparams_indexed

def modify_intensity(diff, graz_file, graz_level, outdir, suffix):
    """Modify past management in terms of intensity.  Modifies the grazing
    parameters file used by CENTURY for the specified grazing level, stashing a
    copy of the modified file in the outdir. Note that this function modifies
    the 'flgrem' and 'fdgrem' parameters of an existing grazing level code
    (e.g., 'GL') but does not add new codes (see function 'add_new_graz_level')."""
    # TODO use add_new_graz_level so that this affects only the selected month
    increase_intensity = 0
    if diff > 0:
        # simulated biomass greater than empirical
        increase_intensity = 1
        
    increment = 0.1  # TODO this should be dynamic
    fh, abs_path = mkstemp()
    try:
        with open(abs_path, 'wb') as new_file:
            with open(graz_file, 'rb') as old_file:
                for line in old_file:
                    if (graz_level + ' ') in line:
                        new_file.write(line)
                        line = old_file.next()
                        if 'FLGREM' in line:
                            flgrem = line[:8].strip()
                            if increase_intensity:
                                flgrem_mod = float(flgrem) + float(increment)
                            else:
                                flgrem_mod = float(flgrem) - float(increment)
                            if flgrem_mod >= 1.0 or flgrem_mod <= 0.:
                                return 0
                            line_mod = "%.5f           'FLGREM'\n" % flgrem_mod
                            new_file.write(line_mod)
                        else:
                            er = "Error: FLGREM expected"
                            raise Exception(er)
                        line = old_file.next()
                        if 'FDGREM' in line:
                            fdgrem = 0.1 * flgrem_mod  # fdgrem always 10% of flgrem
                            fdgrem = float('%.5f' % fdgrem)
                            line_mod = "%.5f           'FDGREM'\n" % fdgrem
                            new_file.write(line_mod)
                        else:
                            er = "Error: FDGREM expected"
                            raise Exception(er)
                    else:
                        new_file.write(line)
    except:
        print "Error in modify intensity: ", sys.exc_info()[0]
        raise
    else:
        # make a copy of the grazing parameters file and stash it in the outdir
        new_graz_params = os.path.join(outdir, ('graz_' + str(suffix) + '.100'))
        shutil.copyfile(abs_path, new_graz_params)
        shutil.copyfile(abs_path, graz_file)
        return 1

def read_block_schedule(schedule):
    """Read the CENTURY schedule file.  This function copies the block structure
    of the schedule file supplied to CENTURY, without regard for any scheduled
    events."""
    
    bl_st_year = []
    bl_end_year = []
    bl_rpt_year = []
    with open(schedule, 'r') as sch:
        for line in sch:
            if '   Starting year' in line:
                start_year = float(line[:9].strip())
                line = sch.next()
                continue
            if 'Last year' in line:
                year_l = float(line[:9].strip())
                line = sch.next()
                if 'Repeats # years' in line:
                    rpt_years = int(line[:5].strip())
                while '-999' not in line:
                    line = sch.next()
                # end of block reached
                bl_st_year.append(start_year)
                bl_end_year.append(year_l)
                bl_rpt_year.append(rpt_years)
                start_year = year_l + 1  # for next block
    composite_dict = {'block_start_year': bl_st_year, 
                      'block_end_year': bl_end_year, 'block_rpt_year': bl_rpt_year}
    schedule_df = pandas.DataFrame(composite_dict, columns = ['block_start_year',
                'block_end_year', 'block_rpt_year'])
    return schedule_df

def read_events(schedule):
    """Get scheduled events from the CENTURY schedule file.  This function
    copies the schedule file supplied to CENTURY for months where any event was
    scheduled, but does not record grazing levels."""
    
    bl_st_year = []
    bl_end_year = []
    bl_rpt_year = []
    year_list = []
    month_list = []
    event_list = []
    with open(schedule, 'r') as sch:
        for line in sch:
            if 'Starting year' in line:
                start_year = float(line[:9].strip())
                line = sch.next()
                continue
            if 'Last year' in line:
                year_l = float(line[:9].strip())
                line = sch.next()
                if 'Repeats # years' in line:
                    rpt_years = int(line[:5].strip())
                while 'Weather choice' not in line:
                    line = sch.next()
                # we have arrived at the line containing 'Weather choice'
                line = sch.next()
                if '.wth' in line:
                    line = sch.next()
                while '-999' not in line:
                    # reading contents of the block
                    if line[:3] == '   ':
                        relative_year = int(line[:5].strip())
                        month = int(line[6:10].strip())
                        event = line[10:15].strip()
                        
                        bl_st_year.append(start_year)
                        bl_end_year.append(year_l)
                        bl_rpt_year.append(rpt_years)
                        year_list.append(relative_year)
                        month_list.append(month)
                        event_list.append(event)
                    line = sch.next()
                # end of block reached
                start_year = year_l + 1  # for next block
    composite_dict = {'relative_year': year_list, 'month': month_list,
                      'event': event_list, 'block_start_year': bl_st_year,
                      'block_end_year': bl_end_year, 'block_rpt_year': bl_rpt_year}
    glevel_df = pandas.DataFrame(composite_dict, columns = ['relative_year',
                'month', 'event', 'block_start_year', 'block_end_year',
                'block_rpt_year'])
    return glevel_df

def read_graz_level(schedule):
    """Get grazing level codes from the CENTURY schedule file.  This function
    copies the schedule file supplied to CENTURY only for months where grazing
    took place.  The resulting table must be further processed by the
    'process_graz_level' function to generate a monthly schedule of grazing
    levels.  TODO: this function should probably be replaced by 'read_events'
    with an argument to pay attention only to grazing events."""
    
    bl_st_year = []
    bl_end_year = []
    bl_rpt_year = []
    year_list = []
    month_list = []
    glevel_list = []
    with open(schedule, 'r') as sch:
        for line in sch:
            if 'Starting year' in line:
                start_year = float(line[:9].strip())
                line = sch.next()
                continue
            if 'Last year' in line:
                year_l = float(line[:9].strip())
                line = sch.next()
                if 'Repeats # years' in line:
                    rpt_years = int(line[:5].strip())
                while 'Weather choice' not in line:
                    line = sch.next()
                # we have arrived at the line containing 'Weather choice'
                line = sch.next()
                if '.wth' in line:
                    line = sch.next()
                while '-999' not in line:
                    # reading contents of the block
                    if 'GRAZ' in line:
                        relative_year = int(line[:5].strip())
                        month = int(line[6:10].strip())
                        line = sch.next()
                        level = line[:4].strip()
                        
                        bl_st_year.append(start_year)
                        bl_end_year.append(year_l)
                        bl_rpt_year.append(rpt_years)
                        year_list.append(relative_year)
                        month_list.append(month)
                        glevel_list.append(level)
                    line = sch.next()
                # end of block reached
                start_year = year_l + 1  # for next block
    composite_dict = {'relative_year': year_list, 'month': month_list,
                      'grazing_level': glevel_list, 'block_start_year': bl_st_year,
                      'block_end_year': bl_end_year, 'block_rpt_year': bl_rpt_year}
    glevel_df = pandas.DataFrame(composite_dict, columns = ['relative_year',
                'month', 'grazing_level', 'block_start_year', 'block_end_year',
                'block_rpt_year'])
    return glevel_df

def process_graz_level(glevel_df, gparam_df):
    """Process the schedule of grazing events produced with the 'read_graz_level'
    function so that instead of being arranged by repeating blocks, the schedule
    is arranged by sequential month.  This function also interprets the grazing
    levels identified with 'read_graz_level' by finding the correct values for
    flgrem (fraction live biomass removed by grazing) and fdgrem (fraction
    standing dead biomass removed by grazing) for each grazing level."""
    
    year_list = []
    flgrem_list = []
    fdgrem_list = []
    for i in range(0, glevel_df.shape[0]):
        start_year = glevel_df.loc[i, 'block_start_year']
        last_year = glevel_df.loc[i, 'block_end_year']
        rpt_years = glevel_df.loc[i, 'block_rpt_year']
        rel_year = glevel_df.loc[i, 'relative_year']
        month = glevel_df.loc[i, 'month']
        g_level = glevel_df.loc[i, 'grazing_level']
        flgrem = float(gparam_df.loc[g_level, 'flgrem'])
        fdgrem = float(gparam_df.loc[g_level, 'fdgrem'])
        year = int(rel_year) - 1 + int(start_year)
        year_dec = float('%.2f' % (year + float(month) / 12.))
        if year_dec >= last_year:
            continue
        else:
            year_list.append(year_dec)
            flgrem_list.append(flgrem)
            fdgrem_list.append(fdgrem)
        while (year + float(month) / 12. + rpt_years) < last_year + 1:
            year += rpt_years
            year_dec = float('%.2f' % (year + float(month) / 12.))
            year_list.append(year_dec)
            flgrem_list.append(flgrem)
            fdgrem_list.append(fdgrem)
    dict = {'year': year_list, 'flgrem': flgrem_list, 'fdgrem': fdgrem_list}
    repeated_df = pandas.DataFrame(dict)
    repeated_indexed = repeated_df.set_index('year')
    return repeated_indexed
    
def read_CENTURY_outputs(cent_file, first_year, last_year):
    """Read biomass outputs from CENTURY for each month of CENTURY output within
    the specified range (between 'first_year' and 'last_year')."""
    
    cent_df = pandas.io.parsers.read_fwf(cent_file, skiprows = [1])
    df_subset = cent_df[(cent_df.time >= first_year) & (cent_df.time < last_year + 1)]
    biomass = df_subset[['time', 'aglivc', 'stdedc', 'aglive(1)', 'stdede(1)']]
    aglivc = biomass.aglivc * 2.5  # live biomass
    biomass.aglivc = aglivc
    stdedc = biomass.stdedc * 2.5  # standing dead biomass
    biomass.stdedc = stdedc
    biomass['total'] = biomass.aglivc + biomass.stdedc
    aglive1 = biomass[['aglive(1)']] * 6.25  # crude protein in  live material
    biomass['aglive1'] = aglive1
    stdede1 = biomass[['stdede(1)']] * 6.25  # crude protein in standing dead
    biomass['stdede1'] = stdede1
    biomass_indexed = biomass.set_index('time')
    return biomass_indexed

def convert_units(g_per_m2, cell_size_ha):
    """Convert a quantity in g per square m to kg per grid cell."""
    
    kg_per_m2 = float(g_per_m2) / 1000.
    kg_per_ha = kg_per_m2 * 10000.
    kg = kg_per_ha * cell_size_ha
    return kg
    
def write_century_bat(century_dir, century_bat, schedule, output, fix_file,
    outvars, extend = None):
    """Write the batch file to run CENTURY"""
    
    if schedule[-4:] == '.sch':
        schedule = schedule[:-4]
    if output[-4:] == '.lis':
        output = output[:-4]
    
    with open(os.path.join(century_dir, century_bat), 'wb') as file:
        file.write('erase ' + output + '.bin\n')
        file.write('erase ' + output + '.lis\n\n')
        
        file.write('copy fix.100 fix_orig.100\n')
        file.write('erase fix.100\n\n')
        
        file.write('copy ' + fix_file + ' fix.100\n')
        file.write('erase ' + output + '_log.txt\n\n')
        
        if extend is not None:
            file.write('century_46 -s ' + schedule + ' -n ' + output + ' -e ' +
                extend + ' > ' + output + '_log.txt\n')
        else:
            file.write('century_46 -s ' + schedule + ' -n ' + output + ' > ' + 
                output + '_log.txt\n')
        file.write('list100_46 ' + output + ' ' + output + ' ' + outvars +
            '\n\n')
        
        file.write('erase fix.100\n')
        file.write('copy fix_orig.100 fix.100\n')
        file.write('erase fix_orig.100\n')

def check_schedule(schedule, n_years, empirical_date):
    """Check that the schedule file used to produce CENTURY output can be
    modified by existing methods.  The block containing the empirical date to
    compare output with must contain n sequential years previous to the
    empirical date.  The block must also be composed of non-repeating
    sequences because any modification made should only apply to one year, not
    to every 3rd year, every 4th year, etc for example."""
    
    sufficient = 0
    schedule_df = read_block_schedule(schedule)
    for i in range(0, schedule_df.shape[0]):
        start_year = schedule_df.loc[i, 'block_start_year']
        last_year = schedule_df.loc[i, 'block_end_year']
        rpt_years = schedule_df.loc[i, 'block_rpt_year']
        if empirical_date > start_year and empirical_date <= last_year + 1:
            # empirical compare date falls in this block
            if (last_year - start_year) > rpt_years:
                # block contains repeating sequences
                er = "Error: CENTURY schedule file must contain non-repeating sequence for years to be manipulated"
                raise Exception(er)
            else:
                if (empirical_date - n_years) >= start_year:
                    sufficient = 1
    if sufficient:
        return
    else:
        er = "Error: CENTURY schedule file does not contain a single block that can be modified"
        raise Exception(er)

def fill_schedule(graz_schedule, first_year, end_year, end_month):
    """Fill in a grazing schedule, from first_year up to the end_year and
    end_month, with months where grazing did not take place."""
    
    filled_schedule = graz_schedule
    for year in xrange(first_year, end_year + 1):
        if year == end_year:
            last_month = end_month
        else:
            last_month = 12
        for month in xrange(1, last_month + 1):
            current_year = graz_schedule.loc[(graz_schedule['relative_year'] ==
                year), ]
            current_month = current_year.loc[(current_year['month'] == month), ]
            if current_month.shape[0] == 0:
                # no entry in schedule for this year/month combination:
                # add an entry with 'none' for grazing level
                df = pandas.DataFrame({'relative_year': [year], 'month':
                    [month], 'grazing_level': ['none']})
                filled_schedule = filled_schedule.append(df)
    return filled_schedule

def find_target_month(add_event, schedule, empirical_date, n_years):
    """Find the target month to add or remove grazing events from the schedule
    used by CENTURY.  This month should be immediately prior to the
    empirical_date and should include grazing (if add_event == 0) or should not
    include grazing (if add_event == 1)."""
    
    target_dict = {}
    
    # find the block we want to modify
    schedule_df = read_block_schedule(schedule)
    for i in range(0, schedule_df.shape[0]):
        start_year = schedule_df.loc[i, 'block_start_year']
        last_year = schedule_df.loc[i, 'block_end_year']
        if empirical_date > start_year and empirical_date <= last_year:
            break
    
    target_dict['last_year'] = last_year
    # find year and month of empirical measurement date relative to the block:
    # this is how they are specified in the schedule file
    relative_empirical_year = int(math.floor(empirical_date) - start_year + 1)
    empirical_month = int(round((empirical_date - float(math.floor(empirical_date)))
        * 12))
    
    # find months where grazing took place prior to empirical date
    graz_schedule = read_graz_level(schedule)
    block = graz_schedule.loc[(graz_schedule["block_end_year"] == last_year), 
        ['relative_year', 'month', 'grazing_level']]
    empirical_year = block.loc[(block['relative_year'] ==
        relative_empirical_year), ]
    empirical_year = empirical_year.loc[(empirical_year['month'] <=
        empirical_month), ]
    prev_year = block.loc[(block['relative_year'] < relative_empirical_year), ]
    prev_year = prev_year.loc[(prev_year['relative_year'] >=
        (relative_empirical_year - n_years)), ]
    history = prev_year.append(empirical_year)
    
    # fill the grazing history with months where no grazing event was scheduled
    filled_history = fill_schedule(history, relative_empirical_year - n_years,
        relative_empirical_year, empirical_month)
    # find candidate months for adding or removing grazing events
    if add_event:
        candidates = filled_history.loc[(filled_history['grazing_level'] ==
            'none'), ]
    else:
        candidates = filled_history.loc[(filled_history['grazing_level'] !=
            'none'), ] 
    if candidates.shape[0] == 0:
        # no opportunities exist to modify grazing schedule as needed
        return 0
    
    # find target month and year where grazing event should be added or removed
    else:
        candidates = candidates.sort(['relative_year', 'month'], ascending = [0, 0])
        target_year = candidates.iloc[0]['relative_year']
        target_month = candidates.iloc[0]['month']
    
    target_dict['target_year'] = target_year
    target_dict['target_month'] = target_month
    
    # if we need to add a grazing event, must find the latest previously 
    # scheduled event
    if add_event:
        events_df = read_events(schedule)
        events_df = events_df.loc[(events_df['block_end_year'] == last_year), ]
        events_df = events_df.loc[(events_df['relative_year'] == target_year), ]
        events_df = events_df.loc[(events_df['month'] <= target_month), ]
        events_df = events_df.sort(['relative_year', 'month'], ascending = [0, 0])
        prev_event_month = events_df.iloc[0]['month']
        prev_month = events_df.loc[(events_df['month'] == prev_event_month), ]
        num_events_prev_month = prev_month.shape[0]
        target_dict['num_events_prev_month'] = num_events_prev_month
        target_dict['prev_event_month'] = prev_event_month
    return target_dict    
    
def modify_schedule(schedule, add_event, target_dict, graz_level, outdir, suffix):
    """Add or remove a grazing event in the target month and year from the
    schedule file used by CENTURY."""
    
    success = 0
    try:
        fh, abs_path = mkstemp()
        with open(abs_path, 'wb') as new_file:
            with open(schedule, 'rb') as sch:
                for line in sch:
                    if 'Last year' in line:
                        year = int(line[:9].strip())
                        if year == int(target_dict['last_year']):
                            # this is the target block
                            new_file.write(line)
                            prev_event_month_count = 0
                            while '-999' not in line:
                                line = sch.next()
                                if 'Labeling type' in line:
                                    new_file.write(line)
                                    break
                                if line[:3] == "   ":
                                    year = int(line[:5].strip())
                                    if year == int(target_dict['target_year']):
                                        month = int(line[7:10].strip())
                                        if add_event:
                                            if month == target_dict['prev_event_month']:
                                                new_file.write(line)
                                                prev_event_month_count += 1
                                                event = line[10:15].strip()
                                                if event not in ['FRST', 'LAST']:
                                                    line = sch.next()
                                                    new_file.write(line)
                                                if prev_event_month_count == target_dict['num_events_prev_month']:
                                                    insertline = '   ' + str(target_dict['target_year']) + '    ' + str(target_dict['target_month']) + ' GRAZ\n'
                                                    new_file.write(insertline)
                                                    new_file.write(graz_level + '\n')
                                                continue
                                        else:
                                            if month == target_dict['target_month']:
                                                if line[10:].strip() == 'GRAZ':
                                                    sch.next()
                                                    continue
                                new_file.write(line)
                            line = sch.next()           
                    new_file.write(line)
    except StopIteration:
        success = 1
    except:
        print "Unexpected error in modify schedule: ", sys.exc_info()[0]        
        raise
    if success:
        # if we successfully modified the schedule
        # save a copy of the modified schedule for future reference
        label = os.path.basename(schedule)[:-4]
        new_sch = os.path.join(outdir, (label + '_' + str(suffix) + '.sch'))
        shutil.copyfile(abs_path, new_sch)
        # replace the schedule used by CENTURY with this modified schedule
        shutil.copyfile(abs_path, schedule)
        return
        
def add_new_graz_level(grass, consumed, graz_file, template_level, outdir,
                       suffix):
    """Add a new graz level to the graz.100 file, taking flgrem (percent live
    biomass removed) and fdgrem (percent standing dead removed) calculated by
    livestock model.  The new level code returned by this function must be added
    to the schedule file to implement this grazing level."""
    
    flgrem_key = ';'.join([grass['label'], 'green'])
    fdgrem_key = ';'.join([grass['label'], 'dead'])
    existing_codes = []
    # make copy of graz.100
    fh, abs_path = mkstemp()
    try:
        template = []
        with open(abs_path, 'wb') as new_file:
            with open(graz_file, 'rb') as old_file:
                for line in old_file:
                    new_file.write(line)
                    if '(orig)' in line or '(added)' in line:
                        existing_codes.append(line[:4].strip())
                    if template_level + '  ' in line:
                        # copy template parameters to template_level
                        line = old_file.next()
                        new_file.write(line)
                        line = old_file.next()
                        new_file.write(line)
                        while 'FECLIG' not in line:
                            line = old_file.next()
                            template.append(line)
                            new_file.write(line)
                        line = old_file.next()
                        new_file.write(line)                        
                newflgrem = '%.5f' % consumed[flgrem_key] + "           'FLGREM'"
                newfdgrem = '%.5f' % consumed[fdgrem_key] + "           'FDGREM'" 
                new_code = ''.join(random.choice(string.ascii_uppercase)
                                   for _ in range(4))
                while new_code in existing_codes:
                    new_code = ''.join(random.choice(string.ascii_uppercase)
                                       for _ in range(4))
                new_file.write(new_code + '     (added)\n')
                new_file.write(newflgrem + '\n')
                new_file.write(newfdgrem + '\n')
                for param in template:
                    new_file.write(param)
    except:
        print "Unexpected error in add new graz level: ", sys.exc_info()[0]        
        raise
    else:
        # if we successfully modified the graz file
        # save a copy of the modified graz params for future reference
        new_graz_params = os.path.join(outdir, 'graz_' + str(suffix) + '.100')
        shutil.copyfile(abs_path, new_graz_params)
        # replace the graz params used by CENTURY with this modified file
        shutil.copyfile(abs_path, graz_file)
        return new_code

def find_prev_month(year, month):
    """Find CENTURY's representation of the month previous to year, month."""
    
    if month == 1:
        prev_month = 12
        year = year - 1
    else:
        prev_month = month - 1
    prev_date = year + float('%.2f' % (prev_month / 12.))
    return prev_date

def convert_to_year_month(CENTURY_date):
    """Convert CENTURY's representation of dates (from output file) to year
    and month.  Returns a list containing integer year and integer month."""
    
    if CENTURY_date - math.floor(CENTURY_date) == 0:
        year = int(CENTURY_date - 1)
        month = 12
    else:
        year = int(math.floor(CENTURY_date))
        month = int(round(12. * (CENTURY_date - year)))
    return [year, month]
        