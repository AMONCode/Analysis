#misctools.py
"""@package misctools
calculates if the iterator ii exceeds a percentage interval of N
# for the first time, where the percentage interval is d%
"""
from builtins import str
from math import trunc

# calculates if the iterator ii exceeds a percentage interval of N
# for the first time, where the percentage interval is d%
def perc_done(ii,N,d):
    if ii > 1:
        r1 = trunc(100/float(d)*(ii-1)/float(N-1))
        r2 = trunc(100/float(d)*ii/float(N-1))
        if r2 != r1:
            return str(r2*d)+'% done'
    return -1


# takes a list of objects with attributes stream, id, rev,
# and searches for the index mathcing the selected values
#def find_id(objects,stream,id,rev):
    
        




    
