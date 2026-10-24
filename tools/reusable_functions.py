g = 9.81 # [m/s^2]

def air_density(h):

    """
    Range of validity: h = [0, 11 000] m 
    """
    # ISA constants
    rho0 = 1.225      # Standard sea-level air density [kg/m^3] 
    T0 = 288.15       # Standard sea-level air temperature [K]
    L = 0.0065        # Temperature rate of change with altitude [K/m]
    R = 287.05        # Specific gas constant of air [J/(kg*K)]

    rho = rho0 * (1 - L * h / T0)**(g / (R * L) - 1) #

    return rho