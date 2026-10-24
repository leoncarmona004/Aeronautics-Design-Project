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

g = 9.81 # [m/s^2]

# Aircraft characteristics (estimates) :
m_to = 3500 # [kg]
W_to = m_to * g # [N]
S = 28.955 # [m^2]
b = 15.22 # [m]
l_fus = 1.47 # [m] ??
l_wing = (b / 2) - (l_fus / 2)
c_mean = 1.937 # [m]
c_root = 2.279 # [m]
c_tip = 1.595 # [m]

n_prop = 8

D_prop = l_wing / (n_prop/2 + 0.1 * n_prop/2)


# Power at takeoff
P_1 = 800e3 # [W]
P_2 = 820e3 # [W]

# Choose the correct power requirement
P_req = P_2

# Assuming a 50/50 thermal/electric propulsion (equal range):
P_el = P_req / 2
P_th = P_req / 2

P_motor = P_req / n_prop

# Battery capacity estimation


print(f"Total power required: P_req = {P_req/1000:.2f} kW or P_req = {W_to_hp(P_req):.2f} hp")
print(f"Total thermal required: P_req = {P_th/1000:.2f} kW or P_req = {W_to_hp(P_th):.2f} hp")
print(f"Total electric power required: P_el = {P_el/1000:.2f} kW or P_req = {W_to_hp(P_el):.2f} hp")
print(f"Total power required per motor: P_req = {P_motor/1000:.2f} kW or P_req = {W_to_hp(P_motor):.2f} hp")
print(f"Wing length: l_wing = {l_wing:.2f} m")
print(f"Prop diameter (reduced for clearance) : D_prop = {D_prop:.2f} m")
