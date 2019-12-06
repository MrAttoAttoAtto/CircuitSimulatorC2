import scipy.linalg
import numpy as np


def make_lapack_inverse(size):
    # The identity matrix
    iden = np.eye(size)

    # Optimises some of the matrix inverting by only doing some things once and by bypassing sanity checks
    def lapack_inverse(A):
        results = scipy.linalg.lapack.dgesv(A, iden)
        if results[3] > 0:
            raise np.linalg.LinAlgError('Singular matrix')
        return results[2]

    return lapack_inverse
