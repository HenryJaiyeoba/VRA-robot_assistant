import pygame
import sys
import RPi.GPIO as GPIO
import os 
import random
import time
from faq_manager import FAQManager
# from gui import GUI
from gui import RobotInterface, display_message, clear_message, Colors
# Define FPS locally since it's not exported from gui
FPS = 30


def check_conditions():
    """
    Check system conditions and return True if message should be displayed.
    Replace this with your actual condition checks.
    """
    # Example condition: Check if a file exists
    if os.path.exists("/tmp/show_message.flag"):
        return True
    
    # Example: Check system temperature (simulated)
    system_temp = 85  # Replace with actual temperature reading
    if system_temp > 80:
        return True
    
    return False


def main():
    try:
        app = RobotInterface()
        
        # Sample messages to display
        messages = [
            {"text": "System status: Normal", "font_size": "regular", "color": Colors.INFO},
            {"text": "Battery level: 75%", "font_size": "large", "color": Colors.SUCCESS},
            {"text": "Warning: Connection unstable", "font_size": "large", "color": Colors.WARNING},
            {"text": "Error: Sensor malfunction", "font_size": "large", "color": Colors.ERROR},
        ]
        
        # Message display counter and delay
        message_counter = 0
        message_duration = 3000  # seconds to show each message
        last_message_time = 0
        
        # Flag to track if a message is currently displayed
        message_displayed = False
        
        # Custom main loop instead of app.run()
        running = True
        while running:
            # Process events
            app.handle_events()
            
            # Random decision: 1 = normal update, 2 = show message
            choice = 2
            
            # Update the application state
            app.update()
            
            # If choice is 2 and no message is currently displayed, show a message
            current_time = time.time()
            if choice == 2 and not message_displayed:
                # Select a message and display it
                msg = messages[message_counter % len(messages)]
                display_message(msg["text"], msg["font_size"], msg["color"])
                
                # Update message tracking
                message_counter += 1
                message_displayed = True
                last_message_time = current_time
            
            # Clear message after duration expires
            # if message_displayed and (current_time - last_message_time) > message_duration:
            #     clear_message()
            #     message_displayed = False
            
            # Draw the screen
            app.draw()
            
            # Control the frame rate
            app.clock.tick(FPS)
            
            # Add a small delay to not overwhelm the system with random decisions
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        GPIO.cleanup()
        pygame.quit()
        print("\nApplication terminated")
        sys.exit(0)


if __name__ == "__main__":
    main()