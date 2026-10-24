######################################################
import sys
from pathlib import Path

for parent in Path(__file__).resolve().parents:
    if (parent / "tools").is_dir():
        sys.path.append(str(parent))
        break

from tools.unit_conversions import *
# from tools.reusable_functions import *
#######################################################

import numpy as np
import matplotlib.pyplot as plt
from ambiance import Atmosphere

g = 9.81 # [m/s^2]


def air_rho(h):

    """
    Range of validity: h = [0, 11000] m 
    """
    # ISA constants
    rho0 = 1.225      # Standard sea-level air density [kg/m^3] 
    T0 = 288.15       # Standard sea-level air temperature [K]
    L = 0.0065        # Temperature rate of change with altitude [K/m]
    R = 287.05        # Specific gas constant of air [J/(kg*K)]

    rho = rho0 * (1 - L * h / T0)**(g / (R * L) - 1) #

    return rho

def air_density(h):
    atm = Atmosphere(h)
    return atm.density

# Aircraft characteristics (estimates) :
m_to = 3500 # [kg]

W_to = m_to * g

v_c_kts = 225
v_c = kt_to_ms(v_c_kts)

CD_0 = 0.025
e = 0.755
#rho_c = 0.674 # [kg/m^3] at cruise altitude 10800 m

# Altitude range
h_min = 0
h_max = 20000
h = np.linspace(h_min, h_max, 1000) # [m]
rho_c = air_density(h)

AR = 8 
S = 28.955 # [m**2]
eta_p = 0.75

C_L_c = W_to / (0.5 * rho_c * v_c**2 * S)
C_D_c = CD_0 + C_L_c**2 / (e * np.pi * AR)

T_c = 0.5 * rho_c * v_c**2 * C_D_c * S # [N]

P_c = T_c * v_c # [W] 

P_c_shaft = P_c / eta_p

# Drag polar

# Theoretical drag polar: 
# C_L = np.linspace(-1.5, 2.0, 200)
# (FOR THIS PLOT, INDEP OF ALTITUDE --> REMOVE h FROM THE PLOT BELOW!)

# In the operating range of altitudes (h = [0,10 000] m):
C_L = C_L_c

C_D = CD_0 + C_L**2 / (e * np.pi * AR)

# L/D as a function of altitude : 

L_D = C_L / C_D

"""
# Next step: trade off study of optimal cruise altitude such that the total energy required
# required for takeoff, climb and cruise is minimised.
"""
# Takeoff energy:

P_to = 791.86e3 # [W]
x_to = ft_to_m(300) # [m]
v_lof = 24.20 # [m/s]
v_to_i = 0 # [m/s]
v_to_f = v_lof
v_to_avg = (v_to_f + v_to_i) / 2
v_to_avg = v_lof / np.sqrt(2)


t_to = x_to / v_to_avg # [s]

E_to = P_to * t_to # [J]

E_to = kWh_to_J(1.18) # (extracted from power_estimate.py)

# Climb energy:

ROC_fpm = 1500 # [fpm]
ROC = fpm_to_ms(ROC_fpm) # [m/s]

h_obs = ft_to_m(50) # [m]

t_climb = (h - h_obs) / ROC

gamma = np.deg2rad(10) # climb angle [rad] (assumption to be verified!!)

v_climb = ROC / np.sin(gamma) # [m/s]

C_L_climb = W_to / (0.5 * air_density(h/2) * v_climb**2 * S)

C_D_climb = CD_0 + C_L_climb**2 / (e * np.pi * AR)

P_climb = 0.5 * air_density(h/2) * S * v_climb**3 * C_D_climb + W_to * ROC

P_climb_shaft = P_climb / eta_p

E_climb = P_climb_shaft * t_climb # [J]

x_climb = (h - h_obs) / np.tan(gamma)

# Cruise energy

x_target = nmi_to_m(400)

x_c = x_target - (x_to + x_climb) # [m]

t_c = x_c / v_c # [s]

E_c = P_c_shaft * t_c # [J]

# Total energy

E_tot = J_to_kWh(E_to + E_climb + E_c) # [kWh]


# Optimal altitude for minimum total mission energy
i_E_min = np.argmin(E_tot)

# Optimal altitude for minimum cruise shaft power
i_P_min = np.argmin(P_c_shaft)

i_c = i_E_min
h_c = h[i_c]

# Chosen optimal cruise altitude
# h_c = 10000 # [m]

# Find the index corresponding to the chosen altitude
#i_c = np.argmin(np.abs(h - h_c))

########################################
#               PLOTS                  #
########################################

# Plot of the air density as a function of altitude

def density_vs_altitude():

    plt.figure(figsize=(8, 5))

    plt.plot(h/1000, rho_c, color = "green")

    plt.grid(True)
    plt.ylabel(r"Air density $\rho$ [kg/m$^3$]")
    plt.xlabel("Altitude h [km]")
    plt.title("Air density vs altitude")


# Plot shaft power as a function of altitude

