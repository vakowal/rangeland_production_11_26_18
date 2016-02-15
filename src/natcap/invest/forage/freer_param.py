"""This is a place to stash parameter values as named in Freer et al. 2012
(The GRAZPLAN animal biology model for sheep and cattle and the GrazFeed
decision support tool)"""

class FreerParamCattle:

    """Class containing parameters for cattle described in Freer et al. 2012,
    using same names as Freer et al 2012."""
    
    def __init__(self, breed):
        self.CN1 = 0.0115
        self.CN2 = 0.27
        self.CN3 = 0.4
        self.CI1 = 0.025
        self.CI2 = 1.7
        self.CI3 = 0.22
        self.CI4 = 60.
        if breed == 'B_indicus':
            self.CI5 = 0.01
        elif breed == 'B_taurus':
            self.CI5 = 0.02
        elif breed == 'indicus_x_taurus':
            self.CI5 = 0.015
        self.CI6 = 25.
        self.CI7 = 22.
        self.CI8 = 62.
        self.CI9 = 1.7
        self.CI10 = 0.6
        self.CI11 = 0.05
        self.CI12 = 0.15
        self.CI13 = 0.005
        self.CI14 = 0.002
        self.CI19 = 0.416
        self.CI20 = 1.5
        self.CR1 = 0.8
        self.CR2 = 0.17
        self.CR3 = 1.7
        self.CR4 = 0.00078
        self.CR5 = 0.6
        self.CR6 = 0.00074
        self.CR7 = 0.5
        self.CR11 = 10.5
        self.CR12 = 0.8
        self.CR13 = 0.35
        self.CR14 = 1.
        self.CR20 = 11.5
        self.CK1 = 0.5
        self.CK2 = 0.02
        self.CK3 = 0.85
        self.CK5 = 0.4
        self.CK6 = 0.02
        self.CK10 = 0.84
        self.CK11 = 0.8
        self.CK13 = 0.035
        self.CK14 = 0.33
        self.CK15 = 0.12
        self.CK16 = 0.043
        self.CL1 = 4.
        self.CL2 = 30.
        self.CL4 = 0.6
        self.CL5 = 0.94
        self.CL6 = 3.1
        self.CL7 = 1.17
        self.CL15 = 0.032
        self.CL16 = 0.7
        self.CL17 = 0.01
        self.CL19 = 1.6
        self.CL20 = 4.
        self.CL21 = 0.004
        self.CL22 = 0.006
        self.CL23 = 3.
        self.CL24 = 0.6
        self.CM1 = 0.09
        if breed == 'B_indicus':
            self.CM2 = 0.31
        elif breed == 'B_taurus':
            self.CM2 = 0.36
        elif breed == 'indicus_x_taurus':
            self.CM2 = 0.335
        self.CM3 = 0.00008
        self.CM4 = 0.84
        self.CM5 = 0.23
        self.CM6 = 0.0025
        self.CM7 = 0.9
        self.CM8 = 0.000057
        self.CM9 = 0.16
        self.CM10 = 0.0152
        self.CM11 = 0.000526
        if breed == 'B_indicus':
            self.CM12 = 0.0129
            self.CM13 = 0.0338
        elif breed == 'B_taurus':
            self.CM12 = 0.0161
            self.CM13 = 0.0422
        elif breed == 'indicus_x_taurus':
            self.CM12 = 0.0145
            self.CM13 = 0.038
        self.CM14 = 0.00011
        self.CM15 = 1.15
        self.CM16 = 0.0026
        self.CM17 = 5.
        self.CRD1 = 0.3
        self.CRD2 = 0.25
        self.CRD3 = 0.1
        self.CRD4 = 0.007
        self.CRD5 = 0.005
        self.CRD6 = 0.35
        self.CRD7 = 0.1
        self.CA1 = 0.05
        self.CA2 = 0.85
        self.CA3 = 5.5
        self.CA4 = 0.178
        self.CA6 = 1.
        self.CA7 = 0.6
        self.CG2 = 0.7
        self.CG4 = 6.
        self.CG5 = 0.4
        self.CG6 = 0.9
        self.CG7 = 0.97
        if breed == 'B_incidus':
            self.CG8 = 23.2
            self.CG9 = 16.5
        else:
            self.CG8 = 27.
            self.CG9 = 20.3
        self.CG10 = 2.
        self.CG11 = 13.8
        if breed == 'B_indicus':
            self.CG12 = 0.092
            self.CG13 = 0.12
        else:
            self.CG12 = 0.072
            self.CG13 = 0.14
        self.CG14 = 0.008
        self.CG15 = 0.115
        
