import numpy as np

class FPRD(object):

    '''
    to use this:

    fname = 'Where FPRD npz file is'
    fprd_obj = FPRD(fname=fname)

    # get the p-value with already known fprd_value

    pval = fprd_obj.get_pval(cos_zen, fprd=fprd_value)

    # get B(r_IC)

    B_IC = fprd_obj.get_B_spat(cos_zen)
    '''

    def __init__(self, fname='FPRD_stuff.npz'):

        npz_file = np.load(fname)

        try:
            up_intp = npz_file['up_log10fprd_intp'].item()
            a = up_intp(-.5, 2.5)

        except Exception as E:
            print E
            print "Probably wrong scipy version"
            print "Trying to make remake interpolator with grid points"

            from scipy import interpolate

            up_intp = interpolate.LinearNDInterpolator(npz_file['up_grid_points'],\
                                            npz_file['up_log10fprds'])


        self.up_fprd_intp = up_intp


        try:
            down_intp = npz_file['down_log10fprd_intp'].item()
            a = down_intp(.5, .05)

        except Exception as E:
            print E
            print "Probably wrong scipy version"
            print "Trying to make remake interpolator with grid points"

            from scipy import interpolate

            down_intp = interpolate.LinearNDInterpolator(npz_file['down_grid_points'],\
                                            npz_file['down_log10fprds'])


        self.down_fprd_intp = down_intp

        self.B_spat_interp = npz_file['B_spat_interp'].item()

        self.tot_rate_per_hour = 24.12422759272274

        npz_file.close()

    def get_fprd(self, cos_zen, y, adj_bdt=True):

        if np.rad2deg(np.arccos(cos_zen)) > 82.:

            if y < 0:
                y = 1.

            if y > 5.0:
                val = 1e-6
            else:
                val = 10.**(self.up_fprd_intp(cos_zen, y))
                if val < 1e-6:
                    val = 1e-6

        else:
            if y <= -1:
                bdt_adj = 0
            elif adj_bdt:
                bdt_adj = self.adj_bdt(cos_zen, y)
            else:
                bdt_adj = y
            if bdt_adj > 0.4:
                val = 5e-6
            else:
                val = 10.**(self.down_fprd_intp(cos_zen, bdt_adj))
                if val < 5e-6:
                    val = 5e-6
        return val

    def get_pval(self, cos_zen, y=None, adj_bdt=True, fprd=None):

        if fprd is None:
            fprd = self.get_fprd(cos_zen, y, adj_bdt=adj_bdt)

        fact = self.get_fprd(cos_zen, -1)

        pval = fprd/fact

        return pval


    def get_B_spat(self, cos_zen):

        B_spat = self.B_spat_interp(cos_zen)

        return B_spat


    def adj_bdt(self, cos_zen, bdt):
        if cos_zen > .39:
            cut = -0.7
        elif cos_zen > .22:
            cut = np.interp(cos_zen, [0.22, 0.39], [-0.6723, -0.7])
        else:
            cut = np.polyval([ -7101.97681, 13756.69027, -10824.05662,\
                4418.69708, -984.41389, 112.85935, -5.83447 ], cos_zen)
        return bdt - cut
