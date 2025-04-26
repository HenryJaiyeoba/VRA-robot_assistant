import pygame
import sys
import RPi.GPIO as GPIO
import os 
import time
from huskylibTest import HuskyLensLibrary
from faq_manager import FAQManager
from gui import RobotInterface, Colors

# Constants
FPS = 30
PERSON_ID = 1  
OBSTACLE_ID = 2  
CHECK_INTERVAL = 0.3  

class HuskyGUIApp:
    def __init__(self):
        self.app = RobotInterface()
        
        self.husky_connected = False
        self.hl = self.initialize_huskylens()
        
        self.last_detection_time = 0
        self.detection_cooldown = CHECK_INTERVAL
        
        # Track current display state
        self.current_display_type = None  
        self.message_start_time = 0
        self.message_duration = 3  

    def initialize_huskylens(self):
        """Initialize and connect to HuskyLens"""
        print("Connecting to HuskyLens...")
        try:
            hl = HuskyLensLibrary("I2C", "", address=0x32)
            
            knock_attempts = 0
            max_attempts = 5
            while knock_attempts < max_attempts:
                if hl.knock() == "Knock Recieved":
                    print("HuskyLens connection successful!")
                    self.husky_connected = True
                    break
                else:
                    print(f"Knock failed. Retrying... ({knock_attempts + 1}/{max_attempts})")
                    knock_attempts += 1
                    time.sleep(0.5)
            
            if self.husky_connected:
                try:
                    hl.algorthim("ALGORITHM_OBJECT_RECOGNITION")
                    print("Algorithm switched to Object Recognition.")
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Warning: Failed to switch algorithm: {str(e)}")
            
            return hl
            
        except Exception as e:
            print(f"Error initializing HuskyLens: {str(e)}")
            self.husky_connected = False
            return None
    
    def check_huskylens_detection(self):
        """Check for object detection via HuskyLens"""
        if not self.husky_connected or not self.hl:
            return
        
        current_time = time.time()
        if (current_time - self.last_detection_time) < self.detection_cooldown:
            return
        
        self.last_detection_time = current_time

        try:
            results = self.hl.blocks()
            

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

                if person_detected:
                    self.show_person_message()
                elif obstacle_detected:
                    self.show_obstacle_message()
            else:
                self.check_message_timeout()
                
        except Exception as e:
            print(f"Error during HuskyLens detection: {str(e)}")
    
    def show_person_message(self):
        """Show person detection message"""
        if self.current_display_type != "person":
            print("Person detected! Showing warning message.")
            self.app.is_showing_message = True
            self.app.message_text = "Please get out of the way!!"
            self.app.message_font_size = "large"
            self.app.message_bg_color = Colors.ERROR
            self.app.status_message = "Person detected"
            
            self.current_display_type = "person"
            self.message_start_time = time.time()
    
    def show_obstacle_message(self):
        """Show obstacle detection message"""
        if self.current_display_type != "obstacle":
            print("Obstacle detected! Showing info message.")
            self.app.is_showing_message = True
            self.app.message_text = "Avoiding Obstacle..."
            self.app.message_font_size = "regular" 
            self.app.message_bg_color = Colors.SUCCESS
            self.app.status_message = "Obstacle avoidance"
            
            self.current_display_type = "obstacle"
            self.message_start_time = time.time()
    
    def check_message_timeout(self):
        """Check if current message should be cleared due to timeout"""
        if (self.current_display_type and 
            time.time() - self.message_start_time > self.message_duration):
            print("No objects detected. Clearing message.")
            self.app.is_showing_message = False
            self.app.status_message = "Ready for navigation"
            self.current_display_type = None
    
    def run(self):
        """Main application loop"""
        running = True
        try:
            while running:
                self.app.handle_events()
                self.check_huskylens_detection()
                self.app.update()
                self.app.draw()
                self.app.clock.tick(FPS)
                
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        finally:
            # Clean up
            GPIO.cleanup()
            pygame.quit()
            sys.exit(0)

if __name__ == "__main__":
    app = HuskyGUIApp()
    app.run()