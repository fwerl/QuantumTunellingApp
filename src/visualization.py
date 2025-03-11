import matplotlib.pyplot as plt
import numpy as np
from numpy.fft import fft
from scipy.constants import e
from src.numerics import NumericalCalculation

class Visualization:
    IMAGE_PATH = 'images/'

    def __init__(self, calc: NumericalCalculation):
        self.image_folder = Visualization.IMAGE_PATH

        # parameters used for plot y limits
        self.packet_max = np.max(np.abs(calc.packet))
        self.scale_packet = 1/self.packet_max
        self.scale_potential_barrier = 1 / calc.potential_barrier_height
        self.k_max = np.max(np.abs(abs(fft(calc.packet))))
        self.dt = calc.dt

        # plotting variables
        self.x_nm = calc.x * 1e9
        self.k_nm_inv = calc.K * 1e-9
        self.V_scaled = calc.V * self.scale_potential_barrier

        # initialize plot
        self._initialize_plot(calc)
        self._define_labels(calc)

    def _initialize_plot(self, calc) -> None:
        """Initialize the figure and axes."""
        plt.rcParams["figure.figsize"] = [16, 12]
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 6), dpi=100)
        self.ax1.set_xlim(calc.x_min * 1e9, calc.x_max * 1e9 * 1.5)
        self.ax1.set_ylim(-0.1, 1.2)
        self.ax1.set_xlabel('x [nm]')
        self.ax2.set_xlabel(r'k [nm$^{-1}$]')
        self.ax2.set_ylim(0, self.k_max * 1.2)

    def _define_labels(self, calc) -> None:
        """Define plot labels."""
        self.label_barrier = f'V$_0$ = {calc.potential_barrier_height / e:.2f} eV'
        self.label_psi_re = r'$\Re (\Psi)$'
        self.label_psi_im = r'$\Im (\Psi)$'
        self.label_Psi = r'|$\Psi$|'
        self.label_F_Psi = r'|F$(\Psi)$|'

    def _compute_error(self, packet):
        """Compute the probability integral error."""
        # integral over wave-packet function ... should be == 1.0
        # error is estimated as the deviation from integral being == 1.0
        integral = np.trapezoid(abs(packet) ** 2, self.x_nm * 1e-9)
        return abs(1 - integral) * 100

    def plot_wave_packet(self, packet: np.ndarray, time_step_index: int) -> None:
        psi = np.abs(packet)  # Probability density
        psi_r = packet.real  # Real part
        psi_i = packet.imag  # Imaginary part
        f_psi = np.abs(fft(packet))  # Fourier transform

        error = self._compute_error(packet)

        psi_r_scaled = psi_r * self.scale_packet
        psi_i_scaled = psi_i * self.scale_packet
        psi_scaled = psi * self.scale_packet

        t = (time_step_index * self.dt) * 1e15
        fig_name = f'{self.image_folder}/frame_{time_step_index:04d}.png'

        # Real Space Plot
        self.ax1.plot(self.x_nm, self.V_scaled, 'gray', label=self.label_barrier)
        self.ax1.plot(self.x_nm, psi_r_scaled, 'b', label=self.label_psi_re)
        self.ax1.plot(self.x_nm, psi_i_scaled, 'r', label=self.label_psi_im)
        self.ax1.plot(self.x_nm, psi_scaled, 'k', label=self.label_Psi)
        self.ax1.set_title(f't = {t:.2f} fs, error = {error:.2f} %')
        self.ax1.legend(loc=1)
        # Fourier Space Plot
        self.ax2.plot(self.k_nm_inv, f_psi[::-1], "k", label=self.label_F_Psi)
        self.ax2.legend(loc=9)
        # self.fig.tight_layout()
        self.fig.savefig(fname=fig_name, dpi=100, bbox_inches='tight',
                    pad_inches=0.1)
        for artist in self.ax1.lines + self.ax2.lines:
            artist.remove()

    @classmethod
    def get_image_path(cls):
        """Return the default image path without instantiation"""
        return cls.IMAGE_PATH

    def __del__(self):
        plt.close(self.fig)  # Close figure to free memory