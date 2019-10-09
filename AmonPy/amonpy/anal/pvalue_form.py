"""@package pvalue_form
   Package that combines p-values from different streams using different methods.
   Under development
"""
from __future__ import division
from __future__ import print_function
from builtins import range
import sys
import numpy
import scipy
import math

def check_pvalues(pvalues):
    len_pvalues=len(pvalues)
    p_range=1
    for ii in range(len_pvalues):
        if ((pvalues[ii]<=0.) or (pvalues[ii]>1.)):
            p_range=0
            return p_range
    return p_range

def pvalue_fisher(pvalues):
    """ Combining p-values using Fisher method
    """
    if (check_pvalues(pvalues) ==1):
        pvalue_log = pvalue_fisher_log(pvalues)
        pvalue = math.exp(pvalue_log)
        return pvalue
    else:
        print('WARNING: Some of p-values entered are outside of allowed range (0,1]')
        print('Returning p=1')
        pvalue = 1.
        return pvalue

def pvalue_fisher_log(pvalues):
    """ Combining p-values using Fisher method
    """
    p_prod = 0.
    p_max = -1.e-10
    log_p = 0.
    p = 0.
    len_pvalues=len(pvalues)
    # compute ln of the p-value products
    for ii in range(len_pvalues):
        p_prod += math.log(pvalues[ii])

    for jj in range(len_pvalues):
        log_p = (p_prod + float(jj)*math.log(math.fabs(p_prod)) - math.log(math.factorial(jj)))
        if (log_p > p_max):
            p_max = log_p
        p += math.exp(log_p)

    if (p>0.):
        return math.log(p)
    else:
        return p_max

def pvalue_good(pvalues_weights):
    """
    Combines p-values using Good's formula
    References: ArXiv e-print 1011.6627, 2010. <http://http://arxiv.org/abs/1011.6627>
    """

    # weights should be decreasing, sort
    pvalues_sort = sorted(pvalues_weights, reverse=True)

    len_p=len(pvalues_weights)
    pvalues=[]
    weights=[]
    for ii in range(len_p):
        pvalues+=[pvalues_sort[ii][1]]
        weights+=[pvalues_sort[ii][0]]
    print('pvalues')
    print(pvalues)
    if (check_pvalues(pvalues) ==1):
        pvalue_log = pvalue_good_log(pvalues, weights)
        pvalue = math.exp(pvalue_log)
        return pvalue
    else:
        print('WARNING: Some of p-values entered are outside of allowed range (0,1]')
        print('Returning p=1')
        pvalue = 1.
        return pvalue

def pvalue_good_log(pvalues, weights):
    """
    Combines p-values using Good's formula
    """
    #computing product of P-value in logarithmic scale
    p_prod=0.
    pvalue_len = len(pvalues)
    weights_len = len(weights)
    p_value = 0.
    log_sum_w = 0.
    log_sum_im = 0
    if (pvalue_len != weights_len):
        print("WARNING: size of weights does match the size of p-values")
        print("Returning p=1")
        p_value = 1.
        return p_value
    else:
        for ii in range(pvalue_len):
            p_prod += weights[ii]*math.log(pvalues[ii])
        p_max = -1.e-10
        log_p = 0.
        p = 0.
        for jj in range(pvalue_len):
            #print jj
            log_sum_w, log_sum_im = good_denominator(jj,weights)
            print(log_sum_w)
            print(log_sum_im)
            if (math.fmod(log_sum_im,2.0) == 0.0):
                #print jj
                log_p = p_prod/weights[jj] + (pvalue_len-1)*math.log(weights[jj]) - log_sum_w
                p += math.exp(log_p)
                if log_p > p_max:
                    p_max = log_p
                #print p
            else:
                #print jj
                log_p =  p_prod/weights[ii] +  (pvalue_len-1)*math.log(weights[jj]) - \
	                     log_sum_w
                p -= math.exp(log_p)
                if (log_p > p_max):
	                p_max = log_p
                #print p
	if (p > 0.):
	    return math.log(p)
	else:
	    return p_max

def good_denominator(ll, pvalue_weights):
    """
    Denominator in Goods formula (product of weight differences)
    """
    diff = 0.
    # computing log of weight
    log_sum_weights=0.
    log_sum_imag=0
    pvalue_len = len(pvalue_weights)
    for ii in range(pvalue_len):
        if ii != ll:
            diff = pvalue_weights[ll] - pvalue_weights[ii]
            log_sum_weights += math.log(math.fabs(diff))
            if (diff < 0.):
                log_sum_imag +=1
	print('denominator % s and %s' % (log_sum_weights, log_sum_imag))
    return log_sum_weights, log_sum_imag


#pval=[[0.6,0.4],[0.8,0.6]]
#pval=[[1./0.6, 0.008000257],[1./0.65,0.008579261],[1./1.2,0.0008911761], \
 #    [1./1.25, 0.006967988],[1./1.3, 0.004973110]]
#print(pvalue_good(pval))
