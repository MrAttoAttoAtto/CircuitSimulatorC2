# Nodal analysis on a circuit such that a 10V cell is connected to a "resistor" with V=sqrt(I)*R, which is itself connected to a standard resistor (connected to ground),
# both of resistance r

import numpy as np
# Initial guess (literally doesn't matter, except that the second MUST be smaller than the first, or more solutions start appearing...)
input_vec = [13, -12, 234]
# Resistance in ohms (both resistors)
r = 1

while True:
    # Load the variables from the input vector
    v1 = input_vec[0]
    v2 = input_vec[1]
    iv = input_vec[2]

    # Calculate the values in result vector
    result_vector = [0, 0, 0]

    result_vector[0] = ((v1-v2)/r)**2-iv
    result_vector[1] = -((v1-v2)/r)**2+v2/r
    result_vector[2] = v1-10

    # Create the Jacobian for this input vector
    g = 2*(v1-v2)/(r**2)
    jac = np.array([[g,-g,-1],[-g,g+1/r,0],[1,0,0]])

    # Calculate the new (better) input vector by doing new x = old x - J(x)^-1*F(x), where J(x)^-1 is the inverse Jacobian of x, and F(x) is the result vector given by x
    inv_jac = np.linalg.inv(jac)
    res = np.dot(inv_jac, result_vector)
    input_vec = input_vec - res
    print(input_vec)
    print(result_vector)
    input()

