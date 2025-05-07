#!/usr/bin/env python3
# filepath: /home/vrapi/vra_robot/VRA-robot_assistant/test_husky.py
import time
import smbus
from huskylibTest import HuskyLensLibrary

def check_i2c_connection():
    try:
        bus = smbus.SMBus(0)  # Use 1 for newer Pi models, 0 for older ones
        print("I2C bus initialized successfully")
        
        # Try to detect devices
        print("Scanning I2C bus...")
        for addr in range(0x03, 0x78):
            try:
                bus.read_byte(addr)
                print(f"Found device at address: 0x{addr:02x}")
            except:
                pass
                
        return True
    except Exception as e:
        print(f"Error initializing I2C: {str(e)}")
        return False

def test_husky():
    print("Starting HuskyLens test...")
    
    # First check basic I2C functionality
    if not check_i2c_connection():
        print("I2C bus not accessible. Check connections and permissions.")
        return
    
    try:
        print("Initializing HuskyLens...")
        hl = HuskyLensLibrary("I2C", "", address=0x32)
        
        print("Sending knock command...")
        response = hl.knock()
        print(f"Response: {response}")
        
        return response
    except Exception as e:
        print(f"Error communicating with HuskyLens: {str(e)}")
        return None

if __name__ == "__main__":
    print("HuskyLens Test Utility")
    print("----------------------")
    
    try:
        result = test_husky()
        if result == "Knock Recieved":
            print("✅ HuskyLens is working correctly!")
        else:
            print("❌ HuskyLens test failed.")
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    
    print("Test complete.")