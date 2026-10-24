######################################################
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / "tools").is_dir():
        sys.path.append(str(parent))
        break

from tools.unit_conversions import *
from tools.reusable_functions import *
#######################################################

import numpy as np
import sympy as sp

# Reference: "Aircraft design: a systems engineering approach" 
# Note: the pages correspond to those of the pdf, not the textbook

# ============================================================
# 1. Mission and payload assumptions
# ============================================================

m_passenger = 190  # [lb/person]
m_baggage = 30      # [lb/passenger]
m_pilot = 190       # [lb]

n_passengers = 7

W_p = n_passengers * (m_passenger + m_baggage)  # [lb]
W_c = m_pilot                                   # [lb]


# ============================================================
# 2. Combustion cruise assumptions 
# ============================================================

R = 200          # Combustion cruise range [nmi]
L_D = 12         # Cruise lift-to-drag ratio [-] (p131)
eta_p = 0.85     # Propeller efficiency [-] (assumed from litterature)
SFC = 0.7        # Specific fuel consumption [lb/(hp*h)] (p136)

# Convert SFC to C [1/nmi]
c = nmi_to_ft(SFC / (3600 * 550)) # (p135)

# ============================================================
# 3. Sadraey mission segment weight ratios (p129)
# ============================================================

W2_W1 = 0.980  # Taxi and takeoff
W3_W2 = 0.970  # Climb
W4_W3 = 1.000  # ELECTRIC CRUISE: no fuel burned -> heavier 
W5_W4 = np.exp(-R * c / (eta_p * L_D))  # Combustion cruise (eq 4.18)
W6_W5 = 0.990  # Descent
W7_W6 = 0.997  # Approach and landing


# Overall mission weight ratio (eq 4.10)
W7_W1 = (
    W2_W1
    * W3_W2
    * W4_W3
    * W5_W4
    * W6_W5
    * W7_W6
)

# Fuel weight fraction, using Sadraey's simplified 1.05 reserve adjustment (eq. 4.11)
W_f_ratio = 1.05 * (1 - W7_W1)

# ============================================================ #
# 4. Sadraey twin turboprop statistical category
# ============================================================ #

# Analytically: 2 eqs for 2 unknowns
# W_to = (W_c + W_p) / (1 - W_e_ratio - W_f_ratio)  (1)
# W_e_ratio = a * W_to + b  (2)

# For a twin-turboprop (p110/111)
a = -8.2e-7
b = 0.65

# For a GA-twin engine (why so high??)
# a = 2.73e-4
# b = -9.08

# Thus: (2)->(1) gives a 2nd order quadratic equation in W_to with coefs A, B, C:

# Rearranging:
# (-a) * W_TO**2
# + (1 - b - W_f_ratio) * W_TO
# -(W_p + W_c) = 0

A = -a
B = 1 - b - W_f_ratio
C = -(W_p + W_c)

W_to = sp.symbols('W_to')

equation = A * W_to**2 + B * W_to + C

solutions = sp.solve(equation, W_to)

print(f"W_to solutions: {solutions}")

W_to = max(solutions) # [lb] 

# Calculate empty-weight fraction at the resulting W_TO (eq. 4.26)
W_e_ratio = a * W_to + b

"""
# Alternatively: (less accurate statistical approach)
W_e_ratio = 0.62 # For a piston/turboprop (p137)
W_to = (W_c + W_p) / (1 - W_e_ratio - W_f_ratio)
"""

# ============================================================
# 5. Results
# ============================================================

print("\n----- Takeoff-weight estimation -----")
print(f"Payload weight Wp = {W_p:.2f} lb")
print(f"Crew weight Wc = {W_c:.2f} lb")
print(f"Empty weight fraction We/Wto = {W_e_ratio:.4f}")
print(f"Fuel weight fraction Wf/Wto = {W_f_ratio:.4f}")
print(f"Estimated W_to = {W_to:.2f} lb or W_to = {lb_to_kg(W_to):.2f} kg")
print()