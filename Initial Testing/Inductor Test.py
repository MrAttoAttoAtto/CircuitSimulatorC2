
import math
import time

import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg

# Initial guess
input_vec = [3, 0, 1e-3]

# Resistance in Ohms
R = 1

# Inductance in Henrys
L = 100

# Initial current
I_0 = 0

# Frequency of the AC source in Hertz
f = 60

# AC peak
Vin_AC_peak = 0

# DC component
Vin_DC = 10

sin_multiplier = f*2*math.pi

# Combo of AC and DC power source
def get_Vin(t):
    return Vin_AC_peak*math.sin(sin_multiplier*t) + Vin_DC


# Starting time, and size of time steps
t = 1e-5
delta_t = 1e-5

old_v2 = 0

# Holds results for plotting
results = [[],[],[]]

start = time.time()
while True:

    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    iv = input_vec[2]

    # Calculate the values in result vector
    result_vector = [0, 0, 0]

    result_vector[0] = -((v1-v2)/R - iv) # Current at 1
    result_vector[1] = -(I_0 + 1/L*delta_t*(old_v2+v2)/2 - (v1-v2)/R) # Current at 2
    result_vector[2] = -(v1-get_Vin(t)) # Voltage at 1

    # Create the Jacobian for this input vector
    g = 1/L*delta_t/2
    jac = np.array([[1/R, -1/R, -1],
                    [-1/R, g + 1/R, 0],
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
        # Updates the variables like time and the "old" voltages
        t += delta_t
        old_v2 = v2
        I_0 = I_0 + delta_t/2*(old_v2+v2)
        
        results[0].append(t)
        results[1].append(I_0)
        results[2].append(v2)

        if t > 300/60:
            print(time.time()-start)
            # Plots nice graph
            fig, ax = plt.subplots(1, 2, figsize=(16, 8))
            print(results[1][int(1/1e-5)])
            ax[0].scatter(results[0], results[1])
            ax[1].scatter(results[0], results[2])
            # '''
            plt.show()
            # '''

            '''
            plt.savefig("fig.svg", format='svg', dpi=300)
            subprocess.call(["/usr/bin/open", "fig.svg"])
            '''

            break
