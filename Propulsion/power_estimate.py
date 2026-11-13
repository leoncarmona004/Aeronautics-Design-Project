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
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import brentq

g = 9.81 # [m/s^2]
M_TEMP = 200 # [kg]
K_FUEL_ASSUMED = 0.15 # fuel mass proportion

############# Imposed atmosphere : ISA + 18 F ###################

# Takeoff in imposed condition
atm = Atmosphere(0)

rho_sl = atm.density[0]
T_sl = atm.temperature[0]

# ISA + 18°F
delta_T = 18 * 5/9  # [K]
T = T_sl + delta_T

# Correct density at constant pressure
rho_imposed = rho_sl * T_sl / T # [kg/m^3] (Ideal gas law)

print(f"rho_imposed = {rho_imposed:.3f} kg/m^3")

#################### Helper functions ########################

def air_density(h):
    """
    Air density following ISA + 18°F. Returns an array
    """
    atm_h = Atmosphere(h)

    return atm_h.density * atm_h.temperature / (atm_h.temperature + delta_T) # Ideal gas law

def mass_computation(m_battery, m_fuel):

    # Known 
    m_passenger = lb_to_kg(190)  
    m_baggage = lb_to_kg(30)      
    m_pilot = lb_to_kg(190) 
    n_passengers = 7  

    m_payload = n_passengers * (m_passenger + m_baggage)

    # Assumed
    n_motors = 6
    m_generator = lb_to_kg(280) # Honeywell 1MW generator
    m_engine = lb_to_kg(250) # [kg] (Rolls Royce)
    m_motor = 50 # [kg] (Magni350)
    m_prop = 30 # [kg] (assumption)
    
    #m_fuel = 30 # [kg] (assumption)
    m_fuselage = 390 # [kg]
    m_wings = 570 
    m_empennage = 140 + 80 # [kg]
    m_gear = 185 # [kg]
    m_furnishing = 310 # [kg]
    m_systems = 270 # [kg]
    m_AC = 70 # [kg]

    m_structure = (m_fuselage + m_wings + m_empennage + m_gear + m_furnishing
                   + m_systems + m_AC)

    m_motors = n_motors * m_motor
    m_props = n_motors * m_prop

    m_empty =  (m_generator + m_engine +
               m_structure + m_battery + m_motors + m_props)

    M_fuel = K_FUEL_ASSUMED * (m_empty)  # temporary approximation : m_fuel = 20% of empty mtow
    #print(M_fuel)

    m_total = (m_empty + M_fuel + m_payload + m_pilot) # replace M_fuel by m_fuel when possible

    #print(m_structure/m_total)
    return m_total

print(f"Empty (no battery) weight: {mass_computation(0, 0):.2f} kg")

def battery_power_output(m_battery, p_b):
    """Output: power output in W"""
    return p_b * m_battery 

def linear_interpolation(x, x1, y1, x2, y2):
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

def power_available_shaft(P_shaft_sl, h):
    """
    Available shaft power as a function of altitude.
    Assumes power is proportional to air density.
    """
    rho_h = air_density(h)

    return P_shaft_sl * (rho_h / rho_imposed) # Power decrease assumption

def power_available_propulsive(P_shaft_sl, h):
    """
    Available propulsive power as a function of altitude.
    """
    return eta_p * power_available_shaft(P_shaft_sl, h) # Would be even worse considering prop efficiency decrease

def find_ROC_ceiling(h, ROC, target_ROC):
    """
    Find the first altitude at which ROC crosses target_ROC.

    Uses linear interpolation between two consecutive altitude points.

    Returns:
        h_ceiling [m], or None if the target is not reached.
    """

    # Find the first index where ROC is below or equal to the target
    indices = np.where(ROC <= target_ROC)[0]

    if len(indices) == 0:
        return None

    i = indices[0]

    # Cannot interpolate if the first point is already below the target
    if i == 0:
        return h[0]

    # Two points surrounding the crossing
    h_1 = h[i - 1]
    h_2 = h[i]

    ROC_1 = ROC[i - 1]
    ROC_2 = ROC[i]

    # Linear interpolation
    # = h_1 + (target_ROC - ROC_1) * ((h_2 - h_1) / (ROC_2 - ROC_1))
    h_ceiling = linear_interpolation(target_ROC, ROC_1, h_1, ROC_2, h_2)

    return h_ceiling

#################### Aircraft characteristics ########################

# Aircraft characteristics (estimates) :

mtow = mass_computation(0, M_TEMP) # at first: no batteries

W_to = mtow * g

AR = 8 
S = 28.955 # [m**2]
C_L_max = 8 # takeoff
C_L_max_2 = 1.8 # high-lift devices retracted

CD_0 = 0.025
e = 0.755
mu = 0.02

# Maximum available power
P_generator = 1000e3 # [W] (generator output at sea level -> fixed)
P_batteries = 0 # [W] (depends on battery  -> iterative)

# Combined maximum available power (for takeoff):
P_max = P_generator + P_batteries

# Restricted climb available power (for less aggressive climb) -> to be implemented later
#P_climb_target = 300  # [kW] Initial value
eta_p = 0.75


# Check if the motors are able to supply enough propulsive power
# n_motors = 6
# P_max_motor = 350e3 # [W] (magni350 peak -> take magni650 if needed or HPDM-350)
# P_max_propulsive = (n_motors * P_max_motor) / eta_p


# H_MAX_MOTORS = ft_to_m(25000) # [m] maximum operating altitude of magni electric motors

#################### Global parameters ########################

PLOTS = 1

ELECTRIC_ONLY = 0

H_CUSTOM = 8000 # [m]

#OPTIMAL_ALT= "cruise_power"
OPTIMAL_ALT = "total_mass"
OPTIMAL_ALT = "total_energy"
#OPTIMAL_ALT = "custom" 

#BATTERY = "current"
BATTERY = "realistic"
BATTERY = "optimistic"

if BATTERY == "current":
    e_b = 200/1000 # [kWh/kg]
    p_b = 0.9 * 1000 # [W/kg]
elif BATTERY == "realistic":
    e_b = 350/1000 # [kWh/kg]
    p_b = 1.5 * 1000 # [W/kg]
else: 
    e_b = 480/1000 # [kWh/kg]
    p_b = 2.5 * 1000 # [W/kg]

M_HEAVY = 5670 # [kg]


# Battery energy contribution
k_to = 0
k_climb = 0

# Takeoff power to shaft
P_to_shaft = 0 

# Altitude range
h_min = 0
h_max = 15000
h = np.linspace(h_min, h_max, 1000) # [m]
rho_c = air_density(h)

############################################################

"""
# Next step: trade off study of optimal cruise altitude such that the total energy required
# required for takeoff, climb and cruise is minimised. Landing to be added later.
"""

h_obs = ft_to_m(50) # [m]
x_to = ft_to_m(300) # [m]
full_target_range = nmi_to_m(400) # [m]
electric_target_range = nmi_to_m(200) # [m]
v_c = kt_to_ms(225) # [m/s]
min_ROC_sl = fpm_to_ms(1500) # [m/s]
ceiling_ROC = fpm_to_ms(100) # [m/s] assumption for service ceiling
cruise_ROC = fpm_to_ms(300) # [m/s] assumption for service cruise

#################### Flight models ########################

