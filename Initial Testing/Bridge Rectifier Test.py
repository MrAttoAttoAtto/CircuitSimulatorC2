import math
import subprocess
import time
import json
from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg

# Initial guess
input_vec = [3, 0, 0, 1e-3]

# Resistance in Ohms
R = 5e3

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
f = 60

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


# Holds results for plotting
results = [[],[]]

start = time.time()
while True:

    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    v3 = input_vec[2]
    iv = input_vec[3]

    # Calculate the values in result vector BUT MINUSED
    result_vector = [0, 0, 0, 0]

    result_vector[0] = -(I_s*(math.exp((v1-v2)/(nV_T)) - 1) - I_s*(math.exp((v3-v1)/(nV_T)) - 1) - iv)
    result_vector[1] = -((v2-v3)/R - I_s*(math.exp((v1-v2)/(nV_T)) - 1) - I_s*(math.exp((-v2)/(nV_T)) - 1))
    result_vector[2] = -(I_s*(math.exp((v3-v1)/(nV_T)) - 1) + I_s*(math.exp((v3)/(nV_T)) - 1) - (v2-v3)/R)
    result_vector[3] = -(v1-get_Vin(t))

    # Create the Jacobian for this input vector
    d1 = I_s_nV_T * math.exp((v1-v2)/(nV_T))
    d2 = I_s_nV_T * math.exp((v3-v1)/(nV_T))
    d3 = I_s_nV_T * math.exp((-v2)/(nV_T))
    d4 = I_s_nV_T * math.exp((v3)/(nV_T))
    jac = np.array([[d1 + d2, -d1, -d2, -1],
                    [-d1, 1/R + d1 + d3, -1/R, 0],
                    [-d2, -1/R, d2 + d4 + 1/R, 0],
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
    #print(input_vec)
    #print()

    # If the better guess is indistinguishable from the prior guess, we probably have the right value...
    if (abs(delta_in) < 1e-5).all():
        results[0].append(t)
        results[1].append(v2-v3)

        # Updates the variables like time and the "old" voltages
        t += delta_t

        if t > 4/60:
            print(time.time()-start)
            # Plots nice graph
            fig, ax = plt.subplots(1, 1, figsize=(20, 9))
            ax.scatter(results[0], results[1])
            ax.scatter(results[0], [get_Vin(t) for t in results[0]])
            #moreres = json.load(open("./res.json", "r"))
            #ax.scatter(results[0], moreres)
            #'''
            plt.show()
            #'''

            '''
            plt.savefig("fig.svg", format='svg', dpi=300)
            subprocess.call(["/usr/bin/open", "fig.svg"])
            '''

            break