class FreerParamSheep:

    """Class containing parameters for sheep described in Freer et al. 2012,
    using same names as Freer et al 2012."""
    
    def __init__(self):
        self.CN1 = 0.0157
        self.CN2 = 0.27
        self.CN3 = 0.4
        self.CI1 = 0.04
        self.CI2 = 1.7
        self.CI3 = 0.5
        self.CI4 = 25.
        self.CI5 = 0.01
        self.CI6 = 25.
        self.CI7 = 22.
        self.CI8 = 28.
        self.CI9 = 1.4
        self.CI12 = 0.15
        self.CI13 = 0.02
        self.CI14 = 0.002
        self.CI20 = 1.5
        self.CR1 = 0.8
        self.CR2 = 0.17
        self.CR3 = 1.7
        self.CR4 = 0.00112
        self.CR5 = 0.6
        self.CR6 = 0.00112
        self.CR7 = 0.
        self.CR11 = 10.5
        self.CR12 = 0.8
        self.CR13 = 0.35
        self.CR14 = 1.
        self.CR20 = 11.5
        self.CK1 = 0.5
        self.CK2 = 0.02
        self.CK3 = 0.85
        self.CK5 = 0.4
        self.CK6 = 0.02
        self.CK10 = 0.84
        self.CK11 = 0.8
        self.CK13 = 0.035
        self.CK14 = 0.33
        self.CK15 = 0.12
        self.CK16 = 0.043
        self.CL1 = 2.
        self.CL2 = 22.
        self.CL5 = 0.94
        self.CL6 = 4.7
        self.CL7 = 1.17
        self.CL15 = 0.045
        self.CL16 = 0.7
        self.CL17 = 0.01
        self.CL19 = 1.6
        self.CL20 = 4.
        self.CL21 = 0.008
        self.CL22 = 0.012
        self.CL23 = 3.
        self.CL24 = 0.6
        self.CM1 = 0.09
        self.CM2 = 0.26
        self.CM3 = 0.00008
        self.CM4 = 0.84
        self.CM5 = 0.23
        self.CM6 = 0.02
        self.CM7 = 0.9
        self.CM8 = 0.000057
        self.CM9 = 0.16
        self.CM10 = 0.0152
        self.CM11 = 0.00046
        self.CM12 = 0.000147
        self.CM13 = 0.003375
        self.CM15 = 1.15
        self.CM16 = 0.0026
        self.CM17 = 40.
        self.CRD1 = 0.3
        self.CRD2 = 0.25
        self.CRD3 = 0.1
        self.CRD4 = 0.007
        self.CRD5 = 0.005
        self.CRD6 = 0.35
        self.CRD7 = 0.1
        self.CA1 = 0.05
        self.CA2 = 0.85
        self.CA3 = 5.5
        self.CA4 = 0.178
        self.CA6 = 1.
        self.CA7 = 0.6
        self.CG2 = 0.7
        self.CG4 = 6.
        self.CG5 = 0.4
        self.CG6 = 0.9
        self.CG7 = 0.97
        self.CG8 = 27.
        self.CG9 = 20.3
        self.CG10 = 2.
        self.CG11 = 13.8
        self.CG12 = 0.072
        self.CG13 = 0.14
        self.CG14 = 0.008
        self.CG15 = 0.115

class FreerParamCamelid:

    """Class containing parameters for new world camelids, based on the
    parameters for sheep described in Freer et al. 2012."""
    
    def __init__(self):
        self.CN1 = 0.0157
        self.CN2 = 0.27
        self.CN3 = 0.4
        self.CI1 = 0.04
        self.CI2 = 1.7
        self.CI3 = 0.5
        self.CI4 = 25.
        self.CI5 = 0.01
        self.CI6 = 25.
        self.CI7 = 22.
        self.CI8 = 28.
        self.CI9 = 1.4
        self.CI12 = 0.15
        self.CI13 = 0.02
        self.CI14 = 0.002
        self.CI20 = 1.5
        self.CR1 = 0.8
        self.CR2 = 0.17
        self.CR3 = 1.7
        self.CR4 = 0.00112
        self.CR5 = 0.6
        self.CR6 = 0.00112
        self.CR7 = 0.
        self.CR11 = 10.5
        self.CR12 = 0.8
        self.CR13 = 0.35
        self.CR14 = 1.
        self.CR20 = 11.5
        self.CK1 = 0.5
        self.CK2 = 0.02
        self.CK3 = 0.85
        self.CK5 = 0.4
        self.CK6 = 0.02
        self.CK10 = 0.84
        self.CK11 = 0.8
        self.CK13 = 0.035
        self.CK14 = 0.33
        self.CK15 = 0.12
        self.CK16 = 0.043
        self.CL1 = 2.
        self.CL2 = 22.
        self.CL5 = 0.94
        self.CL6 = 4.7
        self.CL7 = 1.17
        self.CL15 = 0.045
        self.CL16 = 0.7
        self.CL17 = 0.01
        self.CL19 = 1.6
        self.CL20 = 4.
        self.CL21 = 0.008
        self.CL22 = 0.012
        self.CL23 = 3.
        self.CL24 = 0.6
        self.CM1 = 0.09
        self.CM2 = 0.26
        self.CM3 = 0.00008
        self.CM4 = 0.84
        self.CM5 = 0.23
        self.CM6 = 0.02
        self.CM7 = 0.9
        self.CM8 = 0.000057
        self.CM9 = 0.16
        self.CM10 = 0.0152
        self.CM11 = 0.00046
        self.CM12 = 0.000147
        self.CM13 = 0.003375
        self.CM15 = 1.15
        self.CM16 = 0.0026
        self.CM17 = 40.
        self.CRD1 = 0.3
        self.CRD2 = 0.25
        self.CRD3 = 0.1
        self.CRD4 = 0.007
        self.CRD5 = 0.005
        self.CRD6 = 0.35
        self.CRD7 = 0.1
        self.CA1 = 0.05
        self.CA2 = 0.85
        self.CA3 = 5.5
        self.CA4 = 0.178
        self.CA6 = 1.
        self.CA7 = 0.6
        self.CG2 = 0.7
        self.CG4 = 6.
        self.CG5 = 0.4
        self.CG6 = 0.9
        self.CG7 = 0.97
        self.CG8 = 27.
        self.CG9 = 20.3
        self.CG10 = 2.
        self.CG11 = 13.8
        self.CG12 = 0.072
        self.CG13 = 0.14
        self.CG14 = 0.008
        self.CG15 = 0.115

