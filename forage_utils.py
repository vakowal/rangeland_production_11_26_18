"""InVEST Grassland Forage module"""

# Equations (eq) refer to Freer et al. 2012

import os
import sys
import math
from operator import attrgetter
import freer_param as FreerParam

global _time_step
global _time_divisor_dict


def set_time_step(step):
    global _time_step
    _time_step = step


_time_divisor_dict = {
    u'year': 365,
    u'month': 30.4,
    u'week': 7,
    u'day': 1,
}


def find_steps_per_year():

    """This function takes a time step specified as a string (e.g. 'day',
    'week', month') and converts to numerical number of steps to execute
    within a year.

    Returns numerical time step."""

    year_divisor_dict = {
        u'year': 1,
        u'month': 12,
        u'week': 52,
        u'day': 365,
    }
    step_num = year_divisor_dict[_time_step]
    return step_num


def find_days_per_step():
    """This function takes a time step specified as a string (e.g. 'day',
    'week', month') and converts to number of days within the step.

    Returns number of days in a step."""

    days_in_step = _time_divisor_dict[_time_step]
    return days_in_step


def convert_daily_to_step(daily_amount):

    """Converts an amount calculated per day to the equivalent amount in
    one time step of the model.

    Returns the amount per step.
    """

    days_in_step = _time_divisor_dict[_time_step]
    amount_per_step = float(daily_amount) * float(days_in_step)
    return amount_per_step


def convert_step_to_daily(step_amount):

    """Converts an amount calculated per time step to the equivalent amount per
    day.

    Returns the amount per day.
    """

    steps_in_day = 1.0/_time_divisor_dict[_time_step]
    amount_per_day = float(step_amount) * steps_in_day
    return amount_per_day


class HerdT1:

    """Herd class for tier 1 containing attributes and methods characteristic
    of the livestock herd."""

    def __init__(self, weight, f_m_weight):
        self.average_weight_kg = weight
        self.f_mature_weight_kg = f_m_weight

    def e_allocate(self, MJ_per_indiv, maintenance, activity):
        """Allocate energy consumed by herbivores among the herd.
        Energy is first allocated to maintenance and activity, then to growth.

        Modifies the herd, returns nothing.
        """

        act_table = {
            'low': 0.0,
            'moderate': 0.17,  # IPCC 2006 table 10.5
            'high': 0.36,
        }
        Ca = act_table[activity]
        activity = Ca * float(maintenance)  # IPCC equation 10.4
        total = maintenance + activity
        if MJ_per_indiv == total:
            return

        available_for_growth = float(MJ_per_indiv) - total
        if available_for_growth > 0:
            weight_loss = False  # animal gains weight
            abs_available_for_growth = available_for_growth
        else:
            weight_loss = True  # animal loses weight
            abs_available_for_growth = abs(available_for_growth)

        available_for_growth_daily = convert_step_to_daily(
            abs_available_for_growth)
        weight = self.average_weight_kg
        mature_weight = self.f_mature_weight_kg
        weight_change_daily = math.exp((math.log(available_for_growth_daily/(
            22.02 * ((weight/mature_weight) ** 0.75))))/1.097)  # IPCC eq. 10.6
        delta_weight = convert_daily_to_step(weight_change_daily)

        if weight_loss:
            delta_weight = -delta_weight
        return delta_weight

    def e_maintenance(self):
        """Calculate energy required by one animal for maintenance per time step.
        """

        Cfi = 0.322  # IPCC 2006 table 10.4 (steer and non-lactating cows)
        weight = self.average_weight_kg
        NE_m_day = Cfi * weight ** 0.75  # IPCC 2006 eq. 10.3
        maintenance = convert_daily_to_step(NE_m_day)
        return maintenance


class VegT1:

    """Vegetation class for tier 1 containing attributes and methods
    characteristic of the vegetation."""

    def __init__(self, standing, quality):
        self.standing_veg = standing
        self.forage_quality = quality

    def offtake(self, DMI):
        """Remove vegetation selected by grazing herbivores.

        Modifies standing vegetation.
        """

        self.standing_veg -= DMI
        return

    def diet_selection(self, weight, herd_size):
        """Calculate energy intake for the herd, given available vegetation.
        This function also calculates maximum possible intake given availability
        and quality of available vegetation, and removes offtake by the herd
        from standing vegetation. Vegetation quality and intake calculations
        follow IPCC 2006.

        Returns energy intake for the herd, for the time step.
        """

        quality_table = {  # IPCC 2006 table 10.8
            u'grain': 8.,
            u'high': 7.,
            u'moderate': 6.,
            u'low': 4.5,
        }
        MJ_per_kg_DM = quality_table[self.forage_quality]
        indiv_DMI_daily = weight ** 0.75 * ((0.2444 * MJ_per_kg_DM - 0.0111 *
            MJ_per_kg_DM ** 2 - 0.472) / MJ_per_kg_DM)  # kg; IPCC 2006 eq 10.17

        indiv_DMI_step = convert_daily_to_step(indiv_DMI_daily)
        DMI = indiv_DMI_step * float(herd_size)
        diet = DMI * MJ_per_kg_DM
        self.standing_veg -= DMI  # offtake by the herd
        return diet


def calc_energy_t1(forage_quality):
    """Look up energy content of forage given its forage quality, from IPCC 2006
    table 10.8."""

    quality_table = {  # IPCC 2006 table 10.8
        u'grain': 8.,
        u'high': 7.,
        u'moderate': 6.,
        u'low': 4.5,
    }
    MJ_per_kg_DM = quality_table[forage_quality]
    return MJ_per_kg_DM


def calc_DMI_t1(MJ_per_kg_DM, weight):
    """Calculate dry matter intake (for tier 1) given the energy content of food
    available and average animal weight."""

    indiv_DMI_daily = float(weight) ** 0.75 * ((0.2444 * float(MJ_per_kg_DM) -
        0.0111 * float(MJ_per_kg_DM) ** 2. - 0.472) / float(MJ_per_kg_DM))  # IPCC 2006 eq 10.17

    indiv_DMI_step = convert_daily_to_step(indiv_DMI_daily)
    return indiv_DMI_step


