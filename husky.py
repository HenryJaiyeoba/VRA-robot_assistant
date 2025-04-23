from huskylib import HuskyLensLibrary
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

# --- 3. Define IDs for learned objects ---
# Note: Objects need to be learned using the HuskyLens device itself first.
# These IDs correspond to the order they were learned (ID 1 is the first, ID 2 the second, etc.)
PERSON_ID = 1
OBSTACLE_ID = 2 

# Optional: Assign custom names (if needed, uncomment and adjust)
# print(f"Assigning name 'Person' to ID {PERSON_ID}")
# hl.setCustomName("Person", PERSON_ID)
# time.sleep(0.1)
# print(f"Assigning name 'Obstacle' to ID {OBSTACLE_ID}")
# hl.setCustomName("Obstacle", OBSTACLE_ID)
# time.sleep(0.1)

print("Starting object detection loop...")

# --- 4 & 5. Detect learned objects and run decision function ---
try:
    while True:      
        results = hl.learnedBlocks() 
        # results = True 
        
        person_detected = False
        obstacle_detected = False

        if results and isinstance(results, list) and len(results) > 0:
            print(f"Detected {len(results)} objects")
            for obj in results:
                print(f"Detected: Type={obj.type}, ID={obj.ID}, Center=({obj.x},{obj.y}), Size=({obj.width}x{obj.height})")
                
                if obj.ID == PERSON_ID:
                    person_detected = True
                elif obj.ID == OBSTACLE_ID:
                    obstacle_detected = True
                # Add more 'elif obj.ID == ...' for other learned objects
        else:
            print("No objects detected or communication issue.")

        # Decision Logic
        if person_detected:
            print("ACTION: Person detected! Please move out of the way!")
            # TODO: Integrate with GUI to display the warning message
            # Example: call_gui_function_to_show_warning("Person detected! Move!")

        elif obstacle_detected:
            print("ACTION: Obstacle detected! Engaging obstacle avoidance.")
            # TODO: Integrate with motor control system for avoidance
            # Example: call_motor_control_avoidance()
            # TODO: Integrate with GUI to display status
            # Example: call_gui_function_to_show_status("Obstacle Avoidance Mode")
        else:
            print("No relevant objects detected. Continuing monitoring.")
            pass

        time.sleep(0.5) 

except KeyboardInterrupt:
    print("Stopping detection.")
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()  

finally:
    print("Exiting husky.py")
