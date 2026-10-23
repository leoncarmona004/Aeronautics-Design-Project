import numpy as np 

# Unit conversions
def lb_to_kg(lb):
    return lb * 0.45359237

def nmi_to_ft(nmi):
    return nmi * 6076.12

def kt_to_ms(kt):
    return kt/1.944

def W_to_hp(W):
    return W * 0.00134102

def hp_to_W(hp):
    return hp * 745.7

def ft_to_m(ft):
    return ft * 0.3048

def m_to_ft(m):
    return m * 3.28084

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
