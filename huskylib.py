# HuskyLens Python Library
# Author: Robert Prast (robert@dfrobot.com)
# 08/03/2020
# Dependenices :
#   pyserial
#   smbus
#   pypng
#
# How to use :
# 1) First import the library into your project and connect your HuskyLens
# 2) Init huskylens
#   A) Serial
#          huskyLens = HuskyLensLibrary("SERIAL","COM_PORT", speed) *speed is integer
#   B) I2C
#           huskyLens = HuskyLensLibrary("I2C","", address=0xADDR) *address is hex integer
# 3) Call your desired functions on the huskyLens object!
###
# Example code
'''
huskyLens = HuskyLensLibrary("I2C","",address=0x32)
huskyLens.algorthim("ALGORITHM_FACE_RECOGNITION")
while(true):
    data=huskyLens.blocks()
    x=0
    for i in data:
        x=x+1
        print("Face {} data: {}".format(x,i)
'''


import time
import serial
import png
import json


commandHeaderAndAddress = "55AA11"
algorthimsByteID = {
    "ALGORITHM_OBJECT_TRACKING": "0100",
    "ALGORITHM_FACE_RECOGNITION": "0000",
    "ALGORITHM_OBJECT_RECOGNITION": "0200",
    "ALGORITHM_LINE_TRACKING": "0300",
    "ALGORITHM_COLOR_RECOGNITION": "0400",
    "ALGORITHM_TAG_RECOGNITION": "0500",
    "ALGORITHM_OBJECT_CLASSIFICATION": "0600",
    "ALGORITHM_QR_CODE_RECOGNTITION" : "0700",
    "ALGORITHM_BARCODE_RECOGNTITION":"0800",
}

class Arrow:
    def __init__(self, xTail, yTail , xHead , yHead, ID):
        self.xTail=xTail
        self.yTail=yTail
        self.xHead=xHead
        self.yHead=yHead
        self.ID=ID
        self.learned= True if ID > 0 else False
        self.type="ARROW"


class Block:
    def __init__(self, x, y , width , height, ID):
        self.x = x
        self.y=y
        self.width=width
        self.height=height
        self.ID=ID
        self.learned= True if ID > 0 else False
        self.type="BLOCK"



