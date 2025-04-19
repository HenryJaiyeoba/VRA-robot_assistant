import pygame
import sys
import os
import time
from pygame.locals import *
import RPi.GPIO as GPIO
from faq_manager import FAQManager


pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('VRA Interface')


clock = pygame.time.Clock()
FPS = 30

#color scheme def 
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


class Layout:
    HEADER_HEIGHT = 60
    
    CONTENT_Y = HEADER_HEIGHT
    CONTENT_HEIGHT = SCREEN_HEIGHT - HEADER_HEIGHT
    
    NAV_WIDTH = SCREEN_WIDTH * 0.4
    
    INFO_X = NAV_WIDTH
    INFO_WIDTH = SCREEN_WIDTH - NAV_WIDTH
    FOOTER_HEIGHT = 50
    FOOTER_Y = SCREEN_HEIGHT - FOOTER_HEIGHT
    PADDING = 10
    MARGIN = 20

def load_fonts():
    fonts = {
        'small': pygame.font.Font(None, 24),
        'regular': pygame.font.Font(None, 32),
        'large': pygame.font.Font(None, 48),
        'title': pygame.font.Font(None, 64)
    }
    return fonts

class UI:
    def __init__(self):
        self.fonts = load_fonts()
        
    def draw_text(self, surface, text, font_size, color, x, y, align="left", max_width=None):
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
        panel_rect = pygame.Rect(x, y, width, height)
        
        pygame.draw.rect(surface, bg_color, panel_rect, border_radius=border_radius)
        
        if border_color and border_width > 0:
            pygame.draw.rect(surface, border_color, panel_rect, 
                           width=border_width, border_radius=border_radius)
            
        return panel_rect
    
    def draw_header(self, surface, title="VRA Interface"):
        # header background
        header_rect = self.draw_panel(
            surface, 
            0, 0, 
            SCREEN_WIDTH, Layout.HEADER_HEIGHT,
            bg_color=Colors.PRIMARY
        )
        
        #title text
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
    
    def draw_navigation_panel(self, surface):
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
    
    def draw_info_panel(self, surface, faq_manager, scroll_offset=0):
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
            # ... existing code for displaying selected question ...
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
    
    def draw_warning(self, surface, message="Warning: Obstacle detected!"):
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
    def __init__(self):
        self.ui = UI()
        self.running = True
        self.show_warning = False
        self.warning_message = ""
        self.warning_time = 0
        self.warning_duration = 3  # seconds
        
        # Initialize FAQ manager
        self.faq_manager = FAQManager()
        self.faq_scroll_offset = 0
        self.faq_visible_count = 6 # Initial estimate, will be recalculated in draw
        
        # UI elements that need click detection
        self.nav_buttons = {}
        self.faq_buttons = []
        self.faq_scroll_up_button = None
        self.faq_scroll_down_button = None
        
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
                if not self.faq_manager.selected_question:
                    # Check scroll buttons first
                    scrolled = False
                    if self.faq_scroll_up_button and self.faq_scroll_up_button.collidepoint(pos):
                        if self.faq_scroll_offset > 0:
                            self.faq_scroll_offset -= 1
                            scrolled = True
                    elif self.faq_scroll_down_button and self.faq_scroll_down_button.collidepoint(pos):
                        # Need to know total questions and visible count to check bounds
                        total_questions = len(self.faq_manager.get_all_questions())
                        # Recalculate visible count based on current layout (could be stored)
                        title_y = Layout.CONTENT_Y + Layout.MARGIN
                        content_height = Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT - (title_y - Layout.CONTENT_Y) - Layout.MARGIN * 2
                        available_height = content_height - 20
                        q_total_height = 50 + 10 # height + spacing
                        self.faq_visible_count = max(1, available_height // q_total_height) # Ensure at least 1

                        if self.faq_scroll_offset < total_questions - self.faq_visible_count:
                            self.faq_scroll_offset += 1
                            scrolled = True
                    
                    # If not scrolled, check question buttons
                    if not scrolled:
                        for q_data, q_rect in self.faq_buttons:
                            if q_rect.collidepoint(pos):
                                self.faq_manager.selected_question = q_data
                                break # Found clicked question
                else:
                    # Check only the 'back' button when a question is selected
                     for q_data, q_rect in self.faq_buttons:
                        if q_rect.collidepoint(pos):
                            if q_data == 'back':
                                self.faq_manager.selected_question = None
    
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

        total_questions = len(self.faq_manager.get_all_questions())
        title_y = Layout.CONTENT_Y + Layout.MARGIN
        content_height = Layout.CONTENT_HEIGHT - Layout.FOOTER_HEIGHT - (title_y - Layout.CONTENT_Y) - Layout.MARGIN * 2
        available_height = content_height - 20
        q_total_height = 50 + 10 # height + spacing
        self.faq_visible_count = max(1, available_height // q_total_height)
        
        max_offset = max(0, total_questions - self.faq_visible_count)
        self.faq_scroll_offset = max(0, min(self.faq_scroll_offset, max_offset))
    def draw(self):
        """Draw the interface"""
        # Fill background
        screen.fill(Colors.BLACK)
        
        # Draw header
        self.ui.draw_header(screen, "VRA Mobile Robot:")
        
        # Draw navigation panel and store button references
        self.nav_buttons = self.ui.draw_navigation_panel(screen)
        
        # Draw info panel with FAQ data and store FAQ button references
        _, self.faq_buttons, self.faq_scroll_up_button, self.faq_scroll_down_button = self.ui.draw_info_panel(
            screen, self.faq_manager, self.faq_scroll_offset
        )
        
        # Draw footer
        self.ui.draw_footer(screen, self.status_message)
        
        # Draw warning if active
        if self.show_warning:
            self.ui.draw_warning(screen, self.warning_message)
        
        # Update the display
        pygame.display.flip()
    
    def run(self):            
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            clock.tick(FPS)
        
        # Clean up
            GPIO.cleanup()
        pygame.quit()
        sys.exit()

# Run the application if this is the main script
if __name__ == "__main__":
    try:
        app = RobotInterface()
        app.run()
    except KeyboardInterrupt:
        GPIO.cleanup()
        pygame.quit()
        print("\nApplication terminated by user.")
        sys.exit(0)