def takeoff_model(S, C_L_max):

    v_s = np.sqrt(W_to / (0.5 * rho_imposed * S * C_L_max))
    k_1 = 1.1
    v_LOF = k_1 * v_s

    mu_prime = mu + 0.72 * (CD_0 / C_L_max)

    # Define the residual function: tau = T/W ratio
    def f(tau):

        gamma_LOF = 0.9 * tau - (0.3 / np.sqrt(AR))

        if gamma_LOF <= 0:
            return -np.inf # unphysical -> tells the solver to skip 

        x_a = v_LOF**2 / (g * np.sqrt(2)) + h_obs / gamma_LOF
        x_g = x_to - x_a

        if x_g <= 0:
            return -np.inf # unphysical -> tells the solver to skip 

        residual = tau - (v_LOF**2 / (2 * g * x_g) + mu_prime) # equivalent to the error between 2 iterations

        return residual

    # Minimum feasible thrust-to-weight ratio 
    x_a_min = v_LOF**2 / (g * np.sqrt(2)) # has to clear at least this distance to reach the obstacle

    if x_a_min >= x_to:
        return None # this would mean x_g < 0 which is not valid

    gamma_min = h_obs / (x_to - x_a_min)
    tau_min = (gamma_min + 0.3 / np.sqrt(AR)) / 0.9

    try:
        tau = brentq(f, tau_min + 1e-6, 20)

    except ValueError:
        return None

    ###### Computing the final takeoff parameters ######

    # Calculate takeoff parameters
    T_avg = tau * W_to

    gamma_LOF = 0.9 * tau - (0.3 / np.sqrt(AR))

    x_a = v_LOF**2 / (g * np.sqrt(2)) + h_obs / gamma_LOF
    x_g = x_to - x_a

    P_avg = T_avg * (v_LOF / np.sqrt(2))
    P_shaft_avg = P_avg / eta_p

    global P_to_shaft
    P_to_shaft = P_shaft_avg

    #v_to_i = 0 # [m/s]
    #v_to_f = v_LOF
    #v_to_avg = (v_to_f + v_to_i) / 2
    v_to_avg = v_LOF / np.sqrt(2) # assumption

    E_g = T_avg * x_g / eta_p    # ground roll
    E_a = T_avg * x_a / eta_p    # transition + climb to obstacle, if thrust is held
    E_to = E_g + E_a             

    t_to = x_to / v_to_avg # [s]

    #E_to = P_to * t_to # [J]

    return {
    "x_g": x_g,
    "x_a": x_a,
    "T_avg": T_avg,
    "P_avg": P_avg,
    "v_LOF": v_LOF,
    "v_s": v_s,
    "E_to": E_to,
    "t_to": t_to,
    "P_shaft_avg": P_shaft_avg,
    }


# Goal: have enough installed power P_climb_target to reach the altitude where cruise efficiency is optimal, but without having to carry
#  additional battery capacity and power capability to climb beyond that altitude.

def climb_model(S, C_L_max, P_climb_target):

    # ==========================================================
    # 1. GENERATOR + BATTERY POWER
    # ==========================================================

    # Generator shaft power available at each altitude
    P_generator_available = power_available_shaft(
        P_generator, h
    )

    # Battery continuously compensates for generator power loss
    P_battery_required = np.maximum(
        P_climb_target - P_generator_available,
        0
    )

    # Total available shaft power: constant 1 MW
    P_shaft_available = (
        P_generator_available + P_battery_required
    )

    # Available propulsive power
    P_prop_available = eta_p * P_shaft_available


    # ==========================================================
    # 2. INITIALIZE ARRAYS
    # ==========================================================

    ROC_climb = np.full_like(h, np.nan)
    ROC_ceiling = np.full_like(h, np.nan)

    V_climb = np.full_like(h, np.nan)
    gamma_climb = np.full_like(h, np.nan)

    t_climb = np.full_like(h, np.nan)
    x_climb = np.full_like(h, np.nan)

    E_climb = np.full_like(h, np.nan)
    E_battery_climb = np.full_like(h, np.nan)

    P_battery_climb = np.full_like(h, np.nan)

    # Before the climb starts
    E_climb[h < h_obs] = 0
    E_battery_climb[h < h_obs] = 0
    P_battery_climb[h < h_obs] = 0


    # ==========================================================
    # 3. MAXIMUM RATE OF CLIMB AT EACH ALTITUDE
    # ==========================================================

    for i in range(len(h)):

        rho = rho_c[i]

        # Stall speed
        v_stall = np.sqrt(
            2 * W_to / (rho * S * C_L_max)
        )

        # Candidate airspeeds
        V = np.linspace(
            1.2 * v_stall,
            2.5 * v_stall,
            300
        )

        # Initial estimate: level flight
        CL = W_to / (0.5 * rho * V**2 * S)

        CD = CD_0 + CL**2 / (np.pi * e * AR)

        D = 0.5 * rho * V**2 * S * CD

        P_required = D * V

        # Initial rate of climb
        ROC = (
            P_prop_available[i] - P_required
        ) / W_to

        # Iterative correction for climb angle
        for iteration in range(500):

            gamma = np.arcsin(
                np.clip(ROC / V, -1, 1)
            )

            CL = (
                W_to * np.cos(gamma)
                / (0.5 * rho * V**2 * S)
            )

            CD = CD_0 + CL**2 / (np.pi * e * AR)

            D = 0.5 * rho * V**2 * S * CD

            ROC_new = (
                P_prop_available[i] - D * V
            ) / W_to

            error = np.max(np.abs(ROC_new - ROC))

            ROC = ROC_new

            if error < 1e-6:
                break

        # Maximum rate of climb
        k = np.argmax(ROC)

        ROC_max = ROC[k]

        ROC_ceiling[i] = ROC_max

        # Stop once aircraft cannot climb anymore
        if ROC_max <= 0:
            break

        # Store climb performance
        ROC_climb[i] = ROC_max

        V_climb[i] = V[k]

        gamma_climb[i] = np.arcsin(
            np.clip(ROC_max / V[k], -1, 1)
        )


    # ==========================================================
    # 4. CEILINGS
    # ==========================================================

    h_cruise_ceiling = find_ROC_ceiling(
        h, ROC_ceiling, cruise_ROC
    )

    h_service_ceiling = find_ROC_ceiling(
        h, ROC_ceiling, ceiling_ROC
    )

    h_absolute_ceiling = find_ROC_ceiling(
        h, ROC_ceiling, 0
    )


    # ==========================================================
    # 5. CLIMB TIME, DISTANCE AND ENERGY
    # ==========================================================

    valid_indices = np.where(
        np.isfinite(ROC_climb)
        & (ROC_climb > 0)
        & (h >= h_obs)
    )[0]

    if len(valid_indices) > 0:

        h_valid = h[valid_indices]

        ROC_valid = ROC_climb[valid_indices]
        gamma_valid = gamma_climb[valid_indices]

        P_shaft_valid = P_shaft_available[valid_indices]
        P_battery_valid = P_battery_required[valid_indices]

        # Battery power during feasible climb
        P_battery_climb[valid_indices] = P_battery_valid

        # Climb time
        t_valid = cumulative_trapezoid(
            1 / ROC_valid,
            h_valid,
            initial=0
        )

        # Horizontal distance
        x_valid = cumulative_trapezoid(
            1 / np.tan(gamma_valid),
            h_valid,
            initial=0
        )

        # Total shaft energy
        E_valid = cumulative_trapezoid(
            P_shaft_valid / ROC_valid,
            h_valid,
            initial=0
        )

        # Battery shaft energy
        E_battery_valid = cumulative_trapezoid(
            P_battery_valid / ROC_valid,
            h_valid,
            initial=0
        )

        # Store results
        t_climb[valid_indices] = t_valid
        x_climb[valid_indices] = x_valid

        E_climb[valid_indices] = E_valid
        E_battery_climb[valid_indices] = E_battery_valid


    # ==========================================================
    # 6. RETURN
    # ==========================================================

    return {
        "ROC": ROC_climb,
        "gamma": gamma_climb,
        "t_climb": t_climb,
        "x_climb": x_climb,

        "P_shaft_available": P_shaft_available,
        "P_battery_climb": P_battery_climb,

        "E_climb": E_climb,
        "E_battery_climb": E_battery_climb,

        "V_climb": V_climb,

        "h_cruise_ceiling": h_cruise_ceiling,
        "h_service_ceiling": h_service_ceiling,
        "h_absolute_ceiling": h_absolute_ceiling,

        # Add future parameters below
    }