class HerbivoreClass:

    """Herbivore class for tier 2 containing attributes and methods
    characteristic of a single herbivore type."""

    def __init__(self, inputs_dict):
        global_SRW = 550.
        global_birth_weight = 34.7
        self.FParam = FreerParam.get_params(inputs_dict['type'])
        self.label = inputs_dict['label']
        self.stocking_density = inputs_dict['stocking_density']  # num animals per ha
        if inputs_dict['birth_weight'] > 0:
            self.Wbirth = inputs_dict['birth_weight']
        else:
            self.Wbirth = global_birth_weight
        if inputs_dict['SRW'] > 0:
            self.SRW = inputs_dict['SRW']
        else:
            self.SRW = global_SRW
        self.SFW = inputs_dict['SFW']
        self.Wprev = inputs_dict['weight']  # arbitrary weight previous to initial weight
        self.W = inputs_dict['weight']
        self.sex = inputs_dict['sex']
        self.type = inputs_dict['type']
        self.A = inputs_dict['age']
        if self.sex == 'entire_m':
            self.SRW = self.SRW * 1.4
        if self.sex == 'castrate':
            self.SRW = self.SRW * 1.2
        if self.sex == 'herd_average':
            self.SRW = (self.SRW*0.6323) + (self.SRW*0.1564) + \
                        (self.SRW*0.3071)
        if self.sex == 'NA':
            self.SRW = (self.SRW + self.SRW * 1.4) / 2
        if self.sex == 'breeding_female':
            self.conception_step = inputs_dict['conception_step']
            self.calving_interval = inputs_dict['calving_interval']
            self.lactation_duration = inputs_dict['lactation_duration']

        self.Nmax = self.SRW - (self.SRW - self.Wbirth) * math.exp(
                    (-self.FParam.CN1 * self.A)/(self.SRW ** self.FParam.CN2))  # maximum body size (kg), eq 1
        self.N = self.FParam.CN3 * self.Nmax + (1. - self.FParam.CN3) \
                     * self.Wprev  # normal weight
        self.Z = self.N / self.SRW  # relative size
        self.Z_abs = self.N / 542.  # absolute size
        self.BC = self.W / self.N  # relative condition
        self.D = -1.
        self.f_w = 0
        self.q_w = 0
        self.reproductive_status = None
        self.A_foet = 0  # days since conception, if pregnant
        self.A_y = 0  # days since birth, if lactating

        # quality and quantity weights
        try:
            if inputs_dict['qual_weight'] is not None:
                self.q_w = inputs_dict['qual_weight']
        except KeyError:
            pass
        try:
            if inputs_dict['quant_weight'] is not None:
                self.f_w = inputs_dict['quant_weight']
        except KeyError:
            pass

        # calibration parameters
        try:
            if inputs_dict['CM2'] is not None:
                self.FParam.CM2 = inputs_dict['CM2']
        except KeyError:
            pass
        try:
            if inputs_dict['CM12'] is not None:
                self.FParam.CM12 = inputs_dict['CM12']
        except KeyError:
            pass
        try:
            if inputs_dict['CK13'] is not None:
                self.FParam.CK13 = inputs_dict['CK13']
        except KeyError:
            pass
        try:
            if inputs_dict['CG2'] is not None:
                self.FParam.CG2 = inputs_dict['CG2']
        except KeyError:
            pass

    def __repr__(self):
        return '{}: prev weight: {} weight: {} BC: {}'.format(
                                                    self.__class__.__name__,
                                                    self.Wprev,
                                                    self.W,
                                                    self.BC)

    def check_BC(self, BC):
        """Check model-calculated relative condition against user-supplied
        relative condition, and if they differ by at least 10%, raise an
        error."""

        difference_BC = self.BC - BC
        if abs(difference_BC) >= (BC * 0.1):
            raise Exception("""Error: supplied relative condition differs from
                 calculated condition by more than 10%. Please edit
                 inputs for standard reference weight, age, weight or estimated
                 relative condition.""")
                 # Supplied relative condition: %f.  Calculated relative
                 # condition: %f. % (BC, calc_BC)

    def update(self, model_step):
        """Update reproductive status, days since conception, days since birth,
        and weight including conceptus.

        Parameters:
            model step (int): timestep of the model relative to beginning month

        Modifies:
            reproductive status, age of young, time since conception, and
                weight of the herbivore class if it is breeding female sex

        Returns:
            None
        """
        if self.sex == 'breeding_female':
            months_of_pregnancy = 9
            cycle_month_index = (
                (model_step - self.conception_step) % self.calving_interval)
            if cycle_month_index < months_of_pregnancy:
                self.reproductive_status = 'pregnant'
                self.A_foet = cycle_month_index * 30 + 1
                RA = self.A_foet / self.FParam.CP1
                BW = (
                    (1 - self.FParam.CP4 + self.FParam.CP4 *
                        self.Z) * self.FParam.CP15 * self.SRW)
                W_c_1 = self.FParam.CP5 * BW
                W_c_2 = math.exp(
                    self.FParam.CP6 *
                    (1 - math.exp(self.FParam.CP7 * (1 - RA))))
                W_c = W_c_1 * W_c_2  # equation 62, weight of conceptus
                self.W = self.Wprev + W_c
            elif (cycle_month_index <
                    (months_of_pregnancy + self.lactation_duration)):
                self.reproductive_status = 'lactating'
                self.W = self.Wprev
                self.A_y = (cycle_month_index - months_of_pregnancy) * 30 + 1
            else:  # not pregnant or lactating
                self.reproductive_status = None
                self.W = self.Wprev
                self.A_foet = 0
                self.A_y = 0

    def calc_max_intake(self):
        """Calculate the maximum potential daily intake of dry matter (kg) from
        size and condition of the animal.  Note that max intake may be modified
        after diet selection if the diet is very low in protein.

        Returns maximum kg dry matter intake per day."""

        if self.W <= self.Wbirth:
            return 0
        if self.BC > 1.:
            CF = self.BC * (self.FParam.CI20 - self.BC)/(self.FParam.CI20 - 1.)
        else:
            CF = 1.
        YF = 1.  # eq 4 gives a different value for unweaned animals
        TF = 1.  # ignore effect of temperature on intake
        if self.reproductive_status == 'lactating':
            BCpart = self.BC  # assumed body condition at parturition
            Mi = self.A_y / self.FParam.CI8
            LA = 1. - self.FParam.CI15 + self.FParam.CI15 * BCpart
            LF = 1. + self.FParam.CI19 * Mi ** self.FParam.CI9 * math.exp(
                                          self.FParam.CI9 * (1 - Mi)) * LA
        else:
            LF = 1.  # assume any lactating animals are suckling young (eq 8)
        max_intake = (self.FParam.CI1 * self.SRW * self.Z * (self.FParam.CI2 -
                      self.Z) * CF * YF * TF * LF)  # eq 2
        return max_intake

    def calc_distance_walked(self, steepness, stocking_density,
                             available_forage):
        """Calculate distance walked per day by livestock, following Freer et
        al. 2012 equation 44a."""

        self.D = 4  # constant, somewhat arbtirary, value
        return      # because I believe this was having a huge undue effect
                    # on simulation results
        if stocking_density == 0:
            return
        Bgreen = 0.
        Bdead = 0.
        for feed_type in available_forage:
            if feed_type.green_or_dead == 'green':
                Bgreen += feed_type.biomass
            elif feed_type.green_or_dead == 'dead':
                Bdead += feed_type.biomass
            else:
                raise ValueError
        if Bgreen > 100:
            self.D = (steepness * min(1., self.FParam.CM17 / stocking_density)/
                     (self.FParam.CM8 * Bgreen + self.FParam.CM9))
        elif Bgreen < 100 and Bdead > 100:
            self.D = (steepness * min(1., self.FParam.CM17 / stocking_density)/
                     (self.FParam.CM8 * Bdead + self.FParam.CM9))
        else:
            self.D = 0.

    def calc_milk_yield(self, milk_production):
        """Calculate kg milk produced per day per lactating female."""

        milk_kg_per_day = milk_production / (self.FParam.CL5 * self.FParam.CL6)
        return milk_kg_per_day

    def calc_ZF(self):
        if self.Z_abs < self.FParam.CR7:
            return 1. + (self.FParam.CR7 - self.Z_abs)
        else:
            return 1.


