#!/usr/bin/env python
from time import sleep
print('Contacting bank api', end='')
for i in range(10):
    print('.', end='', flush='True')
    sleep(0.5)
print('Verifying Card information', end='')
for i in range(10):
    print('.', end='', flush='True')
    sleep(0.5)
print('\nUnable to verify credit card information')