def cruise_model(S, C_L_max, target_range, x_climb):

    C_L_c = W_to / (0.5 * rho_c * v_c**2 * S)
    C_D_c = CD_0 + C_L_c**2 / (e * np.pi * AR)

    T_c = 0.5 * rho_c * v_c**2 * C_D_c * S # [N]

    P_c = T_c * v_c # [W] 

    P_c_shaft = P_c / eta_p

    x_c = target_range - (x_to + x_climb) # [m] /!\ this does not include descent and landing!!

    t_c = x_c / v_c # [s]

    E_c = P_c_shaft * t_c # [J]

    return {
        "C_L_c": C_L_c,
        "C_D_c": C_D_c,
        "T_c": T_c,
        "P_c": P_c,
        "P_c_shaft": P_c_shaft,
        "x_c": x_c,
        "t_c": t_c,
        "E_c": E_c,
    }


def landing_model(S, C_L_max):

    return None

#################### Mission requirements ########################

def mission_parameters(S, C_L_max, P_climb_target, PRINT):

    global k_to, k_climb, P_batteries, P_max

    ############ Takeoff performance ###############

    takeoff = takeoff_model(S, C_L_max)

    if takeoff is None:
        return None

    # Extract takeoff results
    x_g = takeoff["x_g"]
    x_a = takeoff["x_a"]
    T_to = takeoff["T_avg"]
    P_to = takeoff["P_avg"]
    v_LOF = takeoff["v_LOF"]
    v_s = takeoff["v_s"]
    E_to = takeoff["E_to"]
    t_to = takeoff["t_to"]
    P_to_shaft = takeoff["P_shaft_avg"]

    ############ Climb performance ###############

    climb = climb_model(S, C_L_max_2, P_climb_target)

    # Extract climb results
    ROC = climb["ROC"]
    gamma = climb["gamma"]
    t_climb = climb["t_climb"]
    x_climb = climb["x_climb"]
    P_shaft_available = climb["P_shaft_available"]
    P_battery_climb = climb["P_battery_climb"]
    E_climb = climb["E_climb"]
    E_battery_climb = climb["E_battery_climb"]
    V_climb = climb["V_climb"]
    h_cruise_ceiling = climb["h_cruise_ceiling"]
    h_service_ceiling = climb["h_service_ceiling"]
    h_absolute_ceiling = climb["h_absolute_ceiling"]

    ############# Cruise performance #############

    cruise = cruise_model(S, C_L_max, full_target_range, climb["x_climb"])

    # Extract cruise results
    C_L_c = cruise["C_L_c"]
    C_D_c = cruise["C_D_c"]
    T_c = cruise["T_c"]
    P_c = cruise["P_c"]
    P_c_shaft = cruise["P_c_shaft"]
    x_c = cruise["x_c"]
    t_c = cruise["t_c"]
    E_c = cruise["E_c"]

    ############## Total energy ###################

    E_tot = J_to_kWh(E_to + E_climb + E_c) # [kWh]

    ############ Battery sizing, for every cruise altitude #####################

    if ELECTRIC_ONLY: # to be implemented later (if needed)
        # Fully electric operation: generator does not contribute during all phases
        # Takeoff
        k_to = 1
        P_b_to = P_to_shaft
        E_b_to = E_to

        # Climb
        k_climb = 1
        P_b_climb = P_batteries
        E_b_climb = E_climb

        # Entire cruise is battery-powered
        P_b_electric = P_c_shaft
        E_b_electric = E_c

        P_b_hybrid = np.zeros_like(h)
        E_b_hybrid = np.zeros_like(h)

    else:

        ##### Takeoff battery contribution #####
        P_b_to = max(P_to_shaft - P_generator, 0)

        k_to = P_b_to / P_to_shaft if P_to_shaft > 0 else 0

        E_b_to = E_to * k_to

        ##### Climb battery contribution: #####

        # Generator power available at each altitude
        P_gen_available = power_available_shaft(P_generator, h)

        # Battery contribution during climb, evaluated at every altitude
        P_b_climb = np.maximum.accumulate(np.nan_to_num(P_battery_climb, nan=0.0)) # replaces nan with 0, then gives the PEAK power needed to CLIMB to every cruise altitude 

        E_b_climb = E_battery_climb # already integrated

        ##### Cruise battery contribution #####

        # 1) 200 nmi fully electric cruise
        #    Generator OFF: battery supplies 100% of cruise power
        t_electric = electric_target_range / v_c

        P_b_electric = P_c_shaft
        E_b_electric = P_b_electric * t_electric

        # note: if the flight is fully hybrid, this will provide extra range!

        # 2) Remaining cruise: hybrid operation
        #    Generator ON: battery supplies only the power deficit for the rest of the range
        x_hybrid = np.maximum(x_c - electric_target_range, 0)

        t_hybrid = x_hybrid / v_c

        P_b_hybrid = np.maximum(P_c_shaft - P_gen_available, 0)
        E_b_hybrid = P_b_hybrid * t_hybrid

    # Total battery energy at every altitude
    E_b_total = (E_b_to + E_b_climb + E_b_electric + E_b_hybrid)

    # Mission phases occur at different times, so their powers do not need to be added together.
    # Peak battery power required at every altitude:
    P_b_peak = np.maximum.reduce([
        np.full_like(h, P_b_to),
        P_b_climb,
        P_b_electric,
        P_b_hybrid
    ])

    # Battery mass constraints: size for both power and energy requirements
    M_b_energy = J_to_kWh(E_b_total) / e_b
    M_b_power = P_b_peak / p_b

    # Final battery mass at every altitude
    m_b_alt = np.maximum(M_b_energy, M_b_power)

    # Installed battery power at every altitude
    P_batteries_alt = P_b_peak # constant
    P_max_alt = P_gen_available + P_batteries_alt

    # Fuel mass: to be implemented!

    ############ Total (UNCONVERGED!!) aircraft mass (mtow) for the mission ################

    m_tot_alt = np.array([mass_computation(mb, M_TEMP) for mb in m_b_alt]) # one for each altitude
    # n.b. mass optimization requires inner convergence loop?
    
    ############ Cruise altitude optimization ########

    # Maximum allowed cruise altitude: cruise ceiling
    valid_altitudes = (h >= h_obs) #& (h <= 1*h_cruise_ceiling) # /!\ to be corrected (increase N in P_climb sweep)
 

    if not np.any(valid_altitudes):
        return None

    if OPTIMAL_ALT == "total_energy":

        # find the altitude that minimizes the total energy, for given mtow and P_climb_target
        E_valid = np.where(valid_altitudes, E_tot, np.nan) # sets nan for non valid altitudes

        if not np.any(np.isfinite(E_valid)):
            return None

        i_c = np.nanargmin(E_valid)

    elif OPTIMAL_ALT == "cruise_power":

        P_valid = np.where(valid_altitudes, P_c_shaft, np.nan)

        if not np.any(np.isfinite(P_valid)):
            return None

        i_c = np.nanargmin(P_valid)

    elif OPTIMAL_ALT == "custom":

        if H_CUSTOM > h_cruise_ceiling:
            raise ValueError(
                "Custom cruise altitude exceeds service ceiling."
            )

        i_c = np.argmin(np.abs(h - H_CUSTOM))

    elif OPTIMAL_ALT == "total_mass":

        m_valid = np.where(valid_altitudes, m_tot_alt, np.nan)

        if not np.any(np.isfinite(m_valid)):
            return None

        i_c = np.nanargmin(m_valid)

    else:
        raise ValueError(f"Unknown OPTIMAL_ALT option: {OPTIMAL_ALT}")

    ############ Extract optimal cruise altitude values ################

    h_c = h[i_c]

    # Battery values at selected altitude
    m_b_total = m_b_alt[i_c]
    m_tot = m_tot_alt[i_c]

    E_b_total_opt = E_b_total[i_c]
    P_batteries = P_batteries_alt[i_c]
    P_max = P_max_alt[i_c]

    # Individual battery contributions at selected altitude
    E_b_to_opt = E_b_to
    E_b_climb_opt = E_b_climb
    E_b_electric_opt = E_b_electric[i_c]
    E_b_hybrid_opt = E_b_hybrid[i_c]

    P_b_to_opt = P_b_to
    P_b_climb_opt = P_b_climb
    P_b_electric_opt = P_b_electric[i_c]
    P_b_hybrid_opt = P_b_hybrid[i_c]

    # Thrust to weight ratio at takeoff
    T_W_ratio = T_to / W_to
    
    if mtow > M_HEAVY:
        print(f"AIRCRAFT IS HEAVY (light aircraft assumption invalid): mtow = {mtow:.2f} kg > {M_HEAVY} kg")

    ############ Print section #################
    if PRINT:
        print("Takeoff:")
        print(f"Imposed air density in ISA + 18F : rho_imposed = {rho_imposed:.3f} kg/m^3")
        print(f"Wing surface area S = {S:.3f} m^2")
        print(f"C_L_max = {C_L_max:.3f}")
        print(f"Stall speed v_s = {v_s:.2f} m/s")
        print(f"Liftoff speed v_LOF = {v_LOF:.2f} m/s")
        print(f"Ground run x_g = {x_g:.2f} m or x_g = {m_to_ft(x_g):.2f} ft")
        print(f"Air run x_a = {x_a:.2f} m or x_a = {m_to_ft(x_a):.2f} ft")
        print(f"Takeoff thrust T_to = {T_to:.2f} N")
        print(f"Takeoff power P_to = {P_to/1000:.2f} kW or P_to = {W_to_hp(P_to):.2f} hp")
        print(f"Takeoff power to the shaft : P_to_shaft = {P_to_shaft/1000:.2f} kW or P_to_shaft = {W_to_hp(P_to_shaft):.2f} hp")
        print(f"Takeoff energy E_to = {J_to_kWh(E_to):.2f} kWh")

        # print("Climb:")
        print()
        print("Cruise:")
        print(f"Cruise speed: v_c = {ms_to_kt(v_c):.2f} kt or v_c = {v_c:.2f} m/s ({ms_to_kmh(v_c):.2f} km/h)")
        print(f"Considered cruise altitude range: h = [{h_min:.0f},{h_max:.0f}] m")
        #print(f"Cruise C_L_c ranges from C_L_c(h = {h_min:.0f}) = {C_L_c[0]:.3f} to C_L_c(h = {h_max:.0f}) = {C_L_c[-1]:.3f}")
        #print(f"Cruise C_D_c ranges from C_D_c(h = {h_min}) = {C_D_c[0]:.3f} to C_D_c(h = {h_max:.0f}) = {C_D_c[-1]:.3f}")

        print()
        print("At chosen cruise altitude h_c:")
        print(f"Chosen optimal cruise altitude: h_c = {h_c:.2f} m or h = {m_to_ft(h_c):.2f} ft")
        #print(f"Lift coefficient : C_L_c = {C_L_c[i_c]:.3f} at h_c")
        #print(f"Drag coefficient : C_D_c = {C_D_c[i_c]:.3f} at h_c")
        print(f"Thrust required for cruise T_c = {T_c[i_c]:.2f} N at h_c")
        print(f"Power required for cruise P_c = {P_c[i_c]/1000:.2f} kW or {W_to_hp(P_c[i_c]):.2f} hp at h_c")

        print()
        print("Total energy:")
        print(f"Total takeoff time: t_to = {t_to:.2f} s")
        print(f"Climb time: t_climb = {t_climb[i_c]:.2f} s")
        print(f"Cruise time: t_c = {t_c[i_c]:.2f} s for x_c = {m_to_nmi(x_c[i_c]):.2f} nmi")
        print(f"Total energy at h_c : E_tot_opt = {E_tot[i_c]:.2f} kWh")

        print()
        print(f"Minimum battery weight (excl. pressurization, avionics, de-icing , etc...) for {BATTERY} batteries")
        print(f"With target range {m_to_nmi(electric_target_range):.2f} nmi:")
        #print(f"For takeoff only : m_b_to = {m_b_to:.2f} kg (to supply {k_to*100} % of the power = {J_to_kWh(E_to):.2f} kWh)")
        #print(f"For climb only : m_b_climb = {m_b_climb:.2f} kg (to supply {k_climb*100} % of the power = {J_to_kWh(E_climb[i_c]):.2f} kWh to h_c = {h_c/1000:.2f} km)")
        #print(f"For cruise only : m_b_c = {m_b_c:.2f} kg (to supply {J_to_kWh(E_c[i_c]):.2f} kWh at h_c = {h_c/1000:.2f} km)")
        print(f"For the mission : m_b_min = {m_b_total:.2f} kg to supply {E_tot[i_c]:.2f} kWh)")
        #print(f"Meaning that the climb requires {M_b_climb/m_b_total*100:.2f} % of the total battery weight for this altitude.")
        print(f"The total mass including batteries m_tot = {m_tot:.2f} kg")

        print()
        print("Top parameters:")
        if OPTIMAL_ALT == "custom":
            print(f"Chosen custom cruise altitude: h_c = {h_c/1000:.2f} km or h = {m_to_ft(h_c):.2f} ft")
        else: print(f"Optimal cruise altitude: h_c = {h_c/1000:.2f} km or h = {m_to_ft(h_c):.2f} ft")
        print(f"Total energy at h_c : E_tot_opt = {E_tot[i_c]:.2f} kWh")
        print(f"Takeoff power to the shaft : P_to_shaft = {P_to_shaft/1000:.2f} kW or P_to_shaft = {W_to_hp(P_to_shaft):.2f} hp")
        print(f"Power to shaft required for cruise P_c_shaft = {P_c_shaft[i_c]/1000:.2f} kW or P_c_shaft = {W_to_hp(P_c_shaft[i_c]):.2f} hp at h_c")
        print(f"Total installed power (sea level): P_max = {W_to_hp(P_max):.2f} hp or P_max = {P_max/1000:.2f} kW")
        print(f"Total battery mass : m_b_total = {m_b_total:.2f} kg ({(m_b_total/mtow)*100:.2f}) % of mtow -> P_batteries = {W_to_hp(P_batteries):.2f} hp or P_batteries = {P_batteries/1000:.2f} kW") 
        print(f"Thrust to Weight ratio at takeoff: {T_W_ratio:.2f} (typically 0.4-0.6)")   
        print(f"Fuel mass: {K_FUEL_ASSUMED * mtow:.2f} kg ({K_FUEL_ASSUMED*100}) % of mtow")
        print()
    
    return {

    # Selected mission results
    "h_c": h_c,
    "E_tot": E_tot,
    "m_b_total": m_b_total,
    "m_tot": m_tot,

    # Mission phases
    "takeoff": takeoff,
    "climb": climb,
    "cruise": cruise,

    # Battery sizing
    "E_b_total": E_b_total,
    "P_b_peak": P_b_peak,
    "m_b_energy": M_b_energy,
    "m_b_power": M_b_power,
    "m_b_alt": m_b_alt,
    "P_batteries_alt": P_batteries_alt,

    # Cruise altitude optimization
    "h": h,
    "valid_altitudes": valid_altitudes,
    "i_c": i_c,

    # Ceiling information
    "h_cruise_ceiling": climb["h_cruise_ceiling"],
    "h_service_ceiling": climb["h_service_ceiling"],
    "h_absolute_ceiling": climb["h_absolute_ceiling"],

    # Add future results below
    }


