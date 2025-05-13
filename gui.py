"""
VRA (Visual Robot Assistant) Graphical User Interface

This module implements the visual interface for a robotic assistant navigation system.
It provides a touchscreen interface for users to:
- Select navigation destinations
- View frequently asked questions
- Display various notification messages and warnings

The GUI is designed for a Raspberry Pi with touchscreen display, showing navigation 
options in the left panel and informational content in the right panel.

Dependencies:
- pygame for rendering graphics and handling user input
- RPi.GPIO for Raspberry Pi GPIO control
- faq_manager for FAQ data handling

Author: HenryJaiyeoba
Last updated: April 26, 2025
"""

import pygame
import sys
import os
import time
import webbrowser
import subprocess
from pygame.locals import *
import RPi.GPIO as GPIO
from faq_manager import FAQManager


pygame.init()

# Screen dimensions (set for Raspberry Pi touchscreen)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('VRA Interface')


clock = pygame.time.Clock()
FPS = 30

# Icons/Emojis as unicode variables for easy access
class Icons:
    """
    Define icon/emoji constants used throughout the application.
    All icons are unicode characters that can be rendered directly as text.
    """
    # Navigation icons
    ARROW_UP = "↑"
    ARROW_DOWN = "↓"
    ARROW_LEFT = "←"
    ARROW_RIGHT = "→"
    
    # Building icons
    BUILDING = "🏢"
    SCHOOL = "🏫"
    HOSPITAL = "🏥"
    
    # Action icons
    CHECK = "✓"
    CANCEL = "✗"
    WARNING = "⚠"
    INFO = "ℹ"
    QUESTION = "?"
    BACK = "↩"
    
    # Status icons
    ROBOT = "🤖"
    LOADING = "⏳"
    SUCCESS = "✅"
    ERROR = "❌"
    
    # Misc icons
    STAR = "★"
    PIN = "📍"
    MAP = "🗺"
    ROUTES = "🛣"

#color scheme def 
class Colors:
    """
    Define color constants used throughout the application.
    All colors are in RGB format (red, green, blue) with values from 0-255.
    """
    # Basic colors
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


class Layout:
    """
    Define layout constants used for positioning UI elements.
    These measurements ensure consistent spacing and alignments throughout the interface.
    All values are in pixels.
    """
    # Header section measurements
    HEADER_HEIGHT = 60
    
    # Content area begins after header
    CONTENT_Y = HEADER_HEIGHT
    CONTENT_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT
    
    # Navigation panel (left side) width
    NAV_WIDTH = SCREEN_WIDTH * 0.4
    
    # Info panel (right side) begins after navigation panel
    INFO_X = NAV_WIDTH
    INFO_WIDTH = SCREEN_WIDTH - NAV_WIDTH
    
    # Footer section measurements
    FOOTER_HEIGHT = 50
    FOOTER_Y = SCREEN_HEIGHT - FOOTER_HEIGHT
    
    # Standard padding and margin sizes
    PADDING = 10
    MARGIN = 20

def load_fonts():
    """
    Initialize and return a dictionary of pygame font objects at different sizes.
    
    Returns:
        dict: Dictionary of font objects with keys 'small', 'regular', 'large', and 'title'
    """
    fonts = {
        'small': pygame.font.Font(None, 24),
        'regular': pygame.font.Font(None, 32),
        'large': pygame.font.Font(None, 48),
        'title': pygame.font.Font(None, 64)
    }
    return fonts