def power_vs_altitude():
    plt.figure(figsize=(8, 5))

    plt.plot(h / 1000, W_to_hp(P_c_shaft), color = "orange")

    plt.grid(True)
    plt.xlabel("Altitude [km]")
    plt.ylabel("Shaft power required [hp]")
    plt.title("Cruise shaft power required vs altitude")

    plt.scatter(h_c/1000, W_to_hp(P_c_shaft[i_c]), color="red")
    plt.annotate(f"h={h_c/1000:.2f} km\n{W_to_hp(P_c_shaft[i_c]):.0f} hp",
             (h_c/1000, W_to_hp(P_c_shaft[i_c])), xytext=(10,10), textcoords="offset points")


def drag_polar_altitude():

    """
    This plot shows the C_L and C_D required in cruise to maintain cruise equilibrium
    i.e. L = W and D = T
    """

    plt.figure(figsize=(8, 5))

    plt.scatter(
        C_D,
        C_L,
        c=h / 1000,
        cmap="viridis",
        s=15
    )

    plt.colorbar(label="Altitude [km]")

    plt.xlabel(r"Drag coefficient $C_D$")
    plt.ylabel(r"Lift coefficient $C_L$")
    plt.title("Aircraft Drag Polar vs Altitude")

    plt.grid(True)
    plt.tight_layout()

    plt.scatter(C_D[i_c], C_L[i_c], color="red")
    plt.annotate(f"h={h_c/1000:.2f} km\nCD={C_D[i_c]:.3f}, CL={C_L[i_c]:.3f}",
             (C_D[i_c], C_L[i_c]), xytext=(10,10), textcoords="offset points")


def LD_vs_CL_altitude():
    # Plot L/D as a function of CL, with altitude represented by color
    plt.figure(figsize=(8, 5))

    scatter = plt.scatter(
        C_L,
        L_D,
        c=h / 1000,
        cmap="viridis",
        s=25
    )

    plt.colorbar(scatter, label="Altitude [km]")

    plt.xlabel(r"Lift coefficient $C_L$")
    plt.ylabel(r"Lift-to-drag ratio $C_L/C_D$")
    plt.title("Cruise Aerodynamic Efficiency vs Lift Coefficient")

    plt.grid(True)
    plt.tight_layout()

    plt.scatter(C_L[i_c], L_D[i_c], color="red")
    plt.annotate(f"h={h_c/1000:.2f} km\nL/D={L_D[i_c]:.2f}",
             (C_L[i_c], L_D[i_c]), xytext=(10,10), textcoords="offset points")

def total_energy():
    plt.figure(figsize=(8, 5))

    plt.plot(h / 1000, E_tot, color = "purple")

    plt.grid(True)
    plt.xlabel("Cruise Altitude h_c [km]")
    plt.ylabel("Total energy required [kWh]")
    plt.title("Total energy required vs cruise altitude")

    plt.scatter(h_c/1000, E_tot[i_c], color="red")
    plt.annotate(f"h={h_c/1000:.2f} km\n{E_tot[i_c]:.1f} kWh",
             (h_c/1000, E_tot[i_c]), xytext=(10,10), textcoords="offset points")
    

plots = 1

if plots:
    density_vs_altitude()
    power_vs_altitude()
    drag_polar_altitude()
    LD_vs_CL_altitude()
    total_energy()


print(f"Cruise speed: v_c = {v_c_kts:.2f} kt or v_c = {v_c:.2f} m/s ({ms_to_kmh(v_c):.2f} km/h)")
print(f"Considered cruise altitude range: h = [{h_min:.0f},{h_max:.0f}] m")
print(f"Cruise C_L_c ranges from C_L_c(h = {h_min:.0f}) = {C_L_c[0]:.3f} to C_L_c(h = {h_max:.0f}) = {C_L_c[-1]:.3f}")
print(f"Cruise C_D_c ranges from C_D_c(h = {h_min}) = {C_D_c[0]:.3f} to C_D_c(h = {h_max:.0f}) = {C_D_c[-1]:.3f}")
print()
print(f"Chosen optimal cruise altitude: h_c = {h_c:.2f} m or h = {m_to_ft(h_c):.2f} ft")
print()
print(f"Lift coefficient : C_L_c = {C_L_c[i_c]:.3f} at h_c")
print(f"Drag coefficient : C_D_c = {C_D_c[i_c]:.3f} at h_c")
print(f"Thrust required for cruise T_c = {T_c[i_c]:.2f} N at h_c")
print(f"Power required for cruise P_c = {P_c[i_c]/1000:.2f} kW or {W_to_hp(P_c[i_c]):.2f} hp at h_c")

print()
print("Total energy:")
print()
print(f"Total takeoff time: t_to = {t_to:.2f} s")
print(f"Climb time: t_climb = {t_climb[i_c]:.2f} s")
print(f"Cruise time: t_c = {t_c[i_c]:.2f} s for x_c = {m_to_nmi(x_c[i_c]):.2f} nmi")

print(f"Takeoff energy: E_to = {J_to_kWh(E_to):.2f} kWh")
print(f"Total energy at h_c : E_tot_opt = {E_tot[i_c]:.2f} kWh")
print(f"Power to shaft required for cruise P_c_shaft = {P_c_shaft[i_c]/1000:.2f} kW or P_c_shaft = {W_to_hp(P_c_shaft[i_c]):.2f} hp at h_c")
plt.show()


