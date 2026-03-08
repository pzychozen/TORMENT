# su3_basis.py
import numpy as np

# Orthonormal tri-octagon basis from the E8 paper
u = np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0)
x = np.array([1.0, -1.0, 0.0]) / np.sqrt(2.0)
y = np.array([1.0, 1.0, -2.0]) / np.sqrt(6.0)

# Columns = basis vectors in the standard R^3 basis
B = np.column_stack([u, x, y])  # shape (3,3)

def weights_from_Omega(Omega: np.ndarray) -> np.ndarray:
    """
    Turn a 3-component complex state Omega into a real weight triplet w,
    like flavor probabilities: w_i ∝ |Omega_i|^2, sum w_i = 1.
    """
    w = np.abs(Omega)**2
    s = np.sum(w)
    if s > 0:
        w = w / s
    return w

def project_to_uxy(Omega: np.ndarray) -> np.ndarray:
    """
    Project w into the (u, x, y) basis.

    c = (c_u, c_x, c_y)  such that  w = c_u * u + c_x * x + c_y * y.
    Since {u,x,y} is orthonormal, coordinates are  B^T @ w.
    """
    w = weights_from_Omega(Omega)       # in standard basis
    coords = B.T @ w                    # shape (3,)
    return coords  # [c_u, c_x, c_y]
