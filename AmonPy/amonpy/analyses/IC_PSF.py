import numpy as np
from scipy.interpolate import interp2d, InterpolatedUnivariateSpline
from scipy import signal, stats, special


def exp_pdf(x, lam):
    return lam*np.exp(-x*lam)

def exp_cdf(x, lam):
    return 1. - np.exp(-lam*x)

def exp_quant(q, lam):
    return -1.*np.log(1.-q)/lam

def log_norm_func(r, sig, mu):
    return (1./(r*sig*(2.*np.pi)**.5))*np.exp(-((np.log(r)-mu)**2)/(2.*sig**2))

def log_norm_func2(sig, mu):
    def F(r):
        return (1./(r*sig*(2.*np.pi)**.5))*np.exp(-((np.log(r)-mu)**2)/(2.*sig**2))
    return F

def log_norm_func_cum(r, sig, mu):
    return .5 + .5*special.erf((np.log(r) - mu)/(sig*2.**.5))

def log_norm_quant(q, sig, mu, x=None):
    #if x == None:
    #    x = np.logspace(-3,2,10**4+1)#[1:]
    #x_q = x[np.argmin(np.abs(q - log_norm_func_cum(x, sig, mu)))]
    x_q = stats.lognorm.ppf(q, sig, scale=np.exp(mu))
    return x_q

def xygrid2r(pdf_grid, grid_r, r_max=5):
    r_ax = np.linspace(0,r_max,50+1)#[1:]
    dr = r_ax[1] - r_ax[0]
    prob = np.zeros_like(r_ax)
    for i in xrange(len(r_ax)):
        r = r_ax[i]
        bl = (grid_r <= r)
        prob[i] = np.sum(pdf_grid[bl])
    return prob, r_ax


def find_xs4ys(yvals, func, x_b = (0,20), tol=.01, err_ret=False):
    x_ax0 = np.linspace(x_b[0], x_b[1], 10**2+1)
    nys = len(yvals)
    xs = np.zeros(nys)
    perc_errs = np.zeros(nys)
    for i in xrange(nys):
        ind_0 = np.argmin(np.abs(yvals[i] - func(x_ax0)))
        if ind_0 < 1:
            xs[i] = x_b[0]
        elif ind_0 >= (len(x_ax0)-1):
            xs[i] = x_b[1]
        else:
            x_ax1 = np.linspace(x_ax0[(ind_0-1)], x_ax0[(ind_0+1)], 10**2+1)
            ind_1 = np.argmin(np.abs(yvals[i] - func(x_ax1)))
            x = x_ax1[ind_1]
            perc_errs[i] = np.abs(yvals[i] - func(x))/(yvals[i])
            #if perc_errs[i] > tol:
            #    print "Warn: High err for yval %.3f, perc err of %.3f percent" %(yvals[i], perc_errs[i]*100.)
            xs[i] = x
    return xs