""" Iteration over battery mass """

def mass_convergence(S, C_L_max, P_climb_target):

    global mtow, W_to

    mtow = mass_computation(0, M_TEMP) # first "guess" : battery-less weight

    tol = 0.1

    for i in range(100):

        mission = mission_parameters(S, C_L_max, P_climb_target, PRINT=1)

        if mission is None:
            raise RuntimeError("No feasible mission found.")

        m_total = mission["m_tot"]

        error = abs(m_total - mtow) # updated mtow from mission parameters (as a global variable )

        if error < tol:
            mtow = m_total
            W_to = mtow * g

            print(f"Mass has reached convergence! mtow = {mtow:.2f} kg")
            #mission_parameters(S, C_L_max, P_climb_target, PRINT=1)

            if mission["takeoff"]["P_shaft_avg"] >= P_generator:
                print("Takeoff power exceeds generator power.")

            return mission

        # Update global variables for all functions
        mtow = m_total 
        W_to = mtow * g

    else:
        raise RuntimeError("Mass convergence not reached!!")


#h_c, E_tot, mtow, m_battery = mass_convergence(S, C_L_max, P_climb_target)
    

def P_target_climb_convergence(S, C_L_max, P_min=300e3, P_max=600e3, N=200):
    """Sweeps through climb power battery targets and returns the best configuration, such that the optimal
        cruise altitude is as close as possible (from below) to the cruise ceiling. No extra useless battery weight."""

    P_range = np.linspace(P_min, P_max, N)

    h_opt_range = []
    h_ceiling_range = []
    mtow_range = []
    battery_range = []
    energy_range = []
    delta_h_range = []

    # Store complete results for each iteration
    mission_range = []

    for P in P_range:

        mission = mass_convergence(S, C_L_max, P)

        h_opt = mission["h_c"]
        mtow_i = mission["m_tot"]
        m_battery = mission["m_b_total"]
        E_tot = mission["E_tot"]

        h_ceiling = mission["h_cruise_ceiling"]

        delta_h = h_ceiling - h_opt

        mission_range.append(mission)

        h_opt_range.append(h_opt)
        h_ceiling_range.append(h_ceiling)
        mtow_range.append(mtow_i)
        battery_range.append(m_battery)
        energy_range.append(E_tot)
        delta_h_range.append(delta_h)

    # Best solution
    i_best = np.nanargmin(np.abs(delta_h_range))

    P_target_best = P_range[i_best]

    print("\n===== BEST SOLUTION =====")
    print(f"P_target_climb = {P_target_best/1000:.1f} kW")
    print(f"Optimal altitude = {h_opt_range[i_best]/1000:.3f} km")
    print(f"Cruise ceiling = {h_ceiling_range[i_best]/1000:.3f} km")
    print(f"MTOW = {mtow_range[i_best]:.1f} kg")
    print(f"Battery mass = {battery_range[i_best]:.1f} kg")

    # Final selected solution
    best_mission = mission_range[i_best]

    # Print final mission results
    # (See note below about separating printing from calculations)

    return {

        "best_mission": best_mission,
        "P_target_best": P_target_best,

        "P_range": P_range,
        "h_opt_range": np.array(h_opt_range),
        "h_ceiling_range": np.array(h_ceiling_range),
        "mtow_range": np.array(mtow_range),
        "battery_range": np.array(battery_range),
        "energy_range": np.array(energy_range),
        "delta_h_range": np.array(delta_h_range),

        "mission_range": mission_range,
    }


