from huskylib import HuskyLensLibrary

h1 = HuskyLensLibrary("I2C", "", address=0x32)
print(h1.knock())