class SiteInfo:

    """This class holds information about the physical site."""

    def __init__(self, steepness, latitude):
        self.S = steepness  # between 1 and 2
        self.latitude = latitude


class Supplement:

    """This class holds information about the supplement."""

    def __init__(self, FParam, digestibility, kg_per_day, M_per_d,
                 ether_extract, crude_protein, rumen_degradability):

        self.DMD = digestibility  # digestibility of supplement
        self.DMO = kg_per_day  # kg supplement offered, per individual, per day
        self.M_per_D = M_per_d  # ratio metabolizable energy to dry matter
        self.EE = ether_extract  # ether extract of supplement
        self.CP = crude_protein  # crude protein concentration of supplement
        self.dg = rumen_degradability  # rumen degradability of crude protein of supplement
        self.RQ = 1. - min(FParam.CR14, (FParam.CR3 * (FParam.CR1 - self.DMD)))  # eq 26


class FeedType:

    """This class holds a description of a forage type distinguished by the
    amount of it in the pasture (biomass) and its digestibility (varying
    between 0 and 1).  There should be separate feed types for green and dead
    forage of the same grass type, because those have different digestibility.

    There is structure here for separating seeds from  herbaceous biomass,
    while the 'biomass' attribute refers to total biomass including both seeds
    and herbaceous."""

    def __init__(self, label, green_or_dead, biomass, digestibility,
                 crude_protein, type):
        self.label = label
        self.green_or_dead = green_or_dead
        self.biomass = biomass  # kg DM per ha: seeds and herbaceous combined
        self.biomass_avail = 0.  # biomass available to herbivores, kg/ha
        self.digestibility = digestibility  # 0 - 1
        self.crude_protein = crude_protein  # 0 - 1
        if type == 'C3':
            self.SF = 0.
        elif type == 'C4':
            self.SF = 0.16
        else:
            er = "Error: grass must be specified as type C3 or C4"
            raise Exception(er)
        self.rel_availability = 0.

    def __repr__(self):
        return '{}: {} {}, biomass: {} digestibility: {} cr protein {}'.format(self.__class__.__name__,
                                                    self.label,
                                                    self.green_or_dead,
                                                    self.biomass,
                                                    self.digestibility,
                                                    self.crude_protein)

    def calc_digestibility_from_protein(self, flag=None):
        """Use equations published in Illius et al. 1995 to calculate dry matter
        digestibility from crude protein concentration.  Note that these
        equations were developed for African perennial grasses."""

        if flag is None:  # use regression from Illius et al. 1995
            if self.green_or_dead == 'green':
                self.digestibility = (
                    ((self.crude_protein * 100 / 6.25) + 1.07) / 0.053) / 100
            else:
                self.digestibility = (
                    ((self.crude_protein * 100 / 6.25) + 0.77) / 0.034) / 100
        elif flag == 'CPER':  # derived from data in Rodriguez Roath 1987
            self.digestibility = (
                    ((self.crude_protein * 100) * 1.5349) + 41.47) / 100
        elif flag == 'Konza':  # derived from data in Hobbs et al. 1991
            self.digestibility = (
                    ((self.crude_protein * 100) * 2.2879) + 31.52) / 100
        else:
            raise Exception("Error: unknown flag value {}".format(flag))


class Diet:

    """This class holds info about the diet selected by an herbivore that is
    later used to allocate energy to growth.  This should be all the information
    that is needed to describe the diet selected (i.e., the product of diet
    selection)."""

    def __init__(self):
        self.If = 0.  # intake of forage, including seeds (kg)
        self.Is = 0.  # intake of supplement (kg)
        self.DMDf = 0.  # dry matter digestibility of forage (0 - 1)
        self.CPIf = 0.  # crude protein intake from forage
        self.intake = {}  # intake of each forage type

    def __repr__(self):
        return 'If: {} Is: {} DMDf: {} CPIf: {} intake: {}'.format(self.If,
                                                                   self.Is,
                                                                   self.DMDf,
                                                                   self.CPIf,
                                                                   self.intake)

    def fill_intake_zero(self, available_forage):
        for feed_type in available_forage:
            label_string = ';'.join([feed_type.label, feed_type.green_or_dead])
            self.intake[label_string] = 0


