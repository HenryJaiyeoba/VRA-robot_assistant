import pygame
import sys
import os
import time
import json
from pygame.locals import *

import FaqManager

# Try to import RPi.GPIO, but allow for development on non-Raspberry Pi systems
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("Warning: RPi.GPIO module not available. Running in development mode.")
    GPIO_AVAILABLE = False

# FAQ Manager class
class FAQManager:
    def __init__(self, database_file='data/faq_database.json'):
        self.database_file = database_file
        self.faq_data = self.load_database()
        self.current_category = None
        self.selected_question = None
    
    def load_database(self):
        """Load the FAQ database from JSON file"""
        try:
            with open(self.database_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: FAQ database file '{self.database_file}' not found. Creating empty database.")
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.database_file), exist_ok=True)
            # Create empty database structure
            empty_db = {"buildings": {}, "general": [], "services": []}
            with open(self.database_file, 'w') as f:
                json.dump(empty_db, f, indent=4)
            return empty_db
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in '{self.database_file}'.")
            return {"buildings": {}, "general": [], "services": []}
    
    def get_categories(self):
        """Get list of all categories"""
        categories = list(self.faq_data.keys())
        # If 'buildings' is a special category with subcategories
        if 'buildings' in categories:
            categories.remove('buildings')
            categories.extend([f"Building: {building}" for building in self.faq_data['buildings'].keys()])
        return categories
    
    def get_questions_for_category(self, category):
        """Get all questions for a given category"""
        # Check if it's a building category
        if category.startswith("Building: "):
            building_name = category.replace("Building: ", "")
            if 'buildings' in self.faq_data and building_name in self.faq_data['buildings']:
                return self.faq_data['buildings'][building_name]
            return []
        
        # Otherwise it's a regular category
        if category in self.faq_data:
            return self.faq_data[category]
        return []
    
    def get_all_questions(self):
        """Get all questions from all categories"""
        all_questions = []
        
        # Add questions from regular categories
        for category in self.faq_data:
            if category != 'buildings':
                for q in self.faq_data[category]:
                    all_questions.append({
                        'category': category,
                        'data': q
                    })
        
        # Add questions from building categories
        if 'buildings' in self.faq_data:
            for building in self.faq_data['buildings']:
                for q in self.faq_data['buildings'][building]:
                    all_questions.append({
                        'category': f"Building: {building}",
                        'data': q
                    })
        
        return all_questions

# Initialize Pygame
pygame.init()

# Screen dimensions (for 7-inch Raspberry Pi touchscreen)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Robot Interface')

# Create a clock object to manage frame rate
clock = pygame.time.Clock()
FPS = 30

# Define color scheme
class Colors:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 100)
    LIGHT_GRAY = (200, 200, 200)
    
    # Primary colors
    PRIMARY = (25, 118, 210)    # Blue
    PRIMARY_LIGHT = (67, 160, 255)
    PRIMARY_DARK = (0, 79, 163)
    
    # Secondary colors
    SECONDARY = (230, 74, 25)   # Orange
    SECONDARY_LIGHT = (255, 114, 64)
    SECONDARY_DARK = (187, 36, 0)
    
    # Building colors
    ST_BUILDING = (76, 175, 80)  # Green
    CU_BUILDING = (255, 193, 7)  # Amber
    GE_BUILDING = (156, 39, 176) # Purple
    
    # Alert colors
    WARNING = (255, 152, 0)     # Orange
    ERROR = (211, 47, 47)       # Red
    SUCCESS = (46, 125, 50)     # Green
    INFO = (2, 136, 209)        # Light Blue

# Define layout dimensions
class Layout:
    # Header section at the top
    HEADER_HEIGHT = 60
    
    # Main content area dimensions
    CONTENT_Y = HEADER_HEIGHT
    CONTENT_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT
    
    # Left panel for navigation
    NAV_WIDTH = SCREEN_WIDTH * 0.4
    
    # Right panel for FAQ and other info
    INFO_X = NAV_WIDTH
    INFO_WIDTH = SCREEN_WIDTH - NAV_WIDTH
    
    # Footer for status and warnings
    FOOTER_HEIGHT = 50
    FOOTER_Y = SCREEN_HEIGHT - FOOTER_HEIGHT
    
    # Padding and margins
    PADDING = 10
    MARGIN = 20

# Load fonts
def load_fonts():
    fonts = {
        'small': pygame.font.Font(None, 24),
        'regular': pygame.font.Font(None, 32),
        'large': pygame.font.Font(None, 48),
        'title': pygame.font.Font(None, 64)
    }
    return fonts

