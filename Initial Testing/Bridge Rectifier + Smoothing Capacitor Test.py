import math
import subprocess
import time
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg

# GMin
gmin = 1e-12

# Initial guess
input_vec = [3, 0, 0, 1e-3]

# Resistance in Ohms
R = 5e3

# Capacitance in Farads
C = 500e-6

# Temperature (kelvin)
T = 293.5

# Boltzmann constant
k = 1.38064852e-23
# Charge on an electron
q = 1.60217662e-19

# Thermal voltage
V_T = k*T/q

# Diode ideality (1 is ideal) (all diodes)
n = 1

nV_T = n * V_T

# Diode saturation current (all diodes)
I_s = 1e-12 # LOW

I_s_nV_T = I_s/nV_T

# Frequency of the AC source in Hertz
f = 0.25

# AC peak
Vin_AC_peak = 10*math.sqrt(2)

# DC component
Vin_DC = 0

sin_multiplier = f*2*math.pi

# Combo of AC and DC power source
def get_Vin(t):
    return Vin_AC_peak*math.sin(sin_multiplier*t) + Vin_DC


# Starting time, and size of time steps
t = 1e-5
delta_t = 1e-5

old_v2 = 0
old_v3 = 0

# Deriv. for current from capacitor
g_c1 = C/delta_t

# Holds results for plotting
results = [[],[],[],[],[]]

# The number of iterastions this time step has taken - too many and we'll reset the input vector
num_tries = 0
start = time.time()
while True:

    # Load the variables from the input vector
    v1 = get_Vin(t) #input_vec[0]
    v2 = input_vec[1]
    v3 = input_vec[2]
    iv = input_vec[3]

    # Calculate the values in result vector BUT MINUSED
    result_vector = [0, 0, 0, 0]

    result_vector[0] = -(I_s*(math.exp((v1-v2)/(nV_T)) - 1) - I_s*(math.exp((v3-v1)/(nV_T)) - 1) - iv) # I at 1
    result_vector[1] = -(C*(v2-old_v2-v3+old_v3)/delta_t + (v2-v3)/R - I_s*(math.exp((v1-v2)/(nV_T)) - 1) - I_s*(math.exp((-v2)/(nV_T)) - 1)) # I at 2
    result_vector[2] = -(I_s*(math.exp((v3-v1)/(nV_T)) - 1) + I_s*(math.exp((v3)/(nV_T)) - 1) - (v2-v3)/R - C*(v2-old_v2-v3+old_v3)/delta_t) # I at 3
    result_vector[3] = -(v1-get_Vin(t)) # P.D. at 1

    # Create the Jacobian for this input vector
    d1 = max(I_s_nV_T * math.exp((v1-v2)/(nV_T)), gmin)
    d2 = max(I_s_nV_T * math.exp((v3-v1)/(nV_T)), gmin)
    d3 = max(I_s_nV_T * math.exp((-v2)/(nV_T)), gmin)
    d4 = max(I_s_nV_T * math.exp((v3)/(nV_T)), gmin)
    jac = np.array([[d1 + d2, -d1, -d2, -1],
                    [-d1, 1/R + d1 + d3 + g_c1, -1/R - g_c1, 0],
                    [-d2, -1/R - g_c1, d2 + d4 + 1/R + g_c1, 0],
                    [1, 0, 0, 0]])
    
    '''
    # Calculate the new (better) input vector by doing new x = old x - J(x)^(-1)*F(x), where J(x)^(-1) is the inverse Jacobian of x, and F(x) is the result vector given by x
    inv_jac = lapack_inverse(jac)
    res = np.dot(inv_jac, np.array(result_vector))
    input_vec -= res
    '''

    delta_in = scipy.linalg.lapack.dgesv(jac, result_vector)[2]
    input_vec += delta_in

    #print(delta_in)

    #print(delta_in)
    #print(input_vec)
    #print()

    # If the better guess is indistinguishable from the prior guess, we probably have the right value...
    if (abs(delta_in) < 1e-5).all():
        results[0].append(t)
        results[1].append(v2-v3)
        results[2].append(v2)
        results[3].append(v3)

        # Updates the variables like time and the "old" voltages
        t += delta_t
        old_v2 = v2
        old_v3 = v3
        num_tries = 0

        if t > 60*8/60:
            print(time.time()-start)
            # Plots nice graph
            fig, ax = plt.subplots(1, 1, figsize=(20, 9))
            ax.scatter(results[0], results[1])
            ax.scatter(results[0], [get_Vin(t) for t in results[0]])
            #ax.scatter(results[0], results[2])
            #ax.scatter(results[0], results[3])
            #print(results[3])
            #'''
            plt.show()
            #'''

            '''
            plt.savefig("fig.svg", format='svg', dpi=300)
            subprocess.call(["/usr/bin/open", "fig.svg"])
            '''

            break

    else:
        num_tries += 1
        if num_tries % 100 == 0:
            print(num_tries)