class DietIntermediates:

    """This class holds intermediate quantities calculated from the diet,
    including total energy and protein intake (MEItotal and RDPLS), energy and
    protein required for maintenance, pregnancy, lactation, and wool growth.
    Also includes the intermediate values necessary to restrict maximum intake
    due to low protein content of the diet."""

    def __init__(self):
        self.RDPIs = -1.
        self.RDPIf = -1.
        self.RDPR = -1.
        self.L = -1.
        self.MEItotal = 0.  # total metabolizable energy intake
        self.MEm = 0.  # energy required for maintenance
        self.MEc = 0.  # energy required for pregnancy
        self.MEl = 0.  # energy required for lactation
        self.NEw = 0.  # energy required for wool growth
        self.DPLS = 0.  # digestible protein leaving the stomach
        self.Pm = 0.  # protein required for maintenance
        self.Pc = 0.  # protein required for pregnancy
        self.Pl = 0.  # protein required for lactation
        self.Pw = 0.  # protein required for wool growth


def diet_selection_t2(ZF, HR, prop_legume, supp_available, Imax, FParam,
                      available_forage, f_w=0, q_w=0, force_supp=None,
                      supp=None):
    """Perform diet selection for an individual herbivore, tier 2.  This
    function calculates relative availability, F (including factors like
    pasture height and animal mouth size) and relative ingestibility, RQ
    (including factors like pasture digestibility and proportion legume in the
    sward) to select a preferred mixture of forage types, including supplement
    if offered.  Available forage must be supplied to the function in an
    ordered list such that available_forage[0] is of highest digestibility.

    Returns daily intake of forage (kg; including seeds), daily intake of
    supplement (kg), average dry matter digestibility of forage, and average
    crude protein intake from forage."""

    available_forage = sorted(available_forage, reverse=True,
                              key=attrgetter('digestibility'))
    diet_selected = Diet()
    if Imax == 0:
        for f_index in range(len(available_forage)):
            f_label = available_forage[f_index].label + ';' +\
                        available_forage[f_index].green_or_dead
            diet_selected.intake[f_label] = 0.
        return diet_selected

    F = list()
    RR = list()
    RT = list()
    HF = list()
    RQ = list()
    R = list()
    R_w = list()
    I = list()
    sum_prev_classes = 0.
    UC = 1.
    supp_selected = 0

    for f_index in range(len(available_forage)):
        RQ.append(1. - FParam.CR3 * (FParam.CR1 - (1. - prop_legume)  # eq 21
                  * available_forage[f_index].SF -
                  available_forage[f_index].digestibility))
        if supp_available:
            if RQ[f_index] <= supp.RQ or force_supp:
                supp_selected = 1
                supp_available = 0
                Fs = min((supp.DMO / Imax) / supp.RQ, UC, FParam.CR11 /
                          supp.M_per_D)  # eq 23
                sum_prev_classes += Fs
                UC = max(0., 1. - sum_prev_classes)
        HF.append(1. - FParam.CR12 + FParam.CR12 * HR[f_index])  # eq 18
        RT.append(1. + FParam.CR5 * math.exp(-(1. + FParam.CR13 *  # eq 17
            available_forage[f_index].rel_availability) *
            (FParam.CR6 * HF[f_index] * ZF * available_forage[f_index].biomass)
            ** 2))
        RR.append(1. - math.exp(-(1. + FParam.CR13 *  # eq 16
            available_forage[f_index].rel_availability) * FParam.CR4 *
            HF[f_index] * ZF * available_forage[f_index].biomass))
        F.append(UC * RR[f_index] * RT[f_index])  # eq 14
        sum_prev_classes += F[f_index]
        UC = max(0., 1. - sum_prev_classes)  # eq 15
    for f_index in range(len(available_forage)):
        # original GRAZPLAN formulation
        R.append(F[f_index] * RQ[f_index] * (1. + FParam.CR2 * sum_prev_classes
                ** 2 * prop_legume))  # eq 20
        # weight proportional intake by quantity weight and quality weight
        R_w.append(R[f_index] + F[f_index]*f_w + RQ[f_index]*q_w)
    # rescale weighted proportions to retain original sum of R
    sum_Rw = sum(R_w)
    for f_index in range(len(available_forage)):
        R_w[f_index] = (R_w[f_index] / sum_Rw) * sum(R)
    # Imax = 11.8 / sum(R_w)  # forcing intake of one Animal Unit, Ucross
    for f_index in range(len(available_forage)):
        I.append(Imax * R_w[f_index])  # eq 27
        diet_selected.DMDf += (I[f_index] *
                               available_forage[f_index].digestibility)
        diet_selected.CPIf += (I[f_index] *
                               available_forage[f_index].crude_protein)
        diet_selected.If += I[f_index]

        # stash the amount consumed of each forage type
        f_label = '{};{}'.format(available_forage[f_index].label,
                                 available_forage[f_index].green_or_dead)
        diet_selected.intake[f_label] = I[f_index]
    diet_selected.DMDf = diet_selected.DMDf / diet_selected.If
    if supp_selected:
        Rs = Fs * supp.RQ  # eq 25
        diet_selected.Is = Imax * Rs  # eq 30
    return diet_selected


def calc_total_biomass(available_forage):
    """Calculate the total biomass across forage types, in kg per ha."""

    sum_biomass = 0.
    for feed_type in available_forage:
        sum_biomass += feed_type.biomass
    return sum_biomass


def calc_relative_height(available_forage):
    """Calculate the relative height of each forage type, as described by Freer
    et al 2012, p. 34 (equations 134 and 135 generalized to an arbitrary number
    of forage classes)."""

    num = 0.
    denom = 0.
    for feed_type in available_forage:
        num = num + feed_type.biomass
        denom = denom + (feed_type.biomass)**2
    num = num**2
    scale_term = num / denom

    rel_height = []
    for feed_type in available_forage:
        height = 0.003 * scale_term * feed_type.biomass
        rel_height.append(height)
    return rel_height


