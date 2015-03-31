__author__ = 'aleaf'

import matplotlib.pyplot as plt
from pyemu import errvar
from mat_handler import jco as Jco
from pst_handler import pst as Pst
import plots

class IdentPar:
    def __init__(self, jco):
        """Computes parameter identifiability for a PEST jco file,
        using the errvar class in pyemu (https://github.com/jtwhite79/pyemu)
        """

        self.la = errvar(jco)

    def plot_singular_spectrum(self):
        """see http://nbviewer.ipython.org/github/jtwhite79/pyemu/blob/master/examples/error_variance_example.ipynb
        """
        s = self.la.qhalfx.s

        figure = plt.figure(figsize=(10, 5))
        ax = plt.subplot(111)
        ax.plot(s.x)
        ax.set_title("singular spectrum")
        ax.set_ylabel("power")
        ax.set_xlabel("singular value")
        ax.set_xlim(0,300)
        ax.set_ylim(0,10)
        plt.show()

    def get_identifiability_dataframe(self, nsingular):

        self.ident_df = self.la.get_identifiability_dataframe(nsingular)

    def plot_bar(self, nsingular=None, nbars=20):
        """Computes a stacked bar chart showing the most identifiable parameters
        at a given number of singular values

        Parameters:
        -----------
        nsingular:
            number of singular values to include

        nbars:
            number of parameters (bars) to include in bar chart
        """
        if nsingular is not None:
            self.ident_df = self.la.get_identifiability_dataframe(nsingular)

        plot_obj = plots.IdentBar(self.ident_df, nsingular=nsingular, nbars=nbars)
        plot_obj.generate()
        plot_obj.draw()