class HuskyLensLibrary:
    def __init__(self, proto, comPort="", speed=3000000, channel=1, address=0x32):
        self.proto = proto
        self.address = address
        self.checkOnceAgain=True
        if(proto == "SERIAL"):
            self.huskylensSer =serial.Serial(
                baudrate=speed,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
                timeout=.5
            )
            self.huskylensSer.dtr = False
            self.huskylensSer.rts = False
            time.sleep(.1)
            self.huskylensSer.port=comPort
            self.huskylensSer.open()
            time.sleep(2)
            self.knock()
            time.sleep(.5)
            self.knock()
            time.sleep(.5)
            self.knock()
            # self.huskylensSer.timeout=5
            self.huskylensSer.flushInput()
            self.huskylensSer.flushOutput()
            self.huskylensSer.flush()

        elif (proto == "I2C"):
            import smbus2 as smbus # Import smbus2 and alias it as smbus
            self.huskylensSer = smbus.SMBus(channel)
        self.lastCmdSent = ""

    def writeToHuskyLens(self, cmd):
        self.lastCmdSent = cmd
        if(self.proto == "SERIAL"):
            self.huskylensSer.flush()
            self.huskylensSer.flushInput()
            self.huskylensSer.write(cmd)
        else:
            self.huskylensSer.write_i2c_block_data(self.address, 12, list(cmd))

    def calculateChecksum(self, hexStr):
        total = 0
        for i in range(0, len(hexStr), 2):
            total += int(hexStr[i:i+2], 16)
        hexStr = hex(total)[-2:]
        return hexStr

    def cmdToBytes(self, cmd):
        return bytes.fromhex(cmd)

    def splitCommandToParts(self, str_in): # Renamed str to str_in to avoid shadowing built-in
        # print(f"We got this str=> {str_in}")
        # Add basic length check
        if len(str_in) < 10: # Minimum length: header(4)+addr(2)+len(2)+cmd(2) = 10
             raise ValueError(f"Received command string too short: {len(str_in)} chars ('{str_in}')")

        headers = str_in[0:4]
        address = str_in[4:6]
        try:
            # Ensure the slice is valid before converting
            data_length_hex = str_in[6:8]
            if not data_length_hex:
                 raise ValueError("Data length field is empty")
            data_length = int(data_length_hex, 16) # Catch potential ValueError here too
        except ValueError as e:
            raise ValueError(f"Invalid data length field: '{str_in[6:8]}'") from e

        command = str_in[8:10]

        expected_len = 12 + data_length * 2 # header(4)+addr(2)+len(2)+cmd(2)+data(N*2)+chk(2)
        if len(str_in) < expected_len:
            raise ValueError(f"Command string length mismatch. Expected at least {expected_len}, got {len(str_in)} ('{str_in}')")

        if(data_length > 0):
            data = str_in[10:10+data_length*2]
        else:
            data = '' # Changed from [] to ''
        # checkSum = str_in[2*(6+data_length-1):2*(6+data_length-1)+2] # Original calculation
        checkSum = str_in[10 + data_length*2 : 12 + data_length*2] # Simplified index calculation

        # Ensure checksum slice is valid
        if len(checkSum) < 2:
             raise ValueError(f"Could not extract checksum. String: '{str_in}', Calculated slice: [{10 + data_length*2}:{12 + data_length*2}]")


        return [headers, address, data_length, command, data, checkSum]

    def getBlockOrArrowCommand(self):
        # This function reads subsequent block/arrow data packets after the initial response header
        # It assumes the initial response indicated how many blocks/arrows to expect.
        # The reading logic here needs similar robustness checks as processReturnData
        try:
            if(self.proto == "SERIAL"):
                # Read header (5 bytes)
                byteString = self.huskylensSer.read(5)
                if len(byteString) < 5:
                    raise TimeoutError(f"Incomplete block/arrow header read (expected 5, got {len(byteString)})")

                # Determine data length
                data_len = int(byteString[3])

                # Read data bytes
                if data_len > 0:
                    data_bytes = self.huskylensSer.read(data_len)
                    if len(data_bytes) < data_len:
                        raise TimeoutError(f"Incomplete block/arrow data read (expected {data_len}, got {len(data_bytes)})")
                    byteString += data_bytes

                # Read checksum byte
                checksum_byte = self.huskylensSer.read(1)
                if len(checksum_byte) < 1:
                    raise TimeoutError("Incomplete block/arrow checksum read")
                byteString += checksum_byte

            else: # I2C
                 # Read header (5 bytes)
                byteString = b''
                for i in range(5):
                    try:
                        byteString += bytes([(self.huskylensSer.read_byte(self.address))])
                    except Exception as i2c_err:
                         raise TimeoutError(f"I2C read error during block/arrow header byte {i+1}: {i2c_err}") from i2c_err
                if len(byteString) < 5:
                     raise TimeoutError("Incomplete block/arrow header read (I2C)")

                # Determine data length
                data_len = int(byteString[3])

                # Read data bytes + checksum byte (data_len + 1 bytes total)
                bytes_to_read = data_len + 1
                for i in range(bytes_to_read):
                     try:
                        byteString += bytes([(self.huskylensSer.read_byte(self.address))])
                     except Exception as i2c_err:
                         raise TimeoutError(f"I2C read error during block/arrow data/checksum byte {i+1}: {i2c_err}") from i2c_err
                # Check total length
                expected_total_len = 5 + data_len + 1
                if len(byteString) < expected_total_len:
                    raise TimeoutError(f"Incomplete block/arrow read (I2C, expected {expected_total_len}, got {len(byteString)})")

            # Now parse the received block/arrow data packet
            commandSplit = self.splitCommandToParts(byteString.hex())
            isBlock = True if commandSplit[3] == "2a" else False # Command 0x2A for block, 0x2B for arrow
            return (commandSplit[4], isBlock)

        except (TimeoutError, serial.SerialTimeoutException, ValueError) as e:
             print(f"Error reading block/arrow data: {e}")
             # Re-raise or return an error indicator? Re-raising might be better.
             raise e # Propagate the error up

    def processReturnData(self, numIdLearnFlag=False, frameFlag=False):
        # Removed inProduction flag, assuming it's always true
        byteString=b"" # Initialize as bytes
        try:
            if(self.proto == "SERIAL"):
                # Read header + address + length byte (5 bytes)
                byteString = self.huskylensSer.read(5)
                if len(byteString) < 5:
                    raise TimeoutError(f"Incomplete header read (expected 5, got {len(byteString)})")

                # Determine data length
                data_len = int(byteString[3]) # This byte indicates the length of the data *payload*

                # Read data bytes
                if data_len > 0:
                    data_bytes = self.huskylensSer.read(data_len)
                    if len(data_bytes) < data_len:
                        raise TimeoutError(f"Incomplete data read (expected {data_len}, got {len(data_bytes)})")
                    byteString += data_bytes

                # Read checksum byte
                checksum_byte = self.huskylensSer.read(1)
                if len(checksum_byte) < 1:
                    raise TimeoutError("Incomplete checksum read")
                byteString += checksum_byte

            else: # I2C
                # Read header + address + length byte (5 bytes total)
                byteString = b''
                for i in range(5):
                    try:
                        byteString += bytes([(self.huskylensSer.read_byte(self.address))])
                    except Exception as i2c_err: # Catch potential I2C read errors
                         raise TimeoutError(f"I2C read error during header byte {i+1}: {i2c_err}") from i2c_err
                if len(byteString) < 5:
                     raise TimeoutError("Incomplete header read (I2C)")

                # Determine data length
                data_len = int(byteString[3])

                # Read data bytes + checksum byte (data_len + 1 bytes total)
                bytes_to_read = data_len + 1
                for i in range(bytes_to_read):
                     try:
                        byteString += bytes([(self.huskylensSer.read_byte(self.address))])
                     except Exception as i2c_err:
                         raise TimeoutError(f"I2C read error during data/checksum byte {i+1}: {i2c_err}") from i2c_err
                # Check if the total expected length was read (5 + data_len + 1)
                expected_total_len = 5 + data_len + 1
                if len(byteString) < expected_total_len:
                    raise TimeoutError(f"Incomplete read (I2C, expected {expected_total_len}, got {len(byteString)})")

            # Now process the complete byteString
            commandSplit = self.splitCommandToParts(byteString.hex())
            # print(commandSplit) # Keep commented out unless debugging

            # Check for standard ACK response (Command 0x2E)
            if(commandSplit[3] == "2e"):
                self.checkOnceAgain=True # Reset retry flag on success
                return "Knock Recieved" # Use a more descriptive success message? Like "OK" or "Command Accepted"?

            # Handle responses containing data (like blocks/arrows)
            # Expected command for block/arrow info response is 0x29 (RETURN_INFO)
            elif commandSplit[3] == "29":
                returnData = []
                # Payload structure for RETURN_INFO: blocks(2), learned(2), frame(2)
                # Ensure data field has enough bytes (6 bytes = 12 hex chars)
                if len(commandSplit[4]) < 12:
                     raise ValueError(f"RETURN_INFO response data too short: {len(commandSplit[4])} chars ('{commandSplit[4]}')")

                numberOfBlocksOrArrow = int(
                    commandSplit[4][2:4]+commandSplit[4][0:2], 16) # Bytes 0-1: Number of blocks/arrows
                numberOfIDLearned = int(
                    commandSplit[4][6:8]+commandSplit[4][4:6], 16) # Bytes 2-3: Number of IDs learned
                frameNumber = int(
                    commandSplit[4][10:12]+commandSplit[4][8:10], 16) # Bytes 4-5: Frame number

                isBlock=None # Determine type based on the *next* packets read
                for i in range(numberOfBlocksOrArrow):
                    # Read each block/arrow packet individually
                    tmpObj=self.getBlockOrArrowCommand() # This now handles its own reading & parsing
                    isBlock=tmpObj[1] # Store the type from the last packet (assumes all are same type)
                    returnData.append(tmpObj[0]) # Append the data payload

                if isBlock is None and numberOfBlocksOrArrow > 0:
                     # This shouldn't happen if getBlockOrArrowCommand works correctly
                     print("Warning: Could not determine if data is Block or Arrow")
                     # Default to Block? Or handle as error? Let's default for now.
                     isBlock = True

                finalData = []
                tmp = []
                # print(returnData) # Keep commented out unless debugging
                for i in returnData:
                    tmp = []
                    # Data format: x(2), y(2), width(2), height(2), ID(2) for blocks
                    # Or: xTail(2), yTail(2), xHead(2), yHead(2), ID(2) for arrows
                    # Each value is 16-bit, split into low/high bytes in the hex string
                    for q in range(0, len(i), 4): # Process 4 hex chars (2 bytes) at a time
                        low=int(i[q:q+2], 16)
                        high=int(i[q+2:q+4], 16)
                        # Combine high and low bytes for 16-bit value
                        # Original code had a potential bug: val=low+255+high if high>0
                        # Correct way: val = (high << 8) | low
                        val = (high << 8) | low
                        tmp.append(val)
                    if len(tmp) == 5: # Ensure we got 5 values
                        finalData.append(tmp)
                    else:
                        print(f"Warning: Incorrect number of values parsed for object data: {len(tmp)}, raw hex: '{i}'")
                    tmp = [] # Reset tmp for next object

                self.checkOnceAgain=True # Reset retry flag on success
                ret=self.convert_to_class_object(finalData,isBlock if isBlock is not None else True) # Pass type, default to Block if unknown
                if(numIdLearnFlag):
                    ret.append(numberOfIDLearned)
                if(frameFlag):
                    ret.append(frameNumber)
                return ret
            else:
                # Handle other command responses if necessary
                print(f"Warning: Received unknown command response: {commandSplit[3]}")
                self.checkOnceAgain=True # Reset retry flag even on unknown response? Maybe.
                # Return something to indicate unexpected response?
                return f"Unknown response command: {commandSplit[3]}"


        except (TimeoutError, serial.SerialTimeoutException, ValueError, IndexError) as e: # Catch specific communication/parsing errors
            print(f"Error communicating with/parsing data from HuskyLens: {e}")
            if(self.checkOnceAgain):
                 self.checkOnceAgain=False # Prevent infinite loops
                 # Maybe add a small delay before retrying?
                 time.sleep(0.1)
                 print("Retrying command...")
                 # How to retry? Need to resend the last command.
                 # Let's return an error indicator for now, retry should happen at higher level if needed.
                 # return self.processReturnData() # Recursive retry might hide the original command context
                 return "Retry Failed" # Indicate failure after retry attempt was conceptually needed
            else:
                print("Read/Parse response error, please try again")
                if self.proto == "SERIAL":
                    try:
                        self.huskylensSer.flushInput()
                        self.huskylensSer.flushOutput()
                        self.huskylensSer.flush()
                    except Exception as flush_err:
                        print(f"Error flushing serial port: {flush_err}")
                return [] # Return empty list on failure

        except Exception as e: # Catch other unexpected errors
            print(f"Unexpected error processing HuskyLens data: {e}")
            import traceback
            traceback.print_exc() # Print stack trace for unexpected errors
            # Should we retry on unexpected errors? Maybe not.
            self.checkOnceAgain=False # Avoid potential loops if error persists
            print("Unexpected error, please try again")
            if self.proto == "SERIAL":
                 try:
                    self.huskylensSer.flushInput()
                    self.huskylensSer.flushOutput()
                    self.huskylensSer.flush()
                 except Exception as flush_err:
                    print(f"Error flushing serial port: {flush_err}")
            return [] # Return empty list on failure

    def convert_to_class_object(self,data,isBlock):
        tmp=[]
        for i in data:
            if len(i) != 5: # Add check for correct number of elements
                print(f"Warning: Skipping object data with incorrect length: {i}")
                continue
            if(isBlock):
                # Ensure indices are valid before accessing
                obj = Block(i[0],i[1],i[2],i[3],i[4])
            else:
                obj = Arrow(i[0],i[1],i[2],i[3],i[4])
            tmp.append(obj)
        return tmp

    def knock(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002c3c")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()
    
    def learn(self,x):
        data = "{:04x}".format(x)
        part1=data[2:]
        part2=data[0:2]
        #reverse to correct endiness
        data=part1+part2
        dataLen = "{:02x}".format(len(data)//2)
        cmd = commandHeaderAndAddress+dataLen+"36"+data
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def forget(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"003747")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def setCustomName(self,name,idV):
        nameDataSize = "{:02x}".format(len(name)+1)
        name = name.encode("utf-8").hex()+"00"
        localId = "{:02x}".format(idV)
        data = localId+nameDataSize+name
        dataLen = "{:02x}".format(len(data)//2)
        cmd = commandHeaderAndAddress+dataLen+"2f"+data
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def customText(self,nameV,xV,yV):
        name=nameV.encode("utf-8").hex()
        nameDataSize = "{:02x}".format(len(name)//2)
        if(xV>255):
            x="ff"+"{:02x}".format(xV%255)
        else:
            x="00"+"{:02x}".format(xV)
        y="{:02x}".format(yV)

        data = nameDataSize+x+y+name
        dataLen = "{:02x}".format(len(data)//2)

        cmd = commandHeaderAndAddress+dataLen+"34"+data
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()
    
    def clearText(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"003545")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def requestAll(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002030")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()
    
    def saveModelToSDCard(self,idVal):
        idVal = "{:04x}".format(idVal)
        idVal = idVal[2:]+idVal[0:2]
        cmd = commandHeaderAndAddress+"0232"+idVal
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def loadModelFromSDCard(self,idVal):
        idVal = "{:04x}".format(idVal)
        idVal = idVal[2:]+idVal[0:2]
        cmd = commandHeaderAndAddress+"0233"+idVal
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def savePictureToSDCard(self):
        self.huskylensSer.timeout=5
        cmd = self.cmdToBytes(commandHeaderAndAddress+"003040")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()
    
    def saveScreenshotToSDCard(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"003949")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()

    def blocks(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002131")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def arrows(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002232")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def learned(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002333")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def learnedBlocks(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002434")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def learnedArrows(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002535")
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def getObjectByID(self, idVal):
        idVal = "{:04x}".format(idVal)
        idVal = idVal[2:]+idVal[0:2]
        cmd = commandHeaderAndAddress+"0226"+idVal
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def getBlocksByID(self, idVal):
        idVal = "{:04x}".format(idVal)
        idVal = idVal[2:]+idVal[0:2]
        cmd = commandHeaderAndAddress+"0227"+idVal
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def getArrowsByID(self, idVal):
        idVal = "{:04x}".format(idVal)
        idVal = idVal[2:]+idVal[0:2]
        cmd = commandHeaderAndAddress+"0228"+idVal
        cmd += self.calculateChecksum(cmd)
        cmd = self.cmdToBytes(cmd)
        self.writeToHuskyLens(cmd)
        return self.processReturnData()[0]

    def algorthim(self, alg):
        if alg in algorthimsByteID:
            cmd = commandHeaderAndAddress+"022d"+algorthimsByteID[alg]
            cmd += self.calculateChecksum(cmd)
            cmd = self.cmdToBytes(cmd)
            self.writeToHuskyLens(cmd)
            return self.processReturnData()
        else:
            print("INCORRECT ALGORITHIM NAME")

    def count(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002030")
        self.writeToHuskyLens(cmd)
        return len(self.processReturnData())
    
    def learnedObjCount(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002030")
        self.writeToHuskyLens(cmd)
        return self.processReturnData(numIdLearnFlag=True)[-1]
    
    def frameNumber(self):
        cmd = self.cmdToBytes(commandHeaderAndAddress+"002030")
        self.writeToHuskyLens(cmd)
        return self.processReturnData(frameFlag=True)[-1]