def reduce_demand(diet_dict, stocking_density_dict, available_forage):
    """Check whether demand is greater than available biomass for each forage
    type. If it is, reduce intake of that forage type for each herbivore type
    according to its proportion of total demand for that forage type."""

    for feed_type in available_forage:
        label_string = '{};{}'.format(feed_type.label,
                                      feed_type.green_or_dead)
        available = feed_type.biomass_avail
        demand = 0.
        indiv_demand_dict = {}
        for hclass_label in diet_dict.keys():
            sd = stocking_density_dict[hclass_label]
            intake_step = convert_daily_to_step(
                             diet_dict[hclass_label].intake[label_string]) * sd
            indiv_demand_dict[hclass_label] = intake_step
            demand += intake_step
        if demand > available:
            for hclass_label in diet_dict.keys():
                sd = stocking_density_dict[hclass_label]
                intake_step = available * (indiv_demand_dict[hclass_label] /
                                           demand)
                try:
                    intake_daily = convert_step_to_daily(intake_step) / sd
                except ZeroDivisionError:
                    intake_daily = 0
                diet_dict[hclass_label].intake[label_string] = intake_daily

    # recalculate all other quantities in diet
    for hclass_label in diet_dict.keys():
        diet_dict[hclass_label].If = 0.
        diet_dict[hclass_label].DMDf = 0.
        diet_dict[hclass_label].CPIf = 0.
        for feed_type in available_forage:
            label_string = '{};{}'.format(feed_type.label,
                                          feed_type.green_or_dead)
            intake_daily = diet_dict[hclass_label].intake[label_string]
            diet_dict[hclass_label].If += intake_daily
            diet_dict[hclass_label].DMDf += (intake_daily *
                                             feed_type.digestibility)
            diet_dict[hclass_label].CPIf += (intake_daily *
                                             feed_type.crude_protein)
        if diet_dict[hclass_label].If > 0:
            diet_dict[hclass_label].DMDf = (diet_dict[hclass_label].DMDf /
                                            diet_dict[hclass_label].If)


def calc_total_intake(diet_dict, stocking_density_dict):
    """Calculate total intake of forage across grass and herbivore types."""

    total_intake = 0.
    for hclass_label in diet_dict.keys():
        sd = stocking_density_dict[hclass_label]
        total_intake += convert_daily_to_step(diet_dict[hclass_label].If) * sd
    return total_intake


def calc_percent_consumed(available_forage, diet_dict, stocking_density_dict):
    """Calculate percent of each forage type consumed through diet selection.
    This proportion is sent back to CENTURY as grazing intensity, in the form
    of the parameters flgrem (percent live biomass removed) and fdgrem (percent
    standing dead biomass removed)."""

    consumed_dict = {}
    for feed_type in available_forage:
        label_string = ';'.join([feed_type.label, feed_type.green_or_dead])
        if feed_type.biomass == 0:
            perc_removed = 0
        else:
            consumed = 0.
            for hclass_label in diet_dict.keys():
                sd = stocking_density_dict[hclass_label]
                try:
                    consumed += (convert_daily_to_step(
                                            diet_dict[hclass_label].intake[
                                            label_string]) * sd)
                except KeyError:
                    continue
            perc_removed = float(consumed) / feed_type.biomass
        consumed_dict[label_string] = perc_removed
    return consumed_dict


def restrict_available_forage(available_forage, management_threshold):
    """Reduce forage available for grazing.

    The management threshold specifies the biomass that must be left
    after herbivore offtake. Calculate the forage available for offtake by
    herbivores according to its relative availability, restricting it to be
    below the management threshold if necessary.

    Parameters:
        available_forage (list): list of class FeedType, where each FeedType
            is characterized by its standing biomass and biomass available
            to herbivores for offtake
        management_threshold (float): biomass (kg/ha) required to be left
            standing after offtake by herbivores

    Returns:
        modified available_forage, a list of class FeedType
    """
    sum_biomass = 0.
    for feed_type in available_forage:
        sum_biomass += feed_type.biomass

    actually_available = max(sum_biomass - management_threshold, 0)
    for feed_type in available_forage:
        feed_type.biomass_avail = (
            feed_type.rel_availability * actually_available)
    return available_forage


def update_feed_types(grass_list, available_forage):
    """Calculate percent growth from previous and current CENTURY outputs, use
    this to update biomass and relative availability in terms of simulation
    units (kg/ha)."""

    matched_g = []
    matched_d = []
    sum_biomass = 0.
    for grass in grass_list:
        perc_grow_g = (grass['green_gm2'] - grass['prev_g_gm2']) / grass['prev_g_gm2']
        perc_grow_d = (grass['dead_gm2'] - grass['prev_d_gm2']) / grass['prev_d_gm2']

        for feed_type in available_forage:
            if feed_type.label == grass['label']:
                if feed_type.green_or_dead == 'green':
                    feed_type.biomass = feed_type.biomass + (perc_grow_g *
                                        feed_type.biomass)
                    feed_type.crude_protein = grass['cprotein_green']
                    matched_g.append(feed_type.label)
                elif feed_type.green_or_dead == 'dead':
                    feed_type.biomass = feed_type.biomass + (perc_grow_d *
                                        feed_type.biomass)
                    feed_type.crude_protein = grass['cprotein_dead']
                    matched_d.append(feed_type.label)
                else:
                    er = "Error: 'green' or 'dead' expected"
                    print er
                    sys.exit(er)
            sum_biomass += feed_type.biomass
        if grass['label'] not in matched_g:
            er = "Error: grass type not found in live biomass list"
            print er
            sys.exit(er)
        if grass['label'] not in matched_d:
            er = "Error: grass type not found in dead biomass list"
            print er
            sys.exit(er)
    for feed_type in available_forage:
        feed_type.rel_availability = feed_type.biomass / sum_biomass
    return available_forage


