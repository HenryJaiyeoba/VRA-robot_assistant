#!/usr/bin/env python3
"""
Message Panel Demo - Shows how to trigger custom message panels from another file
This example demonstrates how to use the message display functions from gui.py
"""

import time
import sys
from gui import display_message, clear_message, Colors

def show_demo_messages():
    """Show a series of demo messages using the display_message function"""
    
    # Display an info message
    print("Displaying INFO message...")
    display_message("This is an information message", "regular", Colors.INFO)
    time.sleep(3)
    
    # Display a warning message
    print("Displaying WARNING message...")
    display_message("WARNING: Battery is low!", "large", Colors.WARNING)
    time.sleep(3)
    
    # Display an error message
    print("Displaying ERROR message...")
    display_message("ERROR: Connection lost", "title", Colors.ERROR)
    time.sleep(3)
    
    # Display a success message
    print("Displaying SUCCESS message...")
    display_message("Successfully connected to robot", "large", Colors.SUCCESS)
    time.sleep(3)
    
    # Clear the message
    print("Clearing message...")
    clear_message()
    time.sleep(1)
    
    print("Demo completed!")

if __name__ == "__main__":
    print("Starting message panel demo")
    print("Press Ctrl+C to exit")
    try:
        show_demo_messages()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    sys.exit(0)