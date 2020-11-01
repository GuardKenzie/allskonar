# Author: Tristan Ferrua
# 2020-09-16 19:17
# Filename: zcycle.py 

import math

def main(n):
    a = int(input("a="))

    group = []

    element = a

    while element not in group:
        group.append(element)
        element = (element + a) % n

    print(sorted(group))

n = int(input("n="))
while True:
    main(n)