def calc_feed_types(grass_list):
    """Calculate initial available forage classes subject to diet selection,
    from grass output from CENTURY and user-defined percent initial biomass of
    each grass type.  Here we also convert biomass from the units of CENTURY
    (g per square m) to the units of the livestock model (kg per ha)."""

    forage = []
    sum_biomass = 0.
    # find total biomass: weighted average of biomass of each grass type
    for grass in grass_list:
        # strict conversion: g/m2 to kg/ha
        kg_ha = (grass['green_gm2'] + grass['dead_gm2']) * 10.
        sum_biomass += (kg_ha * grass['percent_biomass'])

    # biomass of each grass type: percent of total biomass
    for grass in grass_list:
        total_type_biomass = grass['percent_biomass'] * sum_biomass
        percent_green = float(grass['green_gm2']) / (grass['green_gm2'] +
                              grass['dead_gm2'])
        green_kg_ha = percent_green * total_type_biomass
        dead_kg_ha = (1. - percent_green) * total_type_biomass

        forage.append(FeedType(grass['label'], 'green', green_kg_ha,
                      grass['DMD_green'], grass['cprotein_green'],
                      grass['type']))
        forage.append(FeedType(grass['label'], 'dead', dead_kg_ha,
                      grass['DMD_dead'], grass['cprotein_dead'],
                      grass['type']))
    for feed_type in forage:
        feed_type.rel_availability = feed_type.biomass / sum_biomass
    return forage


def calc_diet_intermediates(diet, herb_class, prop_legume,
                            DOY, site=None, supp=None):
    """This mess is necessary to calculate intermediate values that are used
    to check whether there is sufficient protein in the diet (if not, max intake
    is reduced: done with check_max_intake), to check if milk production must be
    reduced (check_milk_production) and to allocate energy and protein to
    maintenance, lactation and growth (calc_delta_weight).  All equations and
    variable names taken directly from Freer et al 2012.

    Returns an object of class DietIntermediates which is a container to hold
    the relevant values later used as input to check_max_intake,
    check_milk_production, calc_milk_yield and calc_delta_weight."""

    if supp is None:
        supp = Supplement(FreerParam.FreerParamCattle('indicus'),
                          0, 0, 0, 0, 0, 0)
    if site is None:
        site = SiteInfo(1, 0)
    diet_interm = DietIntermediates()
    # if diet.If == 0. and diet.Is == 0.:
        # return diet_interm

    MEIf = (17.0 * diet.DMDf - 2) * diet.If  # eq 31: herbage
    MEIs = (13.3 * supp.DMD + 23.4 * supp.EE + 1.32) * diet.Is  # eq 32
    FMEIs = (13.3 * supp.DMD + 1.32) * diet.Is  # eq 32, supp.EE = 0
    MEItotal = MEIf + MEIs  # assuming no intake of milk
    try:
        M_per_Dforage = MEIf / diet.If
    except ZeroDivisionError:
        M_per_Dforage = 0
    kl = herb_class.FParam.CK5 + herb_class.FParam.CK6 * M_per_Dforage  # eq 34
    km = (herb_class.FParam.CK1 + herb_class.FParam.CK2 * M_per_Dforage)  # eq 33 efficiency of energy use for maintenance
    Emove = herb_class.FParam.CM16 * herb_class.D * herb_class.W
    Egraze = herb_class.FParam.CM6 * herb_class.W * diet.If * \
             (herb_class.FParam.CM7 - diet.DMDf) + Emove
    Emetab = herb_class.FParam.CM2 * herb_class.W ** 0.75 * max(math.exp(
             -herb_class.FParam.CM3 * herb_class.A), herb_class.FParam.CM4)
    # eq 41, energy req for maintenance:
    MEm = (Emetab + Egraze) / km + herb_class.FParam.CM1 * MEItotal
    if herb_class.sex == 'castrate' or herb_class.sex == 'entire_m':
        MEm = MEm * 1.15
    if herb_class.sex == 'herd_average':
        MEm = MEm * 1.055
    if herb_class.sex == 'NA':
        MEm = (MEm + MEm * 1.15) / 2
    diet_interm.L = (MEItotal / MEm) - 1.

    MEc = 0.
    Pc = 0.
    if herb_class.reproductive_status == 'pregnant':
        RA = herb_class.A_foet / herb_class.FParam.CP1
        BW = (
            (1 - herb_class.FParam.CP4 + herb_class.FParam.CP4 *
            herb_class.Z) * herb_class.FParam.CP15 * herb_class.SRW)
        BC_foet = 1  # assume condition of foetus is 1, ignoring weight
        # assume she is pregnant with one foetus
        MEc_num1 = (
            herb_class.FParam.CP8 * (herb_class.FParam.CP5 * BW) * BC_foet)
        MEc_num2 = (
            (herb_class.FParam.CP9 * herb_class.FParam.CP10) /
            herb_class.FParam.CP1)
        MEc_num3 = math.exp(
            herb_class.FParam.CP10 * (1 - RA) + herb_class.FParam.CP9 *
            (1 - math.exp(herb_class.FParam.CP10*(1 - RA))))
        MEc = (MEc_num1 * MEc_num2 * MEc_num3) / herb_class.FParam.CK8

        Pc_1 = herb_class.FParam.CP11 * (herb_class.FParam.CP5 * BW) * BC_foet
        Pc_2 = (
            (herb_class.FParam.CP12 * herb_class.FParam.CP13) /
            herb_class.FParam.CP1)
        Pc_3 = herb_class.FParam.CP13 * (1 - RA)
        Pc_4 = (
            herb_class.FParam.CP12 *
            (1 - math.exp(herb_class.FParam.CP13 * (1 - RA))))
        Pc_5 = math.exp(Pc_3 + Pc_4)
        Pc = Pc_1 * Pc_2 * Pc_5
    MEl = 0.
    Pl = 0.
    if herb_class.reproductive_status == 'lactating':
        BCpart = herb_class.BC  # assumed body condition at parturition
        Mm = (herb_class.A_y + herb_class.FParam.CL1) / herb_class.FParam.CL2

        MPmax_1 = herb_class.FParam.CL0 * herb_class.SRW ** 0.75 * herb_class.Z
        MPmax_2 = BCpart * Mm ** herb_class.FParam.CL3
        MPmax_3 = math.exp(herb_class.FParam.CL3 * (1 - Mm))
        MPmax = MPmax_1 * MPmax_2 * MPmax_3  # eq 66, with suckling young

        MEl = MPmax / herb_class.FParam.CL5 * kl
        Pl = herb_class.FParam.CL15 * (MPmax / herb_class.FParam.CL6)

    # eq 46, protein req for maintenance:
    if herb_class.type in ['B_indicus', 'B_taurus', 'indicus_x_taurus',
                           'hindgut_fermenter']:
        Pm = (herb_class.FParam.CM12 * math.log(herb_class.W) -
              herb_class.FParam.CM13 + herb_class.FParam.CM10 * (diet.If +
              diet.Is) + herb_class.FParam.CM14 * herb_class.W ** 0.75)
    else:
        Pm = (herb_class.FParam.CM12 * herb_class.W + herb_class.FParam.CM13 +
              herb_class.FParam.CM10 * (diet.If + diet.Is))
    RF = 1. + herb_class.FParam.CRD7 * (site.latitude / 40.) * math.sin((2. *
              math.pi * DOY) / 365.)  # eq 52
    diet_interm.RDPR = (herb_class.FParam.CRD4 + herb_class.FParam.CRD5 * (1. -
                        math.exp(-herb_class.FParam.CRD6 * (diet_interm.L +
                        1.)))) * (RF * MEIf + FMEIs)  # eq 51
    diet_interm.RDPIs = supp.CP * supp.dg * diet.Is
    diet_interm.RDPIf = diet.CPIf * min(0.84 * diet.DMDf + 0.33, 1.)
    UDPI = (diet.Is * supp.CP - diet_interm.RDPIs) + (diet.CPIf -
            diet_interm.RDPIf)  # rumen undegradable protein
    Dudp = max(herb_class.FParam.CA1, min(herb_class.FParam.CA3 * diet.CPIf -
               herb_class.FParam.CA4, herb_class.FParam.CA2))
    DPLSmcp = herb_class.FParam.CA6 * herb_class.FParam.CA7 * diet_interm.RDPR
    diet_interm.DPLS = Dudp * UDPI + DPLSmcp  # eq 53: digestible protein leaving the stomach
    Pw = 0.
    NEw = 0.
    if herb_class.type in ['sheep', 'camelid']:
        AF = herb_class.FParam.CW5 + (1-herb_class.FParam.CW5)*(1-math.exp(
                                         -herb_class.FParam.CW12*herb_class.A))
        DLF = 1 + herb_class.FParam.CW6  # assume day length = 12
        DPLSw = max(0., diet_interm.DPLS - herb_class.FParam.CW9*diet_interm.Pl)
        MEw = max(0., MEItotal - (MEl + MEc))
        Pw = min(herb_class.FParam.CW7*(herb_class.SFW/herb_class.SRW)*AF*DLF*\
                 DPLSw, herb_class.FParam.CW8*(herb_class.SFW/herb_class.SRW)*\
                 AF*DLF*MEw)  # eq 77: protein req for wool
        NEw = (herb_class.FParam.CW1*(Pw-herb_class.FParam.CW2 * herb_class.Z)/
               herb_class.FParam.CW3)  # eq 81: energy req for wool
    diet_interm.MEm = MEm
    diet_interm.MEc = MEc
    diet_interm.MEl = MEl
    diet_interm.NEw = NEw
    diet_interm.Pm = Pm
    diet_interm.Pl = Pl
    diet_interm.Pc = Pc
    diet_interm.Pw = Pw
    diet_interm.MEItotal = MEItotal
    return diet_interm


