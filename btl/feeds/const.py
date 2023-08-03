from enum import Enum

OneHP = 33000           # (lb-ft) per minute
InchesPerFoot = 12

# Metric Input Conversions (reverse for output)
SMMtoSFM = 3.28084      # SMM -> SFM
mmToInch = 0.03937      # mm -> Inch
KWToHP = 1.34102        # KW -> HP
KWcm3ToHPin3 = 21.9754  # KW/cm^3 -> HP/in^3
NMtoInLbs = 8.85075     # Nm -> In-Pounds
GPtoPSI6 = 0.14503      # GigaPascals -> PSI*10^6
cm3ToIn3 = 0.06102
KGtoLbs = 2.20462

class Operation(Enum):
    MILLING = 1
    SLOTTING = 2
    HSM = 3
    DRILLING = 4
    #TURNING = 5   # unsupported for now
    #PARTING = 6   # unsupported for now
