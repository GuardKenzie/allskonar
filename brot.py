# Author: Tristan Ferrua
# 2020-10-22 12:46
# Filename: brot.py 

import math

def de(a):
    return a[0] / a[1]

def addfracs(a, b):
    return [a[0] + b[0], a[1] + b[1]]


def asfraction(n):
    tens = len(str(int(n)))

    n = n / 10**tens

    frac = [1, 2]

    top = [1, 1]
    bottom = [0, 1]

    while de(frac) != n:
        if n < de(frac):
            top = frac
            frac = addfracs(frac, bottom)
        else:
            bottom = frac
            frac = addfracs(frac, top)

    return [frac[0] * 10**tens, frac[1]]

n = float(input("n="))
print(asfraction(n))
