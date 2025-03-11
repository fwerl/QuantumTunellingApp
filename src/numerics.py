import numpy as np
from numpy.typing import NDArray
from scipy.constants import hbar, m_e, e
from scipy.sparse.linalg import splu
from scipy.sparse import csc_matrix, csr_matrix

class NumericalCalculation:
    def __init__(self, size_packet, size_barrier, duration_time,
                 energy_packet, potential_barrier_height, dx, dt):
        """
                Class managing numerical calculations for quantum tunnelling.
                :param size_packet: spatial size of wave packet [nanometer]
                :param size_barrier: spatial size of barrier [nanometer]
                :param duration_time: time duration of the simulation [fs]
                :param energy_packet: mean energy of the packet [eV]
                :param potential_barrier_height: potential barrier height [eV]
                :param dx: simulation space division step [pm]
                :param dt: simulation time-step [as]
                """
        ## input variables ##
        # saving simulation parameters in SI units
        self.size_packet = size_packet * 1e-9
        self.size_barrier = size_barrier * 1e-9
        self.time_duration = duration_time * 1e-15
        self.energy_packet = energy_packet * e
        self.potential_barrier_height = potential_barrier_height * e
        self.dx = dx*1e-12
        self.dt = dt*1e-18

        ## calculated variables ##
        # spatial #
        # calculate wave packet and barrier positions
        sigma = 6*self.size_packet
        self.x_packet = 2*sigma
        self.x_barrier = self.x_packet + sigma
        # define x-axis borders
        self.x_min = 0.0
        self.x_max = self.x_barrier + 4 * sigma
        # calculate x-axis values
        self.division_x = int((self.x_max - self.x_min) / self.dx)  # x-axis division number
        self.x = np.linspace(self.x_min, self.x_max, self.division_x)  # all x-axis positions to be calculated

        # temporal #
        # calculate time values
        self.division_time = int(self.time_duration/self.dt)
        self.t = np.linspace(0.0, self.time_duration, self.division_time)  # all time points to be calculated

        # energy #
        # potential barrier values for all points in x-axis
        self.V = np.where(
            (self.x_barrier <= self.x) & (self.x <= self.x_barrier + self.size_barrier),
            self.potential_barrier_height,
            0
        )

        # wave numbers #
        self.k = np.sqrt(2 * m_e * self.energy_packet) / hbar  # wave number of the initial packet [1/meter]
        self.dk = 2 * np.pi / (self.x_max - self.x_min)  # wave number step size [1/meter]
        self.K = self.dk * np.linspace(-1, 1, self.division_x)  # wave number points in reciprocal space

        ## numerical parameters used for Schrödinger equation calculation ##
        self._get_numerical_parameters()  # fills in empty arrays A, B, b

        self.packet = np.asarray([self._gauss(x) for x in self.x], dtype=complex)  # initial state of the wave packet
        self.rhs_eq = self.B @ self.packet[1:-1] + self.b  #  dot product of B and packet optimized for sparse matrices

    def _gauss(self, x: NDArray[np.float64]) -> NDArray[np.complex128]:
        """
        used for initial state of the wave packet
        :param x: spatial values, numpy array over whole space
        :return: gaussian wave function
        """
        return np.exp(-(x - self.x_packet) ** 2 / (4 * self.size_packet ** 2) + 1j * self.k * x) / (
                    2 * np.pi * self.size_packet ** 2) ** 0.25

    def _get_numerical_parameters(self) -> None:
        """
        Fills in A, B, b variables with values, used for later calculation.

        Time dependent Schrödinger equation in step k+1 can be numerically calculated from step k
        A*psi^(k+1) = B*psi^(k) + b
        left-hand side = step k+1
        right-hand side = step k
        A, B are matrices, b is a vector
        """

        # Define matrix dimension
        n = self.division_x - 2

        # A, B, b initialization
        self.A = np.zeros((n, n), dtype=complex)
        self.B = np.zeros((n, n), dtype=complex)
        self.b = np.zeros(n, dtype=complex)

        r = 1j * self.dt / self.dx ** 2 * hbar / (4 * m_e)  # used for calculation of A and B matrices
        q = -1j * self.dt / hbar * self.V[1:-1] + 1 - 2 * r  # used for calculation of matrix B

        # Set diagonal and off-diagonal elements
        self.A[np.arange(n), np.arange(n)] = 1 + 2 * r  # Main diagonal
        self.A[np.arange(n - 1), np.arange(1, n)] = -r  # Upper diagonal
        self.A[np.arange(1, n), np.arange(n - 1)] = -r  # Lower diagonal

        self.B[np.arange(n), np.arange(n)] = q  # Main diagonal
        self.B[np.arange(n - 1), np.arange(1, n)] = r  # Upper diagonal
        self.B[np.arange(1, n), np.arange(n - 1)] = r  # Lower diagonal

        # Apply boundary conditions
        self.b[0] = 0
        self.b[-1] = 0

        # Convert matrices to sparse format
        self.A = csc_matrix(self.A)
        self.B = csr_matrix(self.B)

        # Compute LU factorization once for faster computation with constant matrix
        self.lu = splu(self.A)

    def calculate_timestep(self) -> None:
        """
        Calculates one time-step of the time dependent Schrödinger equation.
        :return: None
        """
        # calculation of the packet in next time step - optimized for sparse constant matrix
        self.packet[1:-1] = self.lu.solve(self.rhs_eq)
        # calculation of the right-hand side of the numerical equation
        self.rhs_eq = self.B @ self.packet[1:-1] + self.b  #  dot product of B and packet optimized for sparse matrices

    def get_packet(self) -> NDArray:
        """
        Returns independent deepcopy copy of the wave packet data.
        :return: Numpy array of the wave packet data.
        """
        return self.packet.copy()