def calc_delta_weight(diet_interm, herb_class):
    """Calculate weight gain or loss from the diet selected by a herbivore
    class.  Energy is first allocated to maintenance, then to growth.  This
    function ignores energy and protein costs of pregnancy, wool growth, and
    chilling. Also ignored is the potential nutrition gained from milk.

    Returns the change in weight (kg) in one day."""

    if diet_interm.MEItotal == 0.:
        return 0
    NEg = diet_interm.NEg1 + herb_class.FParam.CG12 * diet_interm.EVG * (min(
          0., diet_interm.Pnet) / diet_interm.PCG)
    EBG = NEg / diet_interm.EVG
    if NEg < 0 and diet_interm.EVG < 0:
        # in this boundary condition, intake is very low relative to
        # requirements and body condition is very poor, and yet delta_W is
        # calculated to be very large positive. We force starvation instead.
        delta_W = -(convert_step_to_daily(herb_class.W))
    else:
        delta_W = herb_class.FParam.CG13 * EBG  # eq 117, kg
    return delta_W


def check_max_intake(diet, diet_interm, herb_class, max_intake):
    """Modify the maximum intake possible, given characteristics of the diet
    selected.  Because diet selection takes maximum intake as an argument,
    calculation of max intake is an interative process (iterated a maximum of
    two times).

    Returns maximum intake given characteristics of the selected diet."""

    if max_intake == 0:
        return 0
    if diet_interm.L > 0:
        RDPI = (diet_interm.RDPIf * (1. - (herb_class.FParam.CRD1 -
                herb_class.FParam.CRD2 * diet.DMDf) * diet_interm.L) +
                diet_interm.RDPIs * (1. - herb_class.FParam.CRD3 *
                diet_interm.L))
    else:
        RDPI = diet_interm.RDPIf + diet_interm.RDPIs
    if diet_interm.RDPR > RDPI:
        if herb_class.type == 'B_taurus':  # TODO camelids?
            reduction_factor = RDPI / diet_interm.RDPR
        elif herb_class.type == 'B_indicus':
            reduction_factor = 1 - ((1 - (RDPI / diet_interm.RDPR)) * 0.5)
        else:
            reduction_factor = 1 - ((1 - (RDPI / diet_interm.RDPR)) * 0.75)
        max_intake = max_intake * reduction_factor
    return max_intake