def comb_psfs2(sig, mu, lam, get_rs=False, r_min=3.5, r_max_perc=.99, probs=None, nlog_steps=50, ignore=False):
    r_Hperc_ln = log_norm_quant(r_max_perc, sig, mu)
    r_Hperc_ex = exp_quant(r_max_perc, lam)


    r_big = r_Hperc_ln if (r_Hperc_ln > r_Hperc_ex) else r_Hperc_ex
    if r_big < r_min:
        if r_big/r_min > 2.:
            nlog_steps *= 2
        r_big = r_min

    # get r01 of both

    r01_ln = log_norm_quant(.01, sig, mu)
    r01_ex = exp_quant(.01, lam)

    r_low = r01_ex if (r01_ln > r01_ex) else r01_ln

    if ignore:
        if exp_cdf(r_big/(2.*nlog_steps), lam) > .5:
            print "Single step contains > 50% of nu prob, skipping"
            #print "r_big/40, %.3f, nu_cdf(r_big/40.), %.3f" %(r_big/40.,\
            #        exp_cdf(r_big/40.,lam))
            return None

        if r_Hperc_ex < r01_ln:
            print "Nu r%d smaller than mu r01, prob don't need to combine" %(int(100*r_max_perc))
            return None

    tot_prob_rbig = log_norm_func_cum(r_big, sig, mu)*exp_cdf(r_big, lam)

    #print "Total prob up to r big, %.2f is %.3f" %(r_big, tot_prob_rbig)

    # do log grid to double the high r end
    g0 = np.log10(r_low/2.)
    g1 = np.log10(2.*r_big)

    #nlog_steps = 100
    x1 = np.logspace(g0,g1,nlog_steps)
    x2 = -1.*np.logspace(g1,g0,nlog_steps)
    x = np.append(x2, x1)
    y1 = np.logspace(g0,g1,nlog_steps)
    y2 = -1.*np.logspace(g1,g0,nlog_steps)
    y = np.append(y2, y1)
    grid_y, grid_x = np.meshgrid(y, x)

    grid_r = (grid_x**2 + grid_y**2)**.5


    pdf_ln_grid_r = log_norm_func(grid_r, sig, mu)
    pdf_ex_grid_r = exp_pdf(grid_r, lam)
    pdf_mu_dens_grid = pdf_ln_grid_r/(2.*np.pi*grid_r)
    pdf_nu_dens_grid = pdf_ex_grid_r/(2.*np.pi*grid_r)

    #intp_steps = 201j
    intp_steps = (2j*nlog_steps+1j)
    grid_intp_x, grid_intp_y = np.mgrid[-r_big:r_big:intp_steps, -r_big:r_big:intp_steps]
    dx = grid_intp_x[1][0] - grid_intp_x[0][0]
    #print "intp dx, %.3f" %(dx)
    orig_x = x
    orig_y = y
    intp_x = grid_intp_x[:,0]
    intp_y = grid_intp_y[0][:]
    grid_intp_r = (grid_intp_x**2 + grid_intp_y**2)**.5

    pdf_mu_dens_intp = interp2d(orig_x, orig_y, pdf_mu_dens_grid)

    pdf_mu_dens_intp_grid = pdf_mu_dens_intp(intp_x, intp_y)

    pdf_nu_dens_intp = interp2d(orig_x, orig_y, pdf_nu_dens_grid)

    pdf_nu_dens_intp_grid = pdf_nu_dens_intp(intp_x, intp_y)

    pdf_mu_dens_intp_grid[(grid_intp_r==0)] = 0.
    pdf_nu_dens_intp_grid[(grid_intp_r==0)] = 0.

    #mu_sum = np.sum(pdf_mu_dens_intp_grid)*dx*dx
    #nu_sum = np.sum(pdf_nu_dens_intp_grid)*dx*dx
    mu_sum_r = np.sum(pdf_mu_dens_intp_grid[(grid_intp_r<=r_big)])*dx*dx
    nu_sum_r = np.sum(pdf_nu_dens_intp_grid[(grid_intp_r<=r_big)])*dx*dx

    cent_prob_mu2 = log_norm_func_cum(r_big, sig, mu) - mu_sum_r
    intp_r0_ind = np.where(grid_intp_r==0)
    mid_ind = nlog_steps
    if cent_prob_mu2 < 0:
        #pdf_mu_dens_intp_grid[intp_r0_ind] =\
        #4.*pdf_mu_dens_intp_grid[intp_r0_ind[0][0],(intp_r0_ind[1][0]+1)]/5.
         pdf_mu_dens_intp_grid[intp_r0_ind] =\
        4.*pdf_mu_dens_intp_grid[mid_ind,mid_ind+1]/5.
    else:
        pdf_mu_dens_intp_grid[(grid_intp_r==0)] = cent_prob_mu2/(dx**2.)
    cent_prob_nu2 = exp_cdf(r_big, lam) - nu_sum_r
    pdf_nu_dens_intp_grid[(grid_intp_r==0)] = cent_prob_nu2/(dx**2.)

    #print pdf_mu_dens_intp_grid[(grid_intp_r==0)]
    #print pdf_nu_dens_intp_grid[(grid_intp_r==0)]

    mu_sum = np.sum(pdf_mu_dens_intp_grid)*dx*dx
    nu_sum = np.sum(pdf_nu_dens_intp_grid)*dx*dx
    #print "mu sum ", mu_sum
    #print "nu sum ", nu_sum
    mu_sum_r = np.sum(pdf_mu_dens_intp_grid[(grid_intp_r<=r_big)])*dx*dx
    nu_sum_r = np.sum(pdf_nu_dens_intp_grid[(grid_intp_r<=r_big)])*dx*dx
    norm_fac = tot_prob_rbig/(mu_sum_r*nu_sum_r)

    convld = signal.convolve2d(pdf_mu_dens_intp_grid, pdf_nu_dens_intp_grid, boundary='symm',\
                                mode='same')

    conv_pdf = convld*dx*dx*norm_fac

    #intp_steps2 = 1001j
    intp_steps2 = (10j*(nlog_steps)+1j)
    grid_intp_x2, grid_intp_y2 = np.mgrid[-r_big:r_big:intp_steps2, -r_big:r_big:intp_steps2]
    dx2 = grid_intp_x2[1][0] - grid_intp_x2[0][0]

    intp_x2 = grid_intp_x2[:,0]
    intp_y2 = grid_intp_y2[0][:]
    grid_intp_r2 = (grid_intp_x2**2 + grid_intp_y2**2)**.5

    conv_pdf_func = interp2d(intp_x, intp_y, conv_pdf)

    conv_pdf2 = conv_pdf_func(intp_x2, intp_y2)


    if get_rs:

        if probs is None:
            probs = np.linspace(0., .94, .94/.02 + 1)

        r_cum2, r_ax = xygrid2r(conv_pdf2, grid_intp_r2, r_max=r_big)
        r_cum2 *= dx2**2

        intp_cum = InterpolatedUnivariateSpline(r_ax, r_cum2)

        rs_from_intp = find_xs4ys(probs, intp_cum, x_b=(0,r_big))
        return conv_pdf_func, rs_from_intp, probs
    return conv_pdf_func
