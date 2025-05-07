from huskylibTest import HuskyLensLibrary

def test_husky():
    hl = HuskyLensLibrary("I2C","", address=0x32, channel=0)
    print(hl.knock())

while True:
    test_husky()