#################### Final function call #########################

results = P_target_climb_convergence(S, C_L_max)

# Selected aircraft configuration
mission = results["best_mission"]

mtow = mission["m_tot"]
h_c = mission["h_c"]
m_battery = mission["m_b_total"]

#####################################
#              PLOTS                #
#####################################

def _add_altitude_markers(ax, h_cruise=None, h_service=None,
                          h_absolute=None, h_opt=None):

    markers = [
        (h_cruise, "green", "--", "Cruise ceiling"),
        (h_service, "orange", "-.", "Service ceiling"),
        (h_absolute, "red", ":", "Absolute ceiling"),
        (h_opt, "purple", "-", "Optimal cruise altitude")
    ]

    for altitude, color, style, label in markers:

        if altitude is not None and np.isfinite(altitude):
            ax.axvline(
                altitude / 1000,
                color=color,
                linestyle=style,
                linewidth=1.5,
                label=f"{label} ({altitude/1000:.2f} km)"
            )

def plot_takeoff_power_mass():

    m_range = np.linspace(3000, 8000, 120)
    CL_max_range = [4, 4.5, 5, 5.5, 6]

    global W_to, P_to_shaft

    W_to_original = W_to
    P_to_original = P_to_shaft

    fig, ax = plt.subplots(figsize=(9, 6))

    try:

        for CL in CL_max_range:

            P_range = np.full_like(m_range, np.nan)

            for i, m in enumerate(m_range):

                W_to = m * g

                result = takeoff_model(S, CL)

                if result is not None:
                    P_range[i] = W_to_hp(result["P_shaft_avg"])

            ax.plot(
                m_range,
                P_range,
                linewidth=2.5,
                label=fr"$C_{{L_{{max}}}}={CL}$"
            )

    finally:
        W_to = W_to_original
        P_to_shaft = P_to_original

    ax.axvline(
        mtow,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Converged MTOW ({mtow:.0f} kg)"
    )

    ax.set_xlabel("Takeoff mass [kg]")
    ax.set_ylabel("Required takeoff shaft power [hp]")
    ax.set_title("Takeoff Shaft Power vs Aircraft Mass")

    ax.set_xlim(m_range[0], m_range[-1])
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()

def plot_optimal_altitude_mass():

    m_range = np.linspace(3000, 8000, 100)

    global W_to, P_max, P_batteries
    global P_to_shaft, k_to, k_climb

    P_climb_target = results["P_target_best"]

    original = {
        "W_to": W_to,
        "P_max": P_max,
        "P_batteries": P_batteries,
        "P_to_shaft": P_to_shaft,
        "k_to": k_to,
        "k_climb": k_climb
    }

    h_opt_range = np.full_like(m_range, np.nan)

    try:

        for i, m in enumerate(m_range):

            W_to = m * g

            try:

                result = mission_parameters(
                    S,
                    C_L_max,
                    P_climb_target,
                    PRINT=0
                )

                if result is not None:
                    h_opt_range[i] = result["h_c"] / 1000

            except (ValueError, TypeError, IndexError, KeyError):
                continue

    finally:

        W_to = original["W_to"]
        P_max = original["P_max"]
        P_batteries = original["P_batteries"]
        P_to_shaft = original["P_to_shaft"]
        k_to = original["k_to"]
        k_climb = original["k_climb"]

    fig, ax = plt.subplots(figsize=(9, 6))

    ax.plot(
        m_range,
        h_opt_range,
        color="tab:blue",
        linewidth=2.5,
        label="Optimal cruise altitude"
    )

    ax.axvline(
        mtow,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Design MTOW ({mtow:.0f} kg)"
    )

    ax.set_xlabel("Assumed takeoff mass [kg]")
    ax.set_ylabel("Optimal cruise altitude [km]")
    ax.set_title("Optimal Cruise Altitude vs Aircraft Mass")

    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()