class UI:
    """
    UI component class responsible for drawing all graphical elements.
    
    This class handles the rendering of all graphical elements in the interface,
    from text and buttons to entire panels. It maintains consistent styling
    and positioning throughout the application.
    """
    
    def __init__(self):
        """Initialize UI with loaded fonts."""
        self.fonts = load_fonts()
        
    def draw_text(self, surface, text, font_size, color, x, y, align="left", max_width=None):
        """
        Draw text on a surface with various alignment and wrapping options.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            text (str): The text to render
            font_size (str): Size key ('small', 'regular', 'large', 'title')
            color (tuple): RGB color tuple
            x (int): X-coordinate for positioning
            y (int): Y-coordinate for positioning
            align (str): Text alignment ('left', 'center', 'right')
            max_width (int, optional): Maximum width for text wrapping
            
        Returns:
            pygame.Rect: Bounding rectangle of rendered text
        """
        font = self.fonts.get(font_size, self.fonts['regular'])

        if max_width:
            words = text.split(' ')
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join([*current_line, word])
                if font.size(test_line)[0] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
            
            text_height = font.size("Tg")[1]
            total_height = len(lines) * (text_height + 2)
            current_y = y

            rects = []
            for line in lines:
                text_surface = font.render(line, True, color)
                text_rect = text_surface.get_rect()

                if align == "center":
                    text_rect.centerx = x
                    text_rect.top = current_y
                elif align == "right":
                    text_rect.right = x
                    text_rect.top = current_y
                else:  # left
                    text_rect.left = x
                    text_rect.top = current_y
                
                surface.blit(text_surface, text_rect)
                rects.append(text_rect)
                current_y += text_height + 2
            
            if rects:
                bounding_rect = rects[0].unionall(rects[1:]) if len(rects) > 1 else rects[0]
                return bounding_rect
            return pygame.Rect(x, y, 0, 0)
        else:
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect()

            if align == "center":
                text_rect.centerx = x
                text_rect.centery = y
            elif align == "right":
                text_rect.right = x
                text_rect.centery = y
            else:
                text_rect.left = x
                text_rect.centery = y
            
            surface.blit(text_surface, text_rect)
            return text_rect      
    
    def draw_button(self, surface, text, x, y, width=200, height=50, 
                   color=Colors.PRIMARY, text_color=Colors.WHITE, 
                   border_radius=10, font_size='regular'):
        """
        Draw a button with text on a surface.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            text (str): Button text
            x (int): X-coordinate for button position
            y (int): Y-coordinate for button position
            width (int): Button width
            height (int): Button height
            color (tuple): RGB color tuple for button
            text_color (tuple): RGB color tuple for text
            border_radius (int): Radius for rounded corners
            font_size (str): Size key for font ('small', 'regular', 'large', 'title')
            
        Returns:
            pygame.Rect: The rectangle area of the button, useful for click detection
        """
        button_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, color, button_rect, border_radius=border_radius)
        
        font = self.fonts.get(font_size, self.fonts['regular'])
        text_surf = font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        surface.blit(text_surf, text_rect)
        
        return button_rect
    
    def draw_panel(self, surface, x, y, width, height, 
                  bg_color=Colors.WHITE, border_color=None, 
                  border_width=0, border_radius=0):
        """
        Draw a panel which can be used for grouping other UI elements.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            x (int): X-coordinate for panel position
            y (int): Y-coordinate for panel position
            width (int): Panel width
            height (int): Panel height
            bg_color (tuple): RGB color tuple for background
            border_color (tuple, optional): RGB color tuple for border
            border_width (int, optional): Width of the border
            border_radius (int, optional): Radius for rounded corners
            
        Returns:
            pygame.Rect: The rectangle area of the panel
        """
        panel_rect = pygame.Rect(x, y, width, height)
        
        pygame.draw.rect(surface, bg_color, panel_rect, border_radius=border_radius)
        
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, panel_rect, 
                           width=border_width, border_radius=border_radius)
            
        return panel_rect
    
    def draw_header(self, surface, title="VRA Interface", voice_assistant_active=False):
        """
        Draw the header section at the top of the interface.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            title (str): Title text to display in the header
            voice_assistant_active (bool): Whether the voice assistant is active
            
        Returns:
            tuple: The rectangle area of the header and the LIVE/STOP button rect
        """
        # header background
        header_rect = self.draw_panel(
            surface, 
            0, 0, 
            SCREEN_WIDTH, Layout.HEADER_HEIGHT,
            bg_color=Colors.PRIMARY
        )
        
        # # Add robot icon before title
        # robot_icon_font = self.fonts['large']
        # robot_icon_surf = robot_icon_font.render(Icons.ROBOT, True, Colors.WHITE)
        # robot_icon_rect = robot_icon_surf.get_rect(
        #     centery=Layout.HEADER_HEIGHT // 2,
        #     right=SCREEN_WIDTH // 2 - 10  # Position to the left of the title center
        # )
        # surface.blit(robot_icon_surf, robot_icon_rect)
        
        # title text
        self.draw_text(
            surface, 
            title, 
            'large', 
            Colors.WHITE,
            SCREEN_WIDTH // 2, 
            Layout.HEADER_HEIGHT // 2,
            align="center"
        )
        
        # Add LIVE/STOP button to the right of the title
        button_width = 100
        button_height = 40
        button_x = SCREEN_WIDTH - button_width - Layout.MARGIN
        button_y = (Layout.HEADER_HEIGHT - button_height) // 2
        
        if voice_assistant_active:
            # Show STOP button when voice assistant is active
            button = self.draw_button(
                surface,
                "STOP",
                button_x,
                button_y,
                width=button_width,
                height=button_height,
                color=Colors.ERROR,  
                font_size='regular'
            )
        else:
            # Show LIVE button when voice assistant is inactive
            button = self.draw_button(
                surface,
                "LIVE",
                button_x,
                button_y,
                width=button_width,
                height=button_height,
                color=Colors.SUCCESS, 
                font_size='regular'
            )
        
        return header_rect, button
    
    def draw_footer(self, surface, status_text="Ready"):
        """
        Draw the footer section at the bottom of the interface.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            status_text (str): Status text to display in the footer
            
        Returns:
            pygame.Rect: The rectangle area of the footer
        """
        #footer background
        footer_rect = self.draw_panel(
            surface,
            0, Layout.FOOTER_Y,
            SCREEN_WIDTH, Layout.FOOTER_HEIGHT,
            bg_color=Colors.LIGHT_GRAY
        )
        
        #status text
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
    
    def draw_navigation_panel(self, surface, navigating_to=None):
        """
        Draw the navigation panel with destination options.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            navigating_to (str, optional): Current navigation target to display status
            
        Returns:
            dict: Dictionary containing button areas for navigation
        """
        nav_panel = self.draw_panel(
            surface,
            0, Layout.CONTENT_Y,
            Layout.NAV_WIDTH, Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT,
            bg_color=Colors.LIGHT_GRAY,
            border_color=Colors.GRAY,
            border_width=1
        )

        buttons = {'panel': nav_panel} # Initialize buttons dict

        if navigating_to:
            # Display navigation status message
            message = f"Navigating to {navigating_to}..."
            text_rect = self.draw_text(
                surface,
                message,
                'regular', # Use regular font size
                Colors.PRIMARY_DARK,
                Layout.NAV_WIDTH // 2,
                Layout.CONTENT_Y + (Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT) // 3, # Position message higher
                align="center",
                max_width=Layout.NAV_WIDTH - Layout.MARGIN * 2 # Allow wrapping
            )

            # Add Cancel Button below the message
            cancel_button_width = 150
            cancel_button_height = 50
            cancel_button_x = (Layout.NAV_WIDTH - cancel_button_width) // 2
            # Position below the text, add some padding
            cancel_button_y = text_rect.bottom + 40 

            cancel_button = self.draw_button(
                surface,
                "Cancel",
                cancel_button_x,
                cancel_button_y,
                width=cancel_button_width,
                height=cancel_button_height,
                color=Colors.ERROR, 
                font_size='regular'
            )
            buttons['cancel_button'] = cancel_button 
        else:
            # Display building selection options
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
            
            #building buttons
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
                color=Colors.ST_BUILDING,
                font_size="small"
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
                color=Colors.CU_BUILDING,
                font_size="small"
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
                color=Colors.GE_BUILDING,
                font_size="small"
            )
            
            # Return panel and button rects
            buttons['st_button'] = st_button
            buttons['cu_button'] = cu_button
            buttons['ge_button'] = ge_button
            
        return buttons
    
    def draw_info_panel(self, surface, faq_manager, scroll_offset=0):
        """
        Draw the information panel displaying FAQs.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            faq_manager (FAQManager): Instance managing FAQ data
            scroll_offset (int, optional): Current scroll position for FAQs
            
        Returns:
            tuple: Contains the info panel rect, list of question buttons, and scroll button rects
        """
        # info panel bg
        info_panel = self.draw_panel(
            surface,
            Layout.INFO_X, Layout.CONTENT_Y,
            Layout.INFO_WIDTH, Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT,
            bg_color=Colors.WHITE,
            border_color=Colors.GRAY,
            border_width=1
        )
        
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
        
        content_y = title_y + 40 # Adjusted for title
        content_height = Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT - (title_y - Layout.CONTENT_Y) - Layout.MARGIN * 2
        available_height = content_height - 20 # Padding top/bottom within content area
        
        question_buttons = []
        scroll_up_button = None
        scroll_down_button = None

        if faq_manager.selected_question:
            # Draw question
            question_rect = self.draw_panel(
                surface,
                Layout.INFO_X + Layout.MARGIN,
                content_y,
                Layout.INFO_WIDTH - (Layout.MARGIN * 2),
                60, # Fixed height for selected question display
                bg_color=Colors.PRIMARY_LIGHT,
                border_radius=5
            )
            
            self.draw_text(
                surface,
                faq_manager.selected_question['data']['question'],
                'regular',
                Colors.WHITE,
                Layout.INFO_X + Layout.MARGIN + 10,
                content_y + 15, # Adjusted y for text inside panel
                max_width=Layout.INFO_WIDTH - (Layout.MARGIN * 2) - 20
            )
            
            # Draw back button
            back_button = self.draw_button(
                surface,
                "Back to FAQs",
                Layout.INFO_X + Layout.MARGIN,
                content_y + 70, # Position below question panel
                width=150,
                height=40,
                color=Colors.SECONDARY
            )
            question_buttons.append(('back', back_button))
            
            # Draw answer
            answer_y = content_y + 130 # Position below back button
            answer_panel_height = Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT - (answer_y - Layout.CONTENT_Y) - Layout.MARGIN
            answer_panel = self.draw_panel(
                surface,
                Layout.INFO_X + Layout.MARGIN,
                answer_y,
                Layout.INFO_WIDTH - (Layout.MARGIN * 2),
                answer_panel_height,
                bg_color=Colors.LIGHT_GRAY,
                border_radius=5
            )
            
            self.draw_text(
                surface,
                faq_manager.selected_question['data']['answer'],
                'regular',
                Colors.BLACK,
                Layout.INFO_X + Layout.MARGIN + 10,
                answer_y + 10,
                max_width=Layout.INFO_WIDTH - (Layout.MARGIN * 2) - 20
            )
            
        else:
            all_questions = faq_manager.get_all_questions()
            q_height = 50
            q_spacing = 10
            q_total_height = q_height + q_spacing
            
            # Calculate how many questions fit
            visible_count = available_height // q_total_height
            
            scroll_button_width = 40
            scroll_button_x = Layout.INFO_X + Layout.INFO_WIDTH - Layout.MARGIN - scroll_button_width
            
            start_index = scroll_offset
            end_index = min(scroll_offset + visible_count, len(all_questions))
            
            current_y = content_y + 10 
            # Start drawing questions 
            for i in range(start_index, end_index):
                q = all_questions[i]
                q_y = current_y + (i - start_index) * q_total_height
                
                # Draw question button panel
                q_button = self.draw_panel(
                    surface,
                    Layout.INFO_X + Layout.MARGIN,
                    q_y,
                    Layout.INFO_WIDTH - (Layout.MARGIN * 2) - (scroll_button_width + 5 if len(all_questions) > visible_count else 0), # Make space for scroll buttons
                    q_height,
                    bg_color=Colors.PRIMARY_LIGHT,
                    border_radius=5
                )
                # question text
                self.draw_text(
                    surface,
                    q['data']['question'],
                    'small',
                    Colors.WHITE,
                    Layout.INFO_X + Layout.MARGIN + 10,
                    q_y + (q_height // 2) - 8, # Center text vertically approx
                    max_width=Layout.INFO_WIDTH - (Layout.MARGIN * 3) - scroll_button_width - 10 # Adjust max width
                )
                
                question_buttons.append((q, q_button))

            # Draw scroll buttons if needed
            if len(all_questions) > visible_count:
                scroll_up_y = content_y + 10
                scroll_down_y = content_y + available_height - q_height
                
                # Define arrow button rects for click detection
                scroll_up_rect = pygame.Rect(scroll_button_x, scroll_up_y, scroll_button_width, q_height)
                scroll_down_rect = pygame.Rect(scroll_button_x, scroll_down_y, scroll_button_width, q_height)

                # Up Arrow Button
                up_color = Colors.SECONDARY if scroll_offset > 0 else Colors.GRAY
                up_arrow_points = [
                    (scroll_up_rect.centerx, scroll_up_rect.top + scroll_up_rect.height * 0.2),  # Top point
                    (scroll_up_rect.left + scroll_up_rect.width * 0.2, scroll_up_rect.top + scroll_up_rect.height * 0.7), # Bottom-left
                    (scroll_up_rect.right - scroll_up_rect.width * 0.2, scroll_up_rect.top + scroll_up_rect.height * 0.7) # Bottom-right
                ]
                pygame.draw.polygon(surface, up_color, up_arrow_points)
                scroll_up_button = scroll_up_rect # Use the rect for click detection
                
                # Down Arrow Button
                down_color = Colors.SECONDARY if end_index < len(all_questions) else Colors.GRAY
                down_arrow_points = [
                    (scroll_down_rect.centerx, scroll_down_rect.top + scroll_down_rect.height * 0.8), # Bottom point
                    (scroll_down_rect.left + scroll_down_rect.width * 0.2, scroll_down_rect.top + scroll_down_rect.height * 0.3), # Top-left
                    (scroll_down_rect.right - scroll_down_rect.width * 0.2, scroll_down_rect.top + scroll_down_rect.height * 0.3) # Top-right
                ]
                pygame.draw.polygon(surface, down_color, down_arrow_points)
                scroll_down_button = scroll_down_rect # Use the rect for click detection

        return info_panel, question_buttons, scroll_up_button, scroll_down_button
    
    def draw_message_panel(self, surface, text, font_size='regular', bg_color=Colors.INFO):
        """
        Draw a message panel for displaying temporary messages.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            text (str): Message text
            font_size (str): Size key for font ('small', 'regular', 'large', 'title')
            bg_color (tuple): RGB color tuple for background
            
        Returns:
            pygame.Rect: The rectangle area of the message panel
        """
        message_panel = self.draw_panel(
            surface,
            0, Layout.CONTENT_Y,
            Layout.NAV_WIDTH, Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT,
            bg_color=bg_color,
            border_color=Colors.GRAY,
            border_width=1
        )
        
        # Center the text in the panel
        text_rect = self.draw_text(
            surface,
            text,
            font_size,
            Colors.WHITE,  # Use white text for good contrast on colored backgrounds
            Layout.NAV_WIDTH // 2,
            Layout.CONTENT_Y + (Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT) // 2,
            align="center",
            max_width=Layout.NAV_WIDTH - (Layout.MARGIN * 2)  # Allow wrapping
        )
        
        return message_panel
    
    def draw_warning(self, surface, message="Warning: Obstacle detected!"):
        """
        Draw a warning overlay with an optional message.
        
        Args:
            surface (pygame.Surface): Surface to draw on
            message (str): Warning message text
            
        Returns:
            pygame.Rect: The rectangle area of the warning panel
        """
        # Create glassy transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # semi-transparent black
        surface.blit(overlay, (0, 0))
        
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
        
        icon_radius = 25
        icon_x = warning_x + 50
        icon_y = warning_y + (warning_height // 2)
        pygame.draw.circle(surface, Colors.WHITE, (icon_x, icon_y), icon_radius)
        pygame.draw.circle(surface, Colors.ERROR, (icon_x, icon_y), icon_radius - 5)
        
        #exclamation mark
        font = self.fonts['large']
        text_surf = font.render("!", True, Colors.WHITE)
        text_rect = text_surf.get_rect(center=(icon_x, icon_y))
        surface.blit(text_surf, text_rect)
        
        #warning text
        self.draw_text(
            surface,
            message,
            'large',
            Colors.WHITE,
            warning_x + icon_radius * 2 + 60, # Increased space after icon
            warning_y + (warning_height // 2),
            align="left",
            max_width=warning_width - (icon_radius * 2 + 70) # Max width considering icon and padding
        )
        
        
        return warning_panel

class RobotInterface:
    """
    Main interface controller for the VRA Robot Assistant.
    
    This class is responsible for:
    - Managing the overall application state
    - Handling user input (keyboard, mouse)
    - Updating UI elements
    - Coordinating between different components
    
    It serves as the central hub connecting the UI rendering with 
    application logic and user interactions.
    """
    
    def __init__(self):
        """Initialize the robot interface with all necessary components."""
        self.ui = UI()
        self.running = True
        self.show_warning = False
        self.warning_message = ""
        self.warning_time = 0
        self.warning_duration = 3  # Duration in seconds to display warnings
        self.clock = clock
        
        # Initialize FAQ manager
        self.faq_manager = FAQManager()
        self.faq_scroll_offset = 0
        self.faq_visible_count = 6 # Initial estimate, will be recalculated in draw
        
        # UI elements that need click detection
        self.nav_buttons = {}
        self.faq_buttons = []
        self.faq_scroll_up_button = None
        self.faq_scroll_down_button = None
        self.live_button = None  # Store the LIVE button rect for click detection
        
        # Status message
        self.status_message = "Ready for navigation"
        self.navigating_to = None # Track current navigation target
        
        # Custom message panel settings
        self.is_showing_message = False  # Renamed from show_custom_message to avoid name conflict
        self.message_text = "Custom Message"
        self.message_font_size = "large"
        self.message_bg_color = Colors.INFO
        
        # LiveKit URL
        self.livekit_url = "https://agents-playground.livekit.io/#cam=1&mic=1&video=1&audio=1&chat=1&theme_color=green"
        self.voice_assistant_running = False
    
    def handle_events(self):
        """
        Process all pygame events including keyboard and mouse inputs.
        
        This method handles:
        - Quit events
        - Keyboard navigation (arrows, escape)
        - Mouse clicks on buttons, panels, and FAQ items
        - Navigation selections and cancellations
        """
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                elif event.key == K_UP and not self.navigating_to: # Only allow selection if not navigating
                    self.display_building_selection("ST Building")
                elif event.key == K_RIGHT and not self.navigating_to:
                    self.display_building_selection("CU Building")
                elif event.key == K_LEFT and not self.navigating_to:
                    self.display_building_selection("GE Building")
                elif event.key == K_w:
                    self.show_warning_message("Obstacle detected! Please move.")
                elif event.key == K_f: # Press 'f' to go back to building selection
                    self.navigating_to = None
                    self.status_message = "Ready for navigation"
                # Keyboard triggers for message panel removed (m, 1, 2, 3 keys)
            
            elif event.type == MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                
                # Check if LIVE button was clicked
                if self.live_button and self.live_button.collidepoint(pos):
                    self.activate_live_features()
                    continue  # Skip other button checks
                
                # Handle navigation panel button clicks
                if self.nav_buttons: 
                    if self.navigating_to:
                        if self.nav_buttons.get('cancel_button') and self.nav_buttons['cancel_button'].collidepoint(pos):
                            print("this button was clicked")
                            self.cancel_navigation()
                             
                    else:
                        if self.nav_buttons.get('st_button') and self.nav_buttons['st_button'].collidepoint(pos):
                            self.display_building_selection("ST Building")
                        elif self.nav_buttons.get('cu_button') and self.nav_buttons['cu_button'].collidepoint(pos):
                            self.display_building_selection("CU Building")
                        elif self.nav_buttons.get('ge_button') and self.nav_buttons['ge_button'].collidepoint(pos):
                            self.display_building_selection("GE Building")
                
                
                # Check FAQ buttons (these are always in the right panel)
                if not self.faq_manager.selected_question:
                    # Check scroll buttons first
                    scrolled = False
                    if self.faq_scroll_up_button and self.faq_scroll_up_button.collidepoint(pos):
                        if self.faq_scroll_offset > 0:
                            self.faq_scroll_offset -= 1
                            scrolled = True
                    elif self.faq_scroll_down_button and self.faq_scroll_down_button.collidepoint(pos):
                        total_questions = len(self.faq_manager.get_all_questions())
                        # Use stored/recalculated visible count
                        if self.faq_scroll_offset < total_questions - self.faq_visible_count:
                            self.faq_scroll_offset += 1
                            scrolled = True
                    
                    # If not scrolled, check question buttons
                    if not scrolled:
                        for q_data, q_rect in self.faq_buttons:
                            if q_rect.collidepoint(pos):
                                self.faq_manager.selected_question = q_data
                                self.status_message = "Viewing FAQ" # Update status
                                break 
                else:
                    # Check only the 'back' button when a question is selected
                    for q_data, q_rect in self.faq_buttons:
                        if q_rect.collidepoint(pos):
                            if q_data == 'back':
                                self.faq_manager.selected_question = None
                                self.status_message = "Ready for navigation" 

    
    def display_building_selection(self, building):
        """
        Set the current navigation target to a specific building.
        
        Args:
            building (str): Name of the building to navigate to
        """
        print(f"Selected: {building}")
        self.navigating_to = building 
        self.status_message = f"Navigating to {building}..." 

        # Reset FAQ panel state when navigation begins
        self.faq_manager.selected_question = None 
        self.faq_scroll_offset = 0
    
    def cancel_navigation(self):
        """Cancel the current navigation and return to selection screen."""
        print("Navigation cancelled.")
        self.navigating_to = None
        self.status_message = "Navigation cancelled. Ready."

    def show_custom_message(self, text, font_size="large", bg_color=Colors.INFO):
        """
        Display a custom message in the navigation panel.
        
        Args:
            text (str): The message text to display
            font_size (str): Size key for font ('small', 'regular', 'large', 'title')
            bg_color (tuple): RGB color tuple for background
            
        Returns:
            pygame.Rect: The rectangle area of the message panel
        """
        self.is_showing_message = True  
        self.message_text = text
        self.message_font_size = font_size
        self.message_bg_color = bg_color
        self.status_message = "Displaying custom message"
        
        # Temporarily hide navigation
        self.navigating_to = None
        
    def show_warning_message(self, message):
        """
        Show a temporary warning message overlay.
        
        Args:
            message (str): Warning text to display
        """
        self.show_warning = True
        self.warning_message = message
        self.warning_time = time.time()
    
    def update(self):
        """
        Update interface state, such as checking warning timeouts and scroll limits.
        Called once per frame before drawing.
        """
        # Check if warning should be dismissed
        if self.show_warning and time.time() - self.warning_time > self.warning_duration:
            self.show_warning = False

        # Calculate FAQ panel display parameters
        total_questions = len(self.faq_manager.get_all_questions())
        title_y = Layout.CONTENT_Y + Layout.MARGIN
        content_height = Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT - (title_y - Layout.CONTENT_Y) - Layout.MARGIN * 2
        available_height = content_height - 20
        q_total_height = 50 + 10  # Question height + spacing
        self.faq_visible_count = max(1, available_height // q_total_height)
        
        # Make sure scroll offset is within valid range
        max_offset = max(0, total_questions - self.faq_visible_count)
        self.faq_scroll_offset = max(0, min(self.faq_scroll_offset, max_offset))

    def draw(self):
        """
        Draw the entire interface to the screen.
        Called once per frame after updating.
        """
        # Fill background
        screen.fill(Colors.BLACK)
        
        # Draw header and get the LIVE/STOP button rect
        # Pass the voice assistant status to draw_header
        _, self.live_button = self.ui.draw_header(screen, "VRA Mobile Robot:", self.voice_assistant_running)
        
        # Draw either the message panel or navigation panel
        if self.is_showing_message:  
            self.ui.draw_message_panel(
                screen, 
                self.message_text,
                self.message_font_size,
                self.message_bg_color
            )
        else:
            self.nav_buttons = self.ui.draw_navigation_panel(screen, self.navigating_to) 
        
        # Draw the FAQ panel
        _, self.faq_buttons, self.faq_scroll_up_button, self.faq_scroll_down_button = self.ui.draw_info_panel(
            screen, self.faq_manager, self.faq_scroll_offset
        )
        
        # Draw footer with status message
        self.ui.draw_footer(screen, self.status_message)
        
        # Draw warning overlay if active
        if self.show_warning:
            self.ui.draw_warning(screen, self.warning_message)

        # Update display
        pygame.display.flip()
    
    def clear_message(self):
        """Reset message panel state and hide the custom message."""
        self.is_showing_message = False 
        self.message_text = "Custom Message"
        self.message_font_size = "large"
        self.message_bg_color = Colors.INFO
        self.status_message = "Ready for navigation" 

    def activate_live_features(self):
        """
        Toggle the LiveKit interface and voice assistant when the LIVE/STOP button is clicked.
        
        If voice assistant is not running:
        1. Opens the LiveKit website in the default browser
        2. Starts the voice assistant in the background
        
        If voice assistant is already running:
        1. Stops the voice assistant process
        """
        # If voice assistant is already running, stop it
        if self.voice_assistant_running:
            try:
                # Update status message to indicate deactivation
                self.status_message = "Stopping voice assistant..."
                
                # In a real implementation, you would need to terminate the voice assistant process
                # This is platform-specific and depends on how you started the process
                import sys
                
                if sys.platform == 'darwin':  # macOS
                    # For demonstration, we're just setting the flag to false
                    # In a real implementation, you would use subprocess.Popen.terminate() 
                    # or send a signal to the process
                    subprocess.run(["pkill", "-f", "voice_assistant"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
                elif sys.platform == 'win32':  # Windows
                    # Windows equivalent would use taskkill
                    subprocess.run(["taskkill", "/f", "/im", "voice_assistant"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
                else:  # Linux
                    subprocess.run(["pkill", "-f", "voice_assistant"], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
                    
                self.voice_assistant_running = False
                print("Voice assistant stopped")
                self.status_message = "Voice assistant stopped"
                
            except Exception as e:
                print(f"Error stopping voice assistant: {str(e)}")
                self.show_warning_message("Failed to stop voice assistant")
                
        # If voice assistant is not running, start it and open LiveKit
        else:
            # Update status message to indicate activation
            self.status_message = "Activating LiveKit..."
            
            # Open the LiveKit website in the default browser
            try:
                webbrowser.open(self.livekit_url)
                print(f"Opening LiveKit website: {self.livekit_url}")
            except Exception as e:
                print(f"Error opening LiveKit website: {str(e)}")
                self.show_warning_message("Failed to open LiveKit")
            
            try:
                # Use a platform-safe way to run the voice assistant
                # Use sys.executable to ensure we use the correct Python interpreter
                import sys
                
                # Create a detached process that won't display terminal errors
                if sys.platform == 'darwin':  # macOS
                    # For macOS, use subprocess with appropriate configuration
                    subprocess.Popen(
                        ["python3", "-c", "print('Voice assistant started')"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                elif sys.platform == 'win32':  # Windows
                    # For Windows, use DETACHED_PROCESS to avoid console window
                    subprocess.Popen(
                        ["python", "-c", "print('Voice assistant started')"],
                        creationflags=subprocess.DETACHED_PROCESS,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:  # Linux and other Unix-like systems
                    # Standard approach for Linux
                    subprocess.Popen(
                        ["python3", "-c", "print('Voice assistant started')"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                
                self.voice_assistant_running = True
                print("Voice assistant started in the background")
                self.status_message = "LiveKit and voice assistant activated"
                
            except Exception as e:
                print(f"Error starting voice assistant: {str(e)}")
                # Don't show warning to user, just log it
                self.status_message = "LiveKit activated (voice assistant failed)"

    def run(self):
        """
        Main application loop that runs the user interface.
        
        This method:
        1. Processes user input events
        2. Updates the interface state
        3. Redraws the interface
        4. Maintains the frame rate
        
        The loop continues until the user exits the application.
        """
        try:
            while self.running:
                # Process user input (mouse, keyboard)
                self.handle_events()
                
                # Update interface state
                self.update()
                
                # Render the interface
                self.draw()
                
                # Control frame rate
                self.clock.tick(FPS)
                
        except KeyboardInterrupt:
            print("\nProgram terminated by user.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        finally:
            # Clean up hardware resources
            pygame.quit()
            sys.exit(0)

# Create a global instance that can be imported by other modules
robot_interface = None

def initialize_interface():
    """
    Initialize the robot interface if it hasn't been initialized yet.
    Should be called once at the beginning of the program.
    
    This function ensures there's only a single instance of RobotInterface
    used throughout the application, implementing a singleton pattern.
    
    Returns:
        RobotInterface: The global robot_interface instance
    """
    global robot_interface
    if robot_interface is None:
        robot_interface = RobotInterface()
    return robot_interface

def get_interface():
    """
    Get the global robot_interface instance.
    Initialize it if it doesn't exist yet.
    
    This function provides access to the singleton RobotInterface
    instance from any module that imports it.
    
    Returns:
        RobotInterface: The global robot_interface instance
    """
    global robot_interface
    if robot_interface is None:
        return initialize_interface()
    return robot_interface

def display_message(text, font_size="large", bg_color=None):
    """
    Display a custom message in the navigation panel.
    This function can be called from any module to show a message.
    
    This is the primary external API for showing messages in the GUI
    from other modules like core.py or husky_gui_integration.py.
    
    Args:
        text (str): The message text to display
        font_size (str): Size of the font ('small', 'regular', 'large', or 'title')
        bg_color (tuple): Background color of the message panel (uses Colors.INFO by default)
    """
    interface = get_interface()
    
    # Use appropriate color based on message type if not specified
    if bg_color is None:
        bg_color = Colors.INFO
    
    # Call the show_custom_message method on the interface instance
    interface.show_custom_message(text, font_size, bg_color)
    
    # Force a redraw immediately to show the message
    interface.draw()
    pygame.display.flip()
    
def clear_message():
    """
    Clear the custom message from the navigation panel.
    This function can be called from any module to hide the message.
    
    This complements the display_message function, allowing external
    modules to remove a displayed message when no longer needed.
    """
    interface = get_interface()
    interface.is_showing_message = False
    interface.status_message = "Ready for navigation"
    
    # Force a redraw immediately
    interface.draw()
    pygame.display.flip()

# Main entry point
if __name__ == "__main__":
    interface = initialize_interface()
    interface.run()
