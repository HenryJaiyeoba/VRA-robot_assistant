from huskylib import HuskyLensLibrary
import time

hl = HuskyLensLibrary("I2C", "", address=0x32)
# print(hl.knock())

def warn_user():
    print("Hey, please move I have somewhere to be!")


try:
    while True:
        hl.requestAll()
        objects = hl.blocks()
        if objects:
            print(f"Detected {len(objects)} objects in front")
            warn_user()
        else:
            print("the path is clear...")
except KeyboardInterrupt:
    print("Interrupted by the Jaiye")