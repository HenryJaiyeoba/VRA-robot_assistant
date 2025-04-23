from huskylibTest import HuskyLensLibrary
import time


hl = HuskyLensLibrary("I2C", "", address=0x32)

# --- 1. Knock to establish connection ---
print("Attempting to connect to HuskyLens...")
knock_attempts = 0
max_attempts = 5
while knock_attempts < max_attempts:
    if hl.knock() == "Knock Recieved":
        print("HuskyLens connection successful!")
        break
    else:
        print(f"Knock failed. Retrying... ({knock_attempts + 1}/{max_attempts})")
        knock_attempts += 1
        time.sleep(0.5)
else:
    print("Error: Could not connect to HuskyLens after multiple attempts.")
    exit() 

# --- 2. Forcefully swap to object recognition ---
print("Switching to Object Recognition algorithm...")
try:
    hl.algorthim("ALGORITHM_OBJECT_RECOGNITION")
    print("Algorithm switched to Object Recognition.")
except Exception as e:
    print(f"Warning: Failed to confirm algorithm switch. {str(e)}")
time.sleep(0.5) 

# --- 3. Main detection loop ---
try:
    print("Starting object detection...")
    while True:
        try:
            results = hl.blocks()
            if results and len(results) > 0:
                print(f"Detected {len(results)} objects")
                print("Detected objects: ", results[0])
            else:
                print("No objects detected.")
            time.sleep(1)
        except IndexError as ie:
            print(f"Index error during detection: {ie}")
            time.sleep(1)
        except Exception as e:
            print(f"Error during detection: {e}")
            time.sleep(1)
except KeyboardInterrupt:
    print("Program stopped by user")
except Exception as e:
    print(f"Unexpected error: {e}")