def plot_power_available():

    global W_to
    W_to = mtow * g

    P_climb_target = results["P_target_best"]

    # Climb performance
    climb = climb_model(S, C_L_max_2, P_climb_target)

    if climb is None:
        raise ValueError("No feasible climb solution.")

    h_service_ceiling = climb["h_service_ceiling"]
    h_absolute_ceiling = climb["h_absolute_ceiling"]
    h_cruise_ceiling = climb["h_cruise_ceiling"]

    P_battery_climb = climb["P_battery_climb"]

    # Generator power available
    P_generator_available = power_available_shaft(
        P_generator, h
    )

    # Combined power available during climb
    P_climb_available = (
        P_generator_available + P_battery_climb
    )

    # Cruise power required
    C_L_c = W_to / (0.5 * rho_c * v_c**2 * S)
    C_D_c = CD_0 + C_L_c**2 / (np.pi * e * AR)

    T_c = 0.5 * rho_c * v_c**2 * S * C_D_c
    P_c_shaft = T_c * v_c / eta_p

    # Total installed battery power
    P_battery_installed = np.full_like(
        h, P_batteries, dtype=float
    )

    P_total_available = (
        P_generator_available + P_battery_installed
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        h / 1000,
        W_to_hp(P_generator_available),
        linewidth=2.5,
        label="Generator power available"
    )

    ax.plot(
        h / 1000,
        W_to_hp(P_battery_climb),
        linewidth=2.5,
        label="Battery power used during climb"
    )

    ax.plot(
        h / 1000,
        W_to_hp(P_climb_available),
        color="tab:green",
        linewidth=2.5,
        label="Combined climb power"
    )

    ax.axhline(
        W_to_hp(P_generator),
        color="black",
        linestyle=":",
        linewidth=1.5,
        label="Target climb power (1 MW)"
    )

    ax.plot(
        h / 1000,
        W_to_hp(P_c_shaft),
        color="tab:red",
        linewidth=2.5,
        label="Required cruise shaft power"
    )

    ax.plot(
        h / 1000,
        W_to_hp(P_total_available),
        color="tab:purple",
        linestyle="--",
        linewidth=2,
        label="Total installed power available"
    )

    _add_altitude_markers(
        ax,
        h_cruise=h_cruise_ceiling,
        h_service=h_service_ceiling,
        h_absolute=h_absolute_ceiling,
        h_opt=h_c
    )

    ax.set_xlabel("Altitude [km]")
    ax.set_ylabel("Shaft power [hp]")
    ax.set_title("Available and Required Shaft Power vs Altitude")

    ax.set_xlim(h_min / 1000, h_max / 1000)
    ax.set_ylim(bottom=0)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)

    fig.tight_layout()


def plot_climb_characteristics():

    global W_to
    W_to = mtow * g

    P_climb_target = results["P_target_best"]

    # Climb performance
    result = climb_model(S, C_L_max_2, P_climb_target)

    if result is None:
        raise ValueError("No feasible climb solution.")

    ROC_climb = result["ROC"]
    gamma_climb = result["gamma"]
    V_climb = result["V_climb"]

    h_service_ceiling = result["h_service_ceiling"]
    h_absolute_ceiling = result["h_absolute_ceiling"]
    h_cruise_ceiling = result["h_cruise_ceiling"]

    P_battery_climb = result["P_battery_climb"]

    # Stall speed
    V_stall = np.sqrt(
        2 * W_to / (rho_c * S * C_L_max_2)
    )

    V_climb_kt = ms_to_kt(V_climb)
    V_stall_kt = ms_to_kt(V_stall)

    # --------------------------------------------------
    # FIGURE
    # --------------------------------------------------

    fig, axes = plt.subplots(
        4, 1,
        figsize=(11, 13),
        sharex=True,
        constrained_layout=True
    )

    ax1, ax2, ax3, ax4 = axes

    altitude = h / 1000

    # --------------------------------------------------
    # 1. RATE OF CLIMB
    # --------------------------------------------------

    ax1.plot(
        altitude,
        ms_to_fpm(ROC_climb),
        color="tab:blue",
        linewidth=2.2,
        label="Maximum rate of climb"
    )

    ax1.axhline(
        1500,
        color="black",
        linestyle=":",
        linewidth=1.2,
        label="Initial climb requirement (1500 fpm)"
    )

    ax1.axhline(
        300,
        color="tab:green",
        linestyle="--",
        linewidth=1.2,
        label="Cruise ceiling criterion (300 fpm)"
    )

    ax1.axhline(
        100,
        color="tab:orange",
        linestyle="-.",
        linewidth=1.2,
        label="Service ceiling criterion (100 fpm)"
    )

    ax1.set_ylabel("Rate of climb [fpm]")
    ax1.set_title("Maximum Rate of Climb")
    ax1.set_ylim(bottom=0)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc="best", fontsize=8)

    # --------------------------------------------------
    # 2. CLIMB ANGLE
    # --------------------------------------------------

    ax2.plot(
        altitude,
        np.degrees(gamma_climb),
        color="tab:orange",
        linewidth=2.2,
        label="Climb angle at maximum ROC"
    )

    ax2.set_ylabel("Climb angle [deg]")
    ax2.set_title("Climb Angle")
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc="best", fontsize=8)

    # --------------------------------------------------
    # 3. CLIMB SPEED AND STALL SPEED
    # --------------------------------------------------

    ax3.plot(
        altitude,
        V_climb_kt,
        color="tab:green",
        linewidth=2.2,
        label="Optimal climb speed"
    )

    ax3.plot(
        altitude,
        V_stall_kt,
        color="tab:red",
        linestyle="--",
        linewidth=2,
        label="Stall speed"
    )

    ax3.set_ylabel("True airspeed [kt]")
    ax3.set_title("Climb and Stall Speeds")
    ax3.set_ylim(bottom=0)
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc="best", fontsize=8)

    # --------------------------------------------------
    # 4. BATTERY POWER DURING CLIMB
    # --------------------------------------------------

    ax4.plot(
        altitude,
        P_battery_climb / 1000,
        color="tab:purple",
        linewidth=2.2,
        label="Battery power during climb"
    )

    ax4.set_ylabel("Battery power [kW]")
    ax4.set_xlabel("Altitude [km]")
    ax4.set_title("Battery Contribution During Climb")
    ax4.set_ylim(bottom=0)
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc="best", fontsize=8)

    # --------------------------------------------------
    # ALTITUDE MARKERS
    # --------------------------------------------------

    altitude_markers = [
        (h_cruise_ceiling, "Cruise ceiling", "tab:green", "--"),
        (h_service_ceiling, "Service ceiling", "tab:orange", "-."),
        (h_absolute_ceiling, "Absolute ceiling", "tab:red", ":"),
        (h_c, "Selected cruise altitude", "black", "--"),
    ]

    for ax in axes:

        for altitude_value, label, color, linestyle in altitude_markers:

            if altitude_value is not None:

                ax.axvline(
                    altitude_value / 1000,
                    color=color,
                    linestyle=linestyle,
                    linewidth=1.3,
                    alpha=0.8
                )

    # Add altitude marker labels only to the first subplot
    for altitude_value, label, color, linestyle in altitude_markers:

        if altitude_value is not None:

            ax1.plot(
                [],
                [],
                color=color,
                linestyle=linestyle,
                linewidth=1.5,
                label=f"{label} ({altitude_value/1000:.2f} km)"
            )

    ax1.legend(loc="best", fontsize=8)

    # --------------------------------------------------
    # FINAL FORMATTING
    # --------------------------------------------------

    fig.suptitle(
        f"Climb Characteristics (MTOW = {mtow:.0f} kg, "
        f"Climb Power Target = {P_climb_target/1000:.0f} kW)",
        fontsize=14
    )

