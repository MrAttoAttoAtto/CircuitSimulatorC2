
import math
import subprocess
import time
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg


# Initial guess
input_vec = [3, 0, 1e-3]

# Resistance in Ohms
R = 1e-3

# Temperature (kelvin)
T = 293.5

# Boltzmann constant
k = 1.38064852e-23
# Charge on an electron
q = 1.60217662e-19

# Thermal voltage
V_T = k*T/q

# Diode ideality (1 is ideal)
n = 1

# Diode saturation current
I_s = 1e-12 # LOW

# Frequency of the AC source in Hertz
f = 10

# AC peak
Vin_AC_peak = 40

# DC component
Vin_DC = 0

sin_multiplier = f*2*math.pi

# Combo of AC and DC power source
def get_Vin(t):
    return Vin_AC_peak*math.sin(sin_multiplier*t) + Vin_DC

DC_slope = 10
DC_start = -21

def get_Vin2(t):
    return t*DC_slope + DC_start


# Starting time, and size of time steps
t = 1e-5
delta_t = 1e-5

# Breakdown voltage
breakdown_v = 20 # Volts

def get_current_through_diode(anode_v, cathode_v):
    if anode_v-cathode_v < -breakdown_v: # Broke down!
        return -I_s*math.exp( (-breakdown_v-(anode_v-cathode_v))/(n*V_T) )
    else:
        return I_s*(math.exp((anode_v-cathode_v)/(n*V_T)) - 1)

gcd = get_current_through_diode

def get_diode_conductance(anode_v, cathode_v):
    if anode_v-cathode_v < -breakdown_v: # Broke down!
        return (I_s/(n*V_T)) * math.exp((-breakdown_v-(anode_v-cathode_v))/(n*V_T))
    else:
        return (I_s/(n*V_T)) * math.exp((v1-v2)/(n*V_T))

gdc = get_diode_conductance


# Holds results for plotting
results = [[],[]]

start = time.time()
while True:

    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    iv = input_vec[2]

    # Calculate the values in result vector
    result_vector = [0, 0, 0]

    result_vector[0] = -(gcd(v1, v2) - iv)
    result_vector[1] = -(v2/R - gcd(v1, v2))
    result_vector[2] = -(v1-get_Vin2(t)) # Put back T!

    #if get_Vin2(t) < -20:
    #    print(gcd(v1, v2))

    # Create the Jacobian for this input vector
    g = get_diode_conductance(v1, v2)
    jac = np.array([[g, -g, -1],
                    [-g, g + 1/R, 0],
                    [1, 0, 0]])
    
    '''
    # Calculate the new (better) input vector by doing new x = old x - J(x)^(-1)*F(x), where J(x)^(-1) is the inverse Jacobian of x, and F(x) is the result vector given by x
    inv_jac = lapack_inverse(jac)
    res = np.dot(inv_jac, np.array(result_vector))
    input_vec -= res
    '''

    delta_in = scipy.linalg.lapack.dgesv(jac, result_vector)[2]
    input_vec += delta_in

    # If the better guess is indistinguishable from the prior guess, we probably have the right value...
    if (abs(delta_in) < 1e-5).all():
        results[0].append(t)
        results[1].append(iv)

        # Updates the variables like time and the "old" voltages
        t += delta_t

        if t > (22/10):
            print(time.time()-start)
            # Plots nice graph
            fig, ax = plt.subplots(1, 1, figsize=(20, 9))

            ax.set_xlabel("Voltage (V)")
            ax.set_ylabel("Current (A)")
            ax.set_title("Current vs Voltage for a diode")
            
            ax.axhline(0, color='black')
            ax.axvline(0, color='black')

            ax.plot([get_Vin2(t) for t in results[0]], results[1], markersize=2)
            # '''
            plt.show()
            # '''

            '''
            plt.savefig("fig.svg", format='svg', dpi=300)
            subprocess.call(["/usr/bin/open", "fig.svg"])
            '''

            break
