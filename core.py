import pygame
import sys
import RPi.GPIO as GPIO
import os 
import time
from faq_manager import FAQManager
from gui import RobotInterface, Colors


FPS = 30

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
        
        message_counter = 0
        
        
        running = True
        while running:
            app.handle_events()
            choice = 3
            app.update()

            if choice == 2:
                # Select a message and display it
                app.is_showing_message = True
                msg = messages[message_counter % len(messages)]
                app.message_text = msg["text"]
                app.message_font_size = msg["font_size"]
                app.message_bg_color = msg["color"]
                
                # Update message tracking
                message_counter += 1

            
            # Clear message after duration expires
            # if message_displayed and (current_time - last_message_time) > message_duration:
            #     self.clear_message()
            #     message_displayed = False
            
            app.draw()
            app.clock.tick(FPS)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        GPIO.cleanup()
        pygame.quit()
        print("\nApplication terminated")
        sys.exit(0)


if __name__ == "__main__":
    main()