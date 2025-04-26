# VRA - Visual Robot Assistant

## Overview

The Visual Robot Assistant (VRA) is an intelligent robot navigation system with computer vision capabilities. The system combines a touchscreen interface for user interaction with real-time object detection to guide users through buildings while avoiding obstacles.

## Features

- Interactive touchscreen UI for building navigation
- Real-time object and person detection using HuskyLens camera
- Dynamic status message system
- FAQ database for common questions
- Obstacle avoidance warnings
- Building-specific navigation

## System Requirements

- Raspberry Pi (with GPIO capabilities)
- HuskyLens camera module
- Touchscreen display (800x480 resolution)
- Python 3.6+
- Internet connection (for initial setup)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/VRA-robot_assistant.git
cd VRA-robot_assistant
```

### 2. Install required packages

```bash
pip install pygame RPi.GPIO
```

### 3. Configure HuskyLens

Ensure your HuskyLens camera is:

- Connected via I2C to your Raspberry Pi (default address: 0x32)
- Trained to recognize:
  - Object ID 1: Person
  - Object ID 2: Obstacle

## Project Structure

- **gui.py**: Main graphical user interface implementation
- **core.py**: Integration between HuskyLens and GUI systems
- **faq_manager.py**: Manages the FAQ database and queries
- **huskylibTest.py**: HuskyLens communication library
- **data/faq_db.json**: FAQ database

## Usage

### Starting the Application

To start the standard VRA application with HuskyLens integration:

```bash
python core.py
```

To run only the GUI without HuskyLens:

```bash
python gui.py
```

### Navigation

- Use the UP key or tap to select ST Building
- Use the RIGHT key or tap to select CU Building
- Use the LEFT key or tap to select GE Building
- Press ESC key to exit the application

### Automatic Detection Mode

When using `core.py`, the system will automatically:

- Display a warning when a person is detected (Object ID 1)
- Show an "Avoiding Obstacle" message when obstacles are detected (Object ID 2)
- Return to navigation display when no objects are detected

## Development

### Message System

The system provides a flexible message display system that can be called from any module:

```python
from gui import display_message, clear_message, Colors

# Display a message
display_message("Your message here", font_size="large", bg_color=Colors.WARNING)

# Clear the message
clear_message()
```

### FAQ System

The FAQ system supports both general categories and building-specific information:

```python
from faq_manager import FAQManager

# Initialize the FAQ manager
faq = FAQManager()

# Get all questions
all_questions = faq.get_all_questions()

# Search for specific topics
results = faq.search("elevator")
```

## Credits

Developed by the VRA Team (April 2025)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
