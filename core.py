import pygame
import sys
import RPi.GPIO as GPIO
import os 
from faq_manager import FAQManager
from gui import GUI
from gui import RobotInterface


def main():
    try:
        app = RobotInterface()
        app.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
        pygame.quit()
        print("\nApplication terminated")
        sys.exit(0)


if __name__ == "__main__":
    main()