# UI Drawing Functions
class UI:
    def __init__(self):
        self.fonts = load_fonts()
        
    def draw_text(self, surface, text, font_size, color, x, y, align="left", max_width=None):
        """Draw text with specified font size and alignment"""
        font = self.fonts.get(font_size, self.fonts['regular'])

        # Handle text wrapping if max_width is specified
        if max_width:
            words = text.split(' ')
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                # Check if adding this word would exceed max width
                if font.size(test_line)[0] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:  # only append if not empty
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            # Add the last line
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw each line
            text_height = font.size('Tg')[1]  # Approximate line height
            total_height = len(lines) * (text_height + 2)
            current_y = y
            
            rects = []
            for line in lines:
                text_surface = font.render(line, True, color)
                text_rect = text_surface.get_rect()
                
                # Adjust position based on alignment
                if align == "center":
                    text_rect.centerx = x
                    text_rect.top = current_y
                elif align == "right":
                    text_rect.right = x
                    text_rect.top = current_y
                else:  # left alignment
                    text_rect.left = x
                    text_rect.top = current_y
                    
                surface.blit(text_surface, text_rect)
                rects.append(text_rect)
                current_y += text_height + 2
            
            # Return the bounding rect that encompasses all lines
            if rects:
                bounding_rect = rects[0].unionall(rects[1:]) if len(rects) > 1 else rects[0]
                return bounding_rect
            return pygame.Rect(x, y, 0, 0)
        else:
            # Simple single-line rendering
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect()
            
            # Adjust position based on alignment
            if align == "center":
                text_rect.center = (x, y)
            elif align == "right":
                text_rect.right = x
                text_rect.top = y
            else:  # left alignment
                text_rect.left = x
                text_rect.top = y
                
            surface.blit(text_surface, text_rect)
            return text_rect
    
    def draw_button(self, surface, text, x, y, width=200, height=50, 
                   color=Colors.PRIMARY, text_color=Colors.WHITE, 
                   border_radius=10, font_size='regular'):
        """Draw a button with text centered inside"""
        # Draw button background
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, button_rect, border_radius=border_radius)
        
        # Draw button text
        font = self.fonts.get(font_size, self.fonts['regular'])
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        surface.blit(text_surf, text_rect)
        
        return button_rect
    
    def draw_panel(self, surface, x, y, width, height, 
                  bg_color=Colors.WHITE, border_color=None, 
                  border_width=0, border_radius=0):
        """Draw a panel/container with optional border"""
        panel_rect = pygame.Rect(x, y, width, height)
        
        # Draw background
        pygame.draw.rect(surface, bg_color, panel_rect, border_radius=border_radius)
        
        # Draw border if specified
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, panel_rect, 
                           width=border_width, border_radius=border_radius)
            
        return panel_rect
    
    def draw_header(self, surface, title="Robot Interface"):
        """Draw the header section with title"""
        # Draw header background
        header_rect = self.draw_panel(
            surface, 
            0, 0, 
            SCREEN_WIDTH, Layout.HEADER_HEIGHT,
            bg_color=Colors.PRIMARY
        )
        
        # Draw title text
        self.draw_text(
            surface, 
            title, 
            'large', 
            Colors.WHITE,
            SCREEN_WIDTH // 2, 
            Layout.HEADER_HEIGHT // 2,
            align="center"
        )
        
        return header_rect
    
    def draw_footer(self, surface, status_text="Ready"):
        """Draw the footer with status text"""
        # Draw footer background
        footer_rect = self.draw_panel(
            surface,
            0, Layout.FOOTER_Y,
            SCREEN_WIDTH, Layout.FOOTER_HEIGHT,
            bg_color=Colors.LIGHT_GRAY
        )
        
        # Draw status text
        self.draw_text(
            surface,
            status_text,
            'regular',
            Colors.BLACK,
            Layout.MARGIN,
            Layout.FOOTER_Y + Layout.PADDING,
            align="left"
        )
        
        return footer_rect
    
    def draw_navigation_panel(self, surface):
        """Draw the navigation panel with building options"""
        # Draw navigation panel background
        nav_panel = self.draw_panel(
            surface,
            0, Layout.CONTENT_Y,
            Layout.NAV_WIDTH, Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT,
            bg_color=Colors.LIGHT_GRAY,
            border_color=Colors.GRAY,
            border_width=1
        )
        
        # Draw navigation title
        title_y = Layout.CONTENT_Y + Layout.MARGIN
        self.draw_text(
            surface,
            "Where would you like to go?",
            'regular',
            Colors.BLACK,
            Layout.NAV_WIDTH // 2,
            title_y,
            align="center"
        )
        
        # Draw building buttons
        button_width = Layout.NAV_WIDTH - (Layout.MARGIN * 2)
        button_height = 60
        button_spacing = 20
        
        # ST Building Button (UP)
        st_y = title_y + 50
        st_button = self.draw_button(
            surface,
            "Press UP for ST Building",
            Layout.MARGIN,
            st_y,
            width=button_width,
            height=button_height,
            color=Colors.ST_BUILDING
        )
        
        # CU Building Button (RIGHT)
        cu_y = st_y + button_height + button_spacing
        cu_button = self.draw_button(
            surface,
            "Press RIGHT for CU Building",
            Layout.MARGIN,
            cu_y,
            width=button_width,
            height=button_height,
            color=Colors.CU_BUILDING
        )
        
        # GE Building Button (LEFT)
        ge_y = cu_y + button_height + button_spacing
        ge_button = self.draw_button(
            surface,
            "Press LEFT for GE Building",
            Layout.MARGIN,
            ge_y,
            width=button_width,
            height=button_height,
            color=Colors.GE_BUILDING
        )
        
        return {
            'panel': nav_panel,
            'st_button': st_button,
            'cu_button': cu_button,
            'ge_button': ge_button
        }
    
    def draw_info_panel(self, surface, faq_manager):
        """Draw the information/FAQ panel with actual FAQ data"""
        # Draw info panel background
        info_panel = self.draw_panel(
            surface,
            Layout.INFO_X, Layout.CONTENT_Y,
            Layout.INFO_WIDTH, Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT,
            bg_color=Colors.WHITE,
            border_color=Colors.GRAY,
            border_width=1
        )
        
        # Draw info panel title
        title_y = Layout.CONTENT_Y + Layout.MARGIN
        self.draw_text(
            surface,
            "Frequently Asked Questions",
            'regular',
            Colors.BLACK,
            Layout.INFO_X + (Layout.INFO_WIDTH // 2),
            title_y,
            align="center"
        )
        
        # Get all questions from FAQ database
        all_questions = faq_manager.get_all_questions()
        
        # Draw FAQ list
        content_y = title_y + 50
        question_buttons = []
        
        # If we have a selected question, display it and its answer
        if faq_manager.selected_question:
            # Display the selected question
            question_text = faq_manager.selected_question['data']['question']
            answer_text = faq_manager.selected_question['data']['answer']
            
            # Draw question
            question_rect = self.draw_panel(
                surface,
                Layout.INFO_X + Layout.MARGIN,
                content_y,
                Layout.INFO_WIDTH - (Layout.MARGIN * 2),
                60,
                bg_color=Colors.PRIMARY_LIGHT,
                border_radius=5
            )
            
            self.draw_text(
                surface,
                question_text,
                'regular',
                Colors.WHITE,
                Layout.INFO_X + Layout.MARGIN + 10,
                content_y + 15,
                max_width=Layout.INFO_WIDTH - (Layout.MARGIN * 2) - 20
            )
            
            # Draw back button
            back_button = self.draw_button(
                surface,
                "Back to FAQs",
                Layout.INFO_X + Layout.MARGIN,
                content_y + 70,
                width=150,
                height=40,
                color=Colors.SECONDARY
            )
            question_buttons.append(('back', back_button))
            
            # Draw answer
            answer_y = content_y + 130
            answer_panel = self.draw_panel(
                surface,
                Layout.INFO_X + Layout.MARGIN,
                answer_y,
                Layout.INFO_WIDTH - (Layout.MARGIN * 2),
                Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT - answer_y - Layout.MARGIN,
                bg_color=Colors.LIGHT_GRAY,
                border_radius=5
            )
            
            self.draw_text(
                surface,
                answer_text,
                'regular',
                Colors.BLACK,
                Layout.INFO_X + Layout.MARGIN + 10,
                answer_y + 10,
                max_width=Layout.INFO_WIDTH - (Layout.MARGIN * 2) - 20
            )
            
        else:
            # Display list of questions
            for i, q in enumerate(all_questions):
                if i < 6:  # Limit to 6 questions to fit on screen
                    q_height = 50
                    q_y = content_y + (i * (q_height + 10))
                    
                    # Draw question button
                    q_button = self.draw_panel(
                        surface,
                        Layout.INFO_X + Layout.MARGIN,
                        q_y,
                        Layout.INFO_WIDTH - (Layout.MARGIN * 2),
                        q_height,
                        bg_color=Colors.PRIMARY_LIGHT,
                        border_radius=5
                    )
                    
                    # Draw question text
                    self.draw_text(
                        surface,
                        q['data']['question'],
                        'small',
                        Colors.WHITE,
                        Layout.INFO_X + Layout.MARGIN + 10,
                        q_y + (q_height // 3),
                        max_width=Layout.INFO_WIDTH - (Layout.MARGIN * 2) - 20
                    )
                    
                    question_buttons.append((q, q_button))
        
        return info_panel, question_buttons
    
    def draw_warning(self, surface, message="Warning: Obstacle detected!"):
        """Draw a warning message"""
        # Create semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # semi-transparent black
        surface.blit(overlay, (0, 0))
        
        # Draw warning panel
        warning_width = 600
        warning_height = 150
        warning_x = (SCREEN_WIDTH - warning_width) // 2
        warning_y = (SCREEN_HEIGHT - warning_height) // 2
        
        warning_panel = self.draw_panel(
            surface,
            warning_x, warning_y,
            warning_width, warning_height,
            bg_color=Colors.ERROR,
            border_radius=10
        )
        
        # Draw warning icon (simple circle)
        icon_radius = 25
        icon_x = warning_x + 50
        icon_y = warning_y + (warning_height // 2)
        pygame.draw.circle(surface, Colors.WHITE, (icon_x, icon_y), icon_radius)
        pygame.draw.circle(surface, Colors.ERROR, (icon_x, icon_y), icon_radius - 5)
        
        # Draw exclamation mark
        font = self.fonts['large']
        text_surf = font.render("!", True, Colors.WHITE)
        text_rect = text_surf.get_rect(center=(icon_x, icon_y))
        surface.blit(text_surf, text_rect)
        
        # Draw warning text
        self.draw_text(
            surface,
            message,
            'large',
            Colors.WHITE,
            warning_x + 100,
            warning_y + (warning_height // 2),
            align="left"
        )
        
        return warning_panel

# Main application class
class RobotInterface:
    def __init__(self):
        self.ui = UI()
        self.running = True
        self.show_warning = False
        self.warning_message = ""
        self.warning_time = 0
        self.warning_duration = 3  # seconds
        
        # Initialize FAQ manager
        self.faq_manager = FAQManager()
        
        # UI elements that need click detection
        self.nav_buttons = {}
        self.faq_buttons = []
        
        # Status message
        self.status_message = "Ready for navigation"
    
    def handle_events(self):
        """Process pygame events"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                # Handle key presses for testing
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_UP:
                    self.display_building_selection("ST Building")
                elif event.key == K_RIGHT:
                    self.display_building_selection("CU Building")
                elif event.key == K_LEFT:
                    self.display_building_selection("GE Building")
                elif event.key == K_w:  # Test warning message
                    self.show_warning_message("Obstacle detected! Please move.")
            
            # Handle mouse clicks (for touch screen)
            elif event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Check navigation buttons
                if self.nav_buttons:
                    if self.nav_buttons.get('st_button') and self.nav_buttons['st_button'].collidepoint(pos):
                        self.display_building_selection("ST Building")
                    elif self.nav_buttons.get('cu_button') and self.nav_buttons['cu_button'].collidepoint(pos):
                        self.display_building_selection("CU Building")
                    elif self.nav_buttons.get('ge_button') and self.nav_buttons['ge_button'].collidepoint(pos):
                        self.display_building_selection("GE Building")
                
                # Check FAQ buttons
                for q_data, q_rect in self.faq_buttons:
                    if q_rect.collidepoint(pos):
                        if q_data == 'back':
                            # Go back to FAQ list
                            self.faq_manager.selected_question = None
                        else:
                            # Show selected question and answer
                            self.faq_manager.selected_question = q_data
                        break
    
    def display_building_selection(self, building):
        """Display building selection message"""
        print(f"Selected: {building}")
        self.status_message = f"Moving to {building}..."
        # In a real implementation, you would send a signal to Arduino
        # or handle the movement logic here
        
    def show_warning_message(self, message):
        """Show a warning message for a specified duration"""
        self.show_warning = True
        self.warning_message = message
        self.warning_time = time.time()
    
    def update(self):
        """Update game state"""
        # Check if warning should be dismissed
        if self.show_warning and time.time() - self.warning_time > self.warning_duration:
            self.show_warning = False
    
    def draw(self):
        """Draw the interface"""
        # Fill background
        screen.fill(Colors.BLACK)
        
        # Draw header
        self.ui.draw_header(screen, "VRA Mobile Robot:")
        
        # Draw navigation panel and store button references
        self.nav_buttons = self.ui.draw_navigation_panel(screen)
        
        # Draw info panel with FAQ data and store FAQ button references
        _, self.faq_buttons = self.ui.draw_info_panel(screen, self.faq_manager)
        
        # Draw footer
        self.ui.draw_footer(screen, self.status_message)
        
        # Draw warning if active
        if self.show_warning:
            self.ui.draw_warning(screen, self.warning_message)
        
        # Update the display
        pygame.display.flip()
    
    def run(self):
        """Main application loop"""
        # Check if we need to create sample FAQ data
        if not self.faq_manager.faq_data['general'] and not self.faq_manager.faq_data.get('buildings', {}):
            self.create_sample_faq_data()
            
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)
        
        # Clean up
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        pygame.quit()
        sys.exit()
    
    def create_sample_faq_data(self):
        """Create sample FAQ data if the database is empty"""
        faq_data = {
            "buildings": {
                "ST Building": [
                    {
                        "id": "st1",
                        "question": "What departments are located in the ST Building?",
                        "answer": "The ST Building houses the Science and Technology departments, including Computer Science, Physics, and Engineering labs."
                    },
                    {
                        "id": "st2",
                        "question": "What are the ST Building hours?",
                        "answer": "The ST Building is open from 7:00 AM to 10:00 PM on weekdays, and 9:00 AM to 6:00 PM on weekends."
                    },
                    {
                        "id": "st3",
                        "question": "Where can I find the computer labs in ST Building?",
                        "answer": "Computer labs are located on the 2nd floor of the ST Building, rooms ST201-ST210."
                    }
                ],
                "CU Building": [
                    {
                        "id": "cu1",
                        "question": "What facilities are in the CU Building?",
                        "answer": "The CU Building contains the Student Union, cafeteria, bookstore, and student organization offices."
                    },
                    {
                        "id": "cu2",
                        "question": "What are the cafeteria hours in CU Building?",
                        "answer": "The cafeteria is open from 7:30 AM to 7:00 PM on weekdays, and 10:00 AM to 2:00 PM on weekends."
                    },
                    {
                        "id": "cu3",
                        "question": "Where is the student help desk in CU Building?",
                        "answer": "The student help desk is located on the 1st floor of the CU Building, next to the main entrance."
                    }
                ],
                "GE Building": [
                    {
                        "id": "ge1",
                        "question": "What classes are held in the GE Building?",
                        "answer": "The GE Building hosts General Education classes including Humanities, Social Sciences, and Arts courses."
                    },
                    {
                        "id": "ge2",
                        "question": "Where is the auditorium in GE Building?",
                        "answer": "The main auditorium is on the ground floor of the GE Building, room GE101."
                    },
                    {
                        "id": "ge3",
                        "question": "Are there study areas in the GE Building?",
                        "answer": "Yes, there are study lounges on each floor of the GE Building, with the largest one on the 3rd floor."
                    }
                ]
            },
            "general": [
                {
                    "id": "gen1",
                    "question": "What are the campus WiFi login details?",
                    "answer": "Connect to 'Campus-WiFi' network and use your student ID and password to log in."
                },
                {
                    "id": "gen2",
                    "question": "Where can I find the nearest restrooms?",
                    "answer": "Restrooms are available on every floor of each building, typically near the elevators or stairwells."
                },
                {
                    "id": "gen3",
                    "question": "How do I contact campus security?",
                    "answer": "Campus security can be reached at extension 5555 from any campus phone, or at (555) 123-5555."
                }
            ],
            "services": [
                {
                    "id": "svc1",
                    "question": "Where is the financial aid office?",
                    "answer": "The financial aid office is located on the 2nd floor of the CU Building, room CU205."
                },
                {
                    "id": "svc2",
                    "question": "How do I reserve a study room?",
                    "answer": "Study rooms can be reserved through the online portal at reserve.campus.edu or at the library information desk."
                },
                {
                    "id": "svc3",
                    "question": "What dining options are available on campus?",
                    "answer": "The main cafeteria is in the CU Building, with coffee shops in the ST and GE Buildings. Food trucks are usually available near the quad area."
                }
            ]
        }
        
        # Save the FAQ data
        os.makedirs(os.path.dirname(self.faq_manager.database_file), exist_ok=True)
        with open(self.faq_manager.database_file, 'w') as f:
            json.dump(faq_data, f, indent=4)
        
        # Reload the database
        self.faq_manager.faq_data = faq_data
        print("Created sample FAQ database.")

# Run the application if this is the main script
if __name__ == "__main__":
    try:
        app = RobotInterface()
        app.run()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        pygame.quit()
        print("\nApplication terminated by user.")
        sys.exit(0)