def plot_battery_mass_and_cruise_energy():

    global W_to
    W_to = mtow * g

    P_climb_target = results["P_target_best"]

    # Climb performance
    result = climb_model(S, C_L_max_2, P_climb_target)

    if result is None:
        raise ValueError("No feasible climb solution.")

    x_climb = result["x_climb"]

    h_service_ceiling = result["h_service_ceiling"]
    h_absolute_ceiling = result["h_absolute_ceiling"]
    h_cruise_ceiling = result["h_cruise_ceiling"]

    P_battery_climb = result["P_battery_climb"]
    E_battery_climb = result["E_battery_climb"]

    # Cruise aerodynamic characteristics
    C_L_c = W_to / (0.5 * rho_c * v_c**2 * S)
    C_D_c = CD_0 + C_L_c**2 / (np.pi * e * AR)

    T_c = 0.5 * rho_c * v_c**2 * S * C_D_c
    P_c_shaft = T_c * v_c / eta_p

    # Generator power available
    P_gen_available = power_available_shaft(
        P_generator, h
    )

    # Electric cruise distance, accounting for takeoff
    # and climb distance
    x_c_electric = electric_target_range - (x_to + x_climb)

    t_c_electric = np.maximum(x_c_electric, 0) / v_c

    # Electric cruise battery energy
    E_electric_J = P_c_shaft * t_c_electric

    # Total battery energy: climb + electric cruise
    E_battery_total = (
        E_battery_climb + E_electric_J
    )

    E_battery_total_kWh = J_to_kWh(E_battery_total)

    # Battery power required during electric cruise
    P_b_cruise = P_c_shaft

    # Maximum climb battery power required up to each altitude
    P_b_climb_peak = np.maximum.accumulate(
        np.nan_to_num(P_battery_climb, nan=0.0)
    )

    # Maximum battery power across climb and electric cruise
    P_b_peak = np.maximum(
        P_b_climb_peak,
        P_b_cruise
    )

    # Battery mass constraints
    m_b_energy = E_battery_total_kWh / e_b
    m_b_power = P_b_peak / p_b

    m_battery = np.maximum(
        m_b_energy,
        m_b_power
    )

    # Feasible altitudes
    valid = (
        np.isfinite(x_climb)
        & np.isfinite(E_battery_climb)
        & (x_c_electric > 0)
    )

    if h_cruise_ceiling is not None:
        valid &= h <= h_cruise_ceiling
    else:
        valid[:] = False

    E_battery_total_kWh = np.where(
        valid, E_battery_total_kWh, np.nan
    )

    m_b_energy = np.where(
        valid, m_b_energy, np.nan
    )

    m_b_power = np.where(
        valid, m_b_power, np.nan
    )

    m_battery = np.where(
        valid, m_battery, np.nan
    )

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(10, 9),
        sharex=True
    )

    # 1. Battery energy
    ax1.plot(
        h / 1000,
        E_battery_total_kWh,
        color="tab:blue",
        linewidth=2.5,
        label="Climb + electric cruise energy"
    )

    ax1.set_ylabel("Battery energy [kWh]")
    ax1.set_title("Battery Energy Requirement")
    ax1.set_ylim(bottom=0)
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    # 2. Battery mass
    ax2.plot(
        h / 1000,
        m_b_energy,
        color="tab:blue",
        linewidth=2,
        linestyle="--",
        label="Energy-limited battery mass"
    )

    ax2.plot(
        h / 1000,
        m_b_power,
        color="tab:orange",
        linewidth=2,
        linestyle=":",
        label="Power-limited battery mass"
    )

    ax2.plot(
        h / 1000,
        m_battery,
        color="tab:green",
        linewidth=2.5,
        label="Required battery mass"
    )

    ax2.set_xlabel("Cruise altitude [km]")
    ax2.set_ylabel("Battery mass [kg]")
    ax2.set_title("Battery Mass Requirement")
    ax2.set_ylim(bottom=0)
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    for ax in (ax1, ax2):

        _add_altitude_markers(
            ax,
            h_cruise=h_cruise_ceiling,
            h_service=h_service_ceiling,
            h_absolute=h_absolute_ceiling,
            h_opt=h_c
        )

        ax.legend(fontsize=8)

    fig.suptitle(
        f"Climb + Electric Cruise Battery Sizing "
        f"({m_to_nmi(electric_target_range):.0f} nmi electric range)",
        fontsize=13
    )

    fig.tight_layout()


def plot_climb_power_altitude():

    P_range = results["P_range"] / 1000  # [kW]

    h_opt = results["h_opt_range"] / 1000
    h_ceiling = results["h_ceiling_range"] / 1000

    mtow_range = results["mtow_range"]

    # Extract energy at the selected optimal altitude
    energy_range = np.array([
        mission["E_tot"][mission["i_c"]]
        if mission is not None else np.nan
        for mission in results["mission_range"]
    ])  # [kWh]

    # Selected climb power
    P_best = results["P_target_best"] / 1000

    # --------------------------------------------------
    # FIGURE
    # --------------------------------------------------

    fig, axes = plt.subplots(
        3, 1,
        figsize=(10, 11),
        sharex=True
    )

    ax1, ax2, ax3 = axes

    # --------------------------------------------------
    # 1. OPTIMAL ALTITUDE AND CRUISE CEILING
    # --------------------------------------------------

    ax1.plot(
        P_range,
        h_opt,
        linewidth=2.5,
        label="Optimal cruise altitude"
    )

    ax1.plot(
        P_range,
        h_ceiling,
        linewidth=2.5,
        label="Cruise ceiling"
    )

    ax1.set_ylabel("Altitude [km]")
    ax1.set_title("Optimal Cruise Altitude vs Climb Power")
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=9)

    # --------------------------------------------------
    # 2. CONVERGED MTOW
    # --------------------------------------------------

    ax2.plot(
        P_range,
        mtow_range,
        color="tab:green",
        linewidth=2.5,
        label="Converged MTOW"
    )

    ax2.set_ylabel("MTOW [kg]")
    ax2.set_title("Converged Aircraft Mass")
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=9)

    # --------------------------------------------------
    # 3. TOTAL MISSION ENERGY AT OPTIMAL ALTITUDE
    # --------------------------------------------------

    ax3.plot(
        P_range,
        energy_range,
        color="tab:orange",
        linewidth=2.5,
        label="Total mission energy"
    )

    ax3.set_ylabel("Energy [kWh]")
    ax3.set_xlabel("Target climb power [kW]")
    ax3.set_title("Mission Energy at Optimal Cruise Altitude")
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)

    # --------------------------------------------------
    # SELECTED CLIMB POWER MARKER
    # --------------------------------------------------

    for ax in axes:

        ax.axvline(
            P_best,
            color="black",
            linestyle="--",
            linewidth=1.5,
            alpha=0.8
        )

    ax1.axvline(
        P_best,
        color="black",
        linestyle="--",
        linewidth=1.5,
        label=f"Selected power ({P_best:.0f} kW)"
    )

    ax1.legend(fontsize=9)

    # --------------------------------------------------
    # FINAL FORMATTING
    # --------------------------------------------------

    fig.suptitle(
        "Aircraft Performance vs Target Climb Power",
        fontsize=14
    )

    fig.tight_layout()

