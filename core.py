#!/usr/bin/env python3
"""
VRA Core Module - HuskyLens Integration with GUI Interface

This module combines the HuskyLens computer vision capabilities with the VRA GUI system,
enabling object recognition and displaying relevant messages based on detected objects.

The system connects to a HuskyLens via I2C, configures it for object recognition mode,
and continuously monitors for recognized objects. When specific objects are detected
(person or obstacle), appropriate messages are shown in the navigation panel.

Dependencies:
- pygame for GUI rendering
- RPi.GPIO for hardware control
- HuskyLensLibrary for HuskyLens communication
- gui module for interface components

Author: HenryJaiyeoba
Last updated: April 26, 2025
"""

import pygame
import sys
import RPi.GPIO as GPIO
import os 
import time
from huskylibTest import HuskyLensLibrary
from faq_manager import FAQManager
from gui import RobotInterface, Colors

# Constants for application configuration
FPS = 30                # Frame rate for GUI updates
PERSON_ID = 1           # HuskyLens ID for person detection
OBSTACLE_ID = 2         # HuskyLens ID for obstacle detection
CHECK_INTERVAL = 0.3    # Time between HuskyLens checks (seconds)

class HuskyGUIApp:
    """
    Main application class that integrates HuskyLens with the VRA GUI.
    
    This class establishes communication with the HuskyLens vision sensor,
    processes object detection results, and updates the GUI accordingly.
    It serves as the bridge between computer vision and user interface.
    """
    
    def __init__(self):
        """Initialize the application with GUI and HuskyLens components."""
        # Create the main interface controller
        self.app = RobotInterface()
        
        # HuskyLens connection status and instance
        self.husky_connected = False
        self.hl = self.initialize_huskylens()
        
        # Detection timing control to prevent overwhelming the system
        self.last_detection_time = 0
        self.detection_cooldown = CHECK_INTERVAL
        
        # Message display settings
        self.current_display_type = None  # Tracks what is currently displayed ("person", "obstacle", or None)
        self.message_start_time = 0       # When the current message was first displayed
        self.message_duration = 3         # How long messages should stay visible (seconds)

    def initialize_huskylens(self):
        """
        Initialize connection to the HuskyLens vision sensor.
        
        This method:
        1. Attempts to establish an I2C connection to the HuskyLens
        2. Sends knock commands to verify communication
        3. Configures the device for object recognition mode
        
        Returns:
            HuskyLensLibrary instance or None if connection fails
        """
        print("Connecting to HuskyLens...")
        try:
            # Create HuskyLens connection via I2C bus at default address 0x32
            hl = HuskyLensLibrary("I2C", "", address=0x32)
            
            # Verify connection with multiple knock attempts
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
            
            # Set algorithm mode if connection was successful
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
        """
        Check for objects detected by the HuskyLens and update the interface.
        
        This method:
        1. Ensures the HuskyLens is connected before proceeding
        2. Controls timing to avoid excessive polling
        3. Processes detected objects and identifies persons and obstacles
        4. Triggers appropriate UI messages based on detected objects
        5. Clears messages when objects are no longer detected
        
        Called repeatedly during the main application loop.
        """
        # Skip if HuskyLens isn't connected
        if not self.husky_connected or not self.hl:
            print("HuskyLens not connected.")
            return
        
        # Throttle detection rate to avoid overwhelming the system
        current_time = time.time()
        if (current_time - self.last_detection_time) < self.detection_cooldown:
            return
        
        self.last_detection_time = current_time

        try:
            # Get detected objects from HuskyLens
            results = self.hl.blocks()
            
            # Track detection flags
            person_detected = False
            obstacle_detected = False
            
            # Process detection results if any objects are found
            if results and isinstance(results, list) and len(results) > 0:
                print(f"Detected {len(results)} objects")
                
                # Check each detected object
                for obj in results:
                    print(f"Detected: Type={obj.type}, ID={obj.ID}, Center=({obj.x},{obj.y}), Size=({obj.width}x{obj.height})")
                    
                    # Set flags based on object ID
                    if obj.ID == PERSON_ID:
                        person_detected = True
                    elif obj.ID == OBSTACLE_ID:
                        obstacle_detected = True

                # Prioritize person detection over obstacle detection
                if person_detected:
                    self.show_person_message()
                elif obstacle_detected:
                    self.show_obstacle_message()
            else:
                # No objects detected, check if we should clear message
                self.check_message_timeout()
                
        except Exception as e:
            print(f"Error during HuskyLens detection: {str(e)}")
    
    def show_person_message(self):
        """
        Display warning message when a person is detected.
        
        This method sets the UI to show a prominent red warning message
        instructing the person to move out of the way. The message is only
        updated if the current display isn't already showing a person warning.
        """
        if self.current_display_type != "person":
            print("Person detected! Showing warning message.")
            # Update UI properties
            self.app.is_showing_message = True
            self.app.message_text = "Please get out of the way!!"
            self.app.message_font_size = "large"
            self.app.message_bg_color = Colors.ERROR
            self.app.status_message = "Person detected"
            
            # Update tracking variables
            self.current_display_type = "person"
            self.message_start_time = time.time()
    
    def show_obstacle_message(self):
        """
        Display notification when an obstacle is detected.
        
        This method sets the UI to show a green success-colored message
        indicating obstacle avoidance is in progress. The message is only
        updated if the current display isn't already showing an obstacle warning.
        """
        if self.current_display_type != "obstacle":
            print("Obstacle detected! Showing info message.")
            # Update UI properties
            self.app.is_showing_message = True
            self.app.message_text = "Avoiding Obstacle..."
            self.app.message_font_size = "regular" 
            self.app.message_bg_color = Colors.SUCCESS
            self.app.status_message = "Obstacle avoidance"
            
            # Update tracking variables
            self.current_display_type = "obstacle"
            self.message_start_time = time.time()
    
    def check_message_timeout(self):
        """
        Check if the current message should be cleared due to timeout.
        
        This method checks if a message has been displayed for longer than
        the configured duration and clears it if needed. This ensures messages
        don't remain on screen indefinitely after objects are no longer detected.
        """
        if (self.current_display_type and 
            time.time() - self.message_start_time > self.message_duration):
            print("No objects detected. Clearing message.")
            # Reset UI to navigation state
            self.app.is_showing_message = False
            self.app.status_message = "Ready for navigation"
            self.current_display_type = None
    
    def run(self):
        """
        Main application loop that runs until the program is terminated.
        
        This method handles the core event loop:
        1. Processing user input through the GUI
        2. Checking for objects via HuskyLens
        3. Updating the interface state
        4. Drawing the interface
        5. Maintaining consistent timing
        
        Also handles proper cleanup on exit.
        """
        running = True
        try:
            while running:
                # Process user input (mouse, keyboard)
                self.app.handle_events()
                
                # Check for objects via HuskyLens
                self.check_huskylens_detection()
                
                # Update interface state
                self.app.update()
                
                # Render the interface
                self.app.draw()
                
                # Control frame rate
                self.app.clock.tick(FPS)
                
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        finally:
            # Clean up hardware resources
            GPIO.cleanup()
            pygame.quit()
            sys.exit(0)

if __name__ == "__main__":
    app = HuskyGUIApp()
    app.run()