class FreerParamHindgut:

    """Class containing parameters for hindgut fermenters, based on the
    parameters for B. indicus cattle described in Freer et al. 2012."""
    
    def __init__(self):
        self.CN1 = 0.0115
        self.CN2 = 0.27
        self.CN3 = 0.4
        self.CI1 = 0.025
        self.CI2 = 1.7
        self.CI3 = 0.22
        self.CI4 = 60.
        self.CI5 = 0.01
        self.CI6 = 25.
        self.CI7 = 22.
        self.CI8 = 62.
        self.CI9 = 1.7
        self.CI10 = 0.6
        self.CI11 = 0.05
        self.CI12 = 0.15
        self.CI13 = 0.005
        self.CI14 = 0.002
        self.CI19 = 0.416
        self.CI20 = 1.5
        self.CR1 = 0.8
        self.CR2 = 0.17
        self.CR3 = 1.7
        self.CR4 = 0.00078
        self.CR5 = 0.6
        self.CR6 = 0.00074
        self.CR7 = 0.5
        self.CR11 = 10.5
        self.CR12 = 0.8
        self.CR13 = 0.35
        self.CR14 = 1.
        self.CR20 = 11.5
        self.CK1 = 0.5
        self.CK2 = 0.02
        self.CK3 = 0.85
        self.CK5 = 0.4
        self.CK6 = 0.02
        self.CK10 = 0.84
        self.CK11 = 0.8
        self.CK13 = 0.035
        self.CK14 = 0.33
        self.CK15 = 0.12
        self.CK16 = 0.043
        self.CL1 = 4.
        self.CL2 = 30.
        self.CL4 = 0.6
        self.CL5 = 0.94
        self.CL6 = 3.1
        self.CL7 = 1.17
        self.CL15 = 0.032
        self.CL16 = 0.7
        self.CL17 = 0.01
        self.CL19 = 1.6
        self.CL20 = 4.
        self.CL21 = 0.004
        self.CL22 = 0.006
        self.CL23 = 3.
        self.CL24 = 0.6
        self.CM1 = 0.09
        self.CM2 = 0.31
        self.CM3 = 0.00008
        self.CM4 = 0.84
        self.CM5 = 0.23
        self.CM6 = 0.0025
        self.CM7 = 0.9
        self.CM8 = 0.000057
        self.CM9 = 0.16
        self.CM10 = 0.0152
        self.CM11 = 0.000526
        self.CM12 = 0.0129
        self.CM13 = 0.0338
        self.CM14 = 0.00011
        self.CM15 = 1.15
        self.CM16 = 0.0026
        self.CM17 = 5.
        self.CRD1 = 0.3
        self.CRD2 = 0.25
        self.CRD3 = 0.1
        self.CRD4 = 0.007
        self.CRD5 = 0.005
        self.CRD6 = 0.35
        self.CRD7 = 0.1
        self.CA1 = 0.05
        self.CA2 = 0.85
        self.CA3 = 5.5
        self.CA4 = 0.178
        self.CA6 = 1.
        self.CA7 = 0.6
        self.CG2 = 0.7
        self.CG4 = 6.
        self.CG5 = 0.4
        self.CG6 = 0.9
        self.CG7 = 0.97
        self.CG8 = 23.2
        self.CG9 = 16.5
        self.CG10 = 2.
        self.CG11 = 13.8
        self.CG12 = 0.092
        self.CG13 = 0.12
        self.CG14 = 0.008
        self.CG15 = 0.115

def get_params(type):
    """Return parameters specific to the animal type or breed."""
    
    if type in ['B_indicus', 'B_taurus', 'indicus_x_taurus']:
        return FreerParamCattle(type)
    elif type == 'sheep':
        return FreerParamSheep()
    elif type == 'camelid':
        return FreerParamCamelid()
    elif type == 'hindgut_fermenter':
        return FreerParamHindgut()
    else:
        er = "Error: breed must match allowable values"
        raise ValueError(er)