def plot_power_tradeoff():

    global P_generator, P_max, P_batteries
    global W_to, mtow, P_to_shaft, k_to, k_climb

    P_climb_target = results["P_target_best"]

    # Sweep generator rated power.
    # Battery power is sized independently by mission_parameters.

    P_range = np.linspace(500e3, 2000e3, 50)

    mass_range = np.full_like(P_range, np.nan)
    h_opt_range = np.full_like(P_range, np.nan)
    gamma_sl_range = np.full_like(P_range, np.nan)
    ROC_sl_range = np.full_like(P_range, np.nan)

    P_to_required = np.full_like(P_range, np.nan)
    P_available_total = np.full_like(P_range, np.nan)

    original = {
        "P_generator": P_generator,
        "P_max": P_max,
        "P_batteries": P_batteries,
        "W_to": W_to,
        "mtow": mtow,
        "P_to_shaft": P_to_shaft,
        "k_to": k_to,
        "k_climb": k_climb
    }

    try:

        for i, P in enumerate(P_range):

            P_generator = P

            try:
                mission = mass_convergence(
                    S,
                    C_L_max,
                    P_climb_target
                )

            except (ValueError, TypeError, RuntimeError):
                continue

            if mission is None:
                continue

            # Converged aircraft mass
            mtow = mission["m_tot"]
            W_to = mtow * g

            mass_range[i] = mtow
            h_opt_range[i] = mission["h_c"] / 1000

            # Takeoff power requirement
            takeoff_result = takeoff_model(S, C_L_max)

            if takeoff_result is None:
                continue

            P_to_required[i] = takeoff_result["P_shaft_avg"]

            # Total available power at sea level
            P_available_total[i] = P_generator + P_batteries

            # Initial climb performance
            climb_result = climb_model(
                S,
                C_L_max_2,
                P_climb_target
            )

            if climb_result is None:
                continue

            ROC_sl_range[i] = ms_to_fpm(
                climb_result["ROC"][0]
            )

            gamma_sl_range[i] = np.degrees(
                climb_result["gamma"][0]
            )

    finally:

        P_generator = original["P_generator"]
        P_max = original["P_max"]
        P_batteries = original["P_batteries"]
        W_to = original["W_to"]
        mtow = original["mtow"]
        P_to_shaft = original["P_to_shaft"]
        k_to = original["k_to"]
        k_climb = original["k_climb"]

    # Takeoff feasibility
    takeoff_feasible = (
        np.isfinite(P_to_required)
        & np.isfinite(P_available_total)
        & (P_to_required <= P_available_total)
    )

    P_range_kW = P_range / 1000

    fig, axes = plt.subplots(
        2, 2,
        figsize=(13, 9)
    )

    ax1, ax2, ax3, ax4 = axes.flatten()

    plot_data = [
        (
            ax1,
            mass_range,
            "Aircraft mass [kg]",
            "Converged MTOW",
            "tab:blue"
        ),
        (
            ax2,
            h_opt_range,
            "Optimal cruise altitude [km]",
            "Optimal Cruise Altitude",
            "tab:orange"
        ),
        (
            ax3,
            gamma_sl_range,
            "Climb angle [deg]",
            "Initial Climb Angle at Sea Level",
            "tab:green"
        ),
        (
            ax4,
            ROC_sl_range,
            "Rate of climb [fpm]",
            "Initial Rate of Climb at Sea Level",
            "tab:red"
        )
    ]

    for ax, values, ylabel, title, color in plot_data:

        ax.plot(
            P_range_kW,
            values,
            color=color,
            linewidth=2.5,
            label=title
        )

        ax.axvline(
            original["P_generator"] / 1000,
            color="black",
            linestyle="--",
            linewidth=1.5,
            label="Current generator rating"
        )

        ax.set_xlabel("Generator rated shaft power [kW]")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)

    # Add the takeoff feasibility information
    ax1.scatter(
        P_range_kW[takeoff_feasible],
        mass_range[takeoff_feasible],
        marker="o",
        facecolors="none",
        edgecolors="green",
        s=55,
        label="Takeoff feasible"
    )

    ax1.legend()

    fig.suptitle(
        "Aircraft Performance vs Generator Rated Power",
        fontsize=14
    )

    fig.tight_layout()

def plot_total_energy():

    global W_to
    W_to = mtow * g

    # Retrieve the selected mission
    mission = mission_parameters(
        S,
        C_L_max,
        results["P_target_best"],
        PRINT=0
    )

    if mission is None:
        raise ValueError(
            "No feasible mission at the converged mass."
        )

    h_c_plot = mission["h_c"]
    E_tot_plot = mission["E_tot"]

    # Retrieve climb ceiling information
    climb_result = mission["climb"]

    h_service_ceiling = climb_result["h_service_ceiling"]
    h_absolute_ceiling = climb_result["h_absolute_ceiling"]
    h_cruise_ceiling = climb_result["h_cruise_ceiling"]

    # Cruise power required
    cruise_result = mission["cruise"]
    P_c_shaft = cruise_result["P_c_shaft"]

    # Total available shaft power
    P_generator_available = power_available_shaft(
        P_generator, h
    )

    P_battery_available = np.full_like(
        h, P_batteries, dtype=float
    )

    P_available = (
        P_generator_available + P_battery_available
    )

    # Feasibility
    valid = (
        np.isfinite(E_tot_plot)
        & (P_c_shaft <= P_available)
    )

    if h_cruise_ceiling is not None and h_absolute_ceiling is not None:
        valid &= h <= h_absolute_ceiling
    else:
        valid[:] = False

    E_tot_plot = np.where(
        valid, E_tot_plot, np.nan
    )

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(
        h / 1000,
        E_tot_plot,
        color="tab:blue",
        linewidth=2.5,
        label="Total mission energy"
    )

    # Find actual minimum on feasible part of curve
    if np.any(np.isfinite(E_tot_plot)):

        i_min = np.nanargmin(E_tot_plot)

        h_min_energy = h[i_min]
        E_min_energy = E_tot_plot[i_min]

        ax.scatter(
            h_min_energy / 1000,
            E_min_energy,
            color="purple",
            s=65,
            zorder=5,
            label=f"Minimum energy ({h_min_energy/1000:.2f} km)"
        )

    # Mark selected mission altitude
    i_opt = np.argmin(np.abs(h - h_c_plot))

    if np.isfinite(E_tot_plot[i_opt]):

        ax.scatter(
            h_c_plot / 1000,
            E_tot_plot[i_opt],
            color="black",
            marker="x",
            s=75,
            zorder=6,
            label=f"Selected altitude ({h_c_plot/1000:.2f} km)"
        )

    _add_altitude_markers(
        ax,
        h_cruise=h_cruise_ceiling,
        h_service=h_service_ceiling,
        h_absolute=h_absolute_ceiling
    )

    ax.set_xlabel("Cruise altitude [km]")
    ax.set_ylabel("Total mission energy [kWh]")
    ax.set_title("Total Mission Energy vs Cruise Altitude")

    ax.set_xlim(h_min / 1000, h_max / 1000)
    ax.set_ylim(bottom=0)

    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

    fig.tight_layout()

#     # S_tradeoff_plots()
#     # climb_performance_plots()
#     # cruise_performance_plots() 
#     # aerodynamic_efficiency_plots()
#     # total_energy_vs_hc()
#     # mission_energy_plots()
#     # climb_profile_plots()

if PLOTS:
    plot_power_available()
    plot_climb_characteristics()
    plot_total_energy()
    plot_climb_power_altitude()
    #plot_takeoff_power_mass()
    #plot_battery_mass_and_cruise_energy()
    #plot_optimal_altitude_mass()
    #plot_power_tradeoff()


plt.show()