def check_milk_production(FParam, diet_interm):
    """Check to see if protein in the diet is sufficient to support predicted
    milk production before allocating energy and protein to weight gain.  If
    protein is low, milk production is lowered before allocating weight gain.

    Modifies values in diet_interm and returns modified milk production."""

    if diet_interm.L == -1.:
        return 0
    MP = (1. + min(0., diet_interm.Pnet / diet_interm.Pl)) * diet_interm.MP2  # eq 110
    if MP != diet_interm.MP2:
        print "Recalculated MP differs from original"
    NEg2 = diet_interm.NEg1 + FParam.CL5 * (diet_interm.MP2 - MP)  # eq 111
    Pg2 = diet_interm.Pg1 + (diet_interm.MP2 - MP) * (FParam.CL15 / FParam.CL6)  # eq 112
    Pnet2 = Pg2 - diet_interm.PCG * (NEg2 / diet_interm.EVG)  # eq 113
    diet_interm.Pl = FParam.CL15 * (MP / FParam.CL6)  # eq 76
    diet_interm.NEg1 = NEg2
    diet_interm.Pnet = Pnet2
    return MP

def check_initial_biomass(grass_list):
    """Check that initial percent biomass supplied by user adds to 1."""

    total_perc_biomass = 0.
    for grass in grass_list:
        total_perc_biomass += grass['percent_biomass']
    if total_perc_biomass < 1.:
        raise ValueError("Initial percent biomass adds to less than 1")


def one_step(site, DOY, herb_class, available_forage, prop_legume,
             supp_available, supp, intake=None, force_supp=None):
    """One step of the forage model, with one herbivore type, if available
    forage does not change."""

    row = []
    herb_class.calc_distance_walked(site.S, herb_class.stocking_density,
                                    available_forage)
    max_intake = herb_class.calc_max_intake()

    ZF = herb_class.calc_ZF()
    HR = calc_relative_height(available_forage)
    if intake is not None:  # if forage intake should be forced
        diet = Diet()
        diet.If = intake
        diet.DMDf = available_forage[0].digestibility  # this is super hack-y
        diet.CPIf = intake * available_forage[0].crude_protein  # and only works with one type of available forage
        diet.Is = supp.DMO  # also force intake of all supplement offered
        diet_interm = calc_diet_intermediates(diet, supp, herb_class,
                                              site, prop_legume, DOY)
    else:
        diet = diet_selection_t2(ZF, HR, prop_legume, supp_available,
                                 max_intake, herb_class.FParam,
                                 available_forage, supp=supp)
        diet_interm = calc_diet_intermediates(diet, herb_class, prop_legume,
                                              DOY, site, supp=supp)
        if herb_class.type != 'hindgut_fermenter':
            reduced_max_intake = check_max_intake(diet, diet_interm,
                                                  herb_class, max_intake)
            row.append(reduced_max_intake)
            if reduced_max_intake < max_intake:
                diet = diet_selection_t2(ZF, HR, prop_legume, supp_available,
                                         reduced_max_intake, herb_class.FParam,
                                         available_forage, supp=supp)
                diet_interm = calc_diet_intermediates(diet, herb_class,
                                                      prop_legume, DOY, site,
                                                      supp=supp)
    delta_W = calc_delta_weight(diet_interm, herb_class)
    delta_W_step = convert_daily_to_step(delta_W)
    herb_class.update(delta_weight=delta_W_step,
                      delta_time=find_days_per_step())

    row.append(max_intake)
    row.append(diet.If)
    row.append(diet.Is)
    row.append(delta_W)
    return row


def calc_total_stocking_density(herbivore_list):
    """Calculate the total stocking density of herbivores, including multiple
    classes."""

    stocking_density = 0
    for herb_class in herbivore_list:
        stocking_density += herb_class.stocking_density
    return stocking_density


def populate_sd_dict(herbivore_list):
    """Create and populate the stocking density dictionary, giving the stocking
    density of each herbivore type."""

    stocking_density_dict = {}
    for herb_class in herbivore_list:
        stocking_density_dict[herb_class.label] = herb_class.stocking_density
    return stocking_density_dict


def fill_dict(d_fill, fill_val):
    """Fill a dictionary with fill_val so that it can be converted to a pandas
    data frame and written to csv."""

    max_len = 0
    for key in d_fill.keys():
        if len(d_fill[key]) > max_len:
            max_len = len(d_fill[key])
    for key in d_fill.keys():
        if len(d_fill[key]) < max_len:
            for diff_val in xrange(max_len - len(d_fill[key])):
                d_fill[key].append(fill_val)
    return d_fill


def write_inputs_log(args, now_str):
    """Write model inputs to a text file."""

    save_as = os.path.join(args['outdir'], "forage-log-%s.txt" % now_str)
    with open(save_as, 'w') as new_file:
        new_file.write("Rangeland production model launched %s\n" % now_str)
        new_file.write("\n\n")
        new_file.write("____________________________________\n")
        new_file.write("Arguments\n")
        new_file.write("____________________________________\n")
        for key in args.keys():
            new_file.write('%s: %s\n' % (key, args[key]))


def calc_diet_segregation(diet_dict):
    """Calculate the segregation between diets of two herbivores. This is
    calculated as the average difference in percentage of the diet comprised of
    each forage type.  So a value of 1 means they eat completely separate grass
    types. A value of 0 means they select grass types in identical
    proportions."""

    if len(diet_dict.keys()) < 2:
        return 0
    perc_lists = []
    for hclass_label in diet_dict.keys():
        percent_consumed = []
        total_consumed = 0.
        for grass_label in diet_dict[hclass_label].intake.keys():
            total_consumed = total_consumed + \
                                    diet_dict[hclass_label].intake[grass_label]
        for grass_label in diet_dict[hclass_label].intake.keys():
            percent_consumed.append(
                    diet_dict[hclass_label].intake[grass_label]/total_consumed)
        perc_lists.append(percent_consumed)
    assert len(perc_lists) == 2
    assert len(perc_lists[0]) == len(perc_lists[1])
    diff_list = [abs(i - j) for i, j in zip(perc_lists[0], perc_lists[1])]
    ave_diff = sum(diff_list) / len(diff_list)
    return ave_diff
