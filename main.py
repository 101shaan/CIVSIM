#!/usr/bin/env python3
"""
civilization simulator - main entry point
simulates the rise and fall of civilizations across time
"""
import sys
import os
import pygame
import pygame.freetype
from src.world import World
from src.simulation import Simulation
from src.visualization import Visualizer
from src.ui.renderer import Renderer
from src.ui.controls import Controls, Button

def ensure_directories():
    """make sure our folders exist"""
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/reports", exist_ok=True)
    os.makedirs("data/charts", exist_ok=True)

class MainMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.freetype.SysFont("Arial", 36)
        self.font = pygame.freetype.SysFont("Arial", 22)
        self.font_small = pygame.freetype.SysFont("Arial", 16)
        
        width, height = screen.get_size()
        button_width = 300
        button_height = 50
        button_x = (width - button_width) // 2
        
        # Load background image
        try:
            # First try the direct path, then try with CIVSIM/ prefix
            bg_path = "assets/backgrounds/main_menu_bg.png"
            if not os.path.exists(bg_path):
                bg_path = os.path.join("CIVSIM", "assets/backgrounds/main_menu_bg.png")
            
            self.background = pygame.image.load(bg_path)
            # Scale to match screen size if needed
            if self.background.get_size() != (width, height):
                self.background = pygame.transform.scale(self.background, (width, height))
        except:
            # Fallback - create a simple gradient background if image not found
            self.background = pygame.Surface((width, height))
            for y in range(height):
                r = int(10 + (y / height) * 15)
                g = int(20 + (y / height) * 20)
                b = int(50 + (y / height) * 30)
                pygame.draw.line(self.background, (r, g, b), (0, y), (width, y))
        
        # Create custom menu buttons for the main menu
        # These are different from the regular Button class used in Controls
        class MenuButton:
            def __init__(self, rect, text, action=None):
                self.rect = pygame.Rect(rect)
                self.text = text
                self.action = action
                self.is_hovered = False
                self.font = pygame.freetype.SysFont("Arial", 20)
                
                # Button animation state
                self.animation_state = 0  # 0-100 for glow effect
                self.animation_direction = 1  # 1 = increasing, -1 = decreasing
            
            def draw(self, screen):
                # Create a surface with per-pixel alpha
                button_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                
                # Calculate base color and glow color based on hover state
                base_alpha = 180  # Semi-transparent
                if self.is_hovered:
                    # Update animation state
                    self.animation_state += self.animation_direction * 5
                    if self.animation_state > 100:
                        self.animation_state = 100
                        self.animation_direction = -1
                    elif self.animation_state < 0:
                        self.animation_state = 0
                        self.animation_direction = 1
                        
                    # Enhanced glow when hovered
                    glow_strength = self.animation_state / 100
                    base_color = (40, 80, 120, base_alpha)
                    glow_color = (60, 120, 180, base_alpha)
                    r = int(base_color[0] + (glow_color[0] - base_color[0]) * glow_strength)
                    g = int(base_color[1] + (glow_color[1] - base_color[1]) * glow_strength)
                    b = int(base_color[2] + (glow_color[2] - base_color[2]) * glow_strength)
                    color = (r, g, b, base_alpha)
                else:
                    # Reset animation when not hovered
                    self.animation_state = 0
                    color = (30, 60, 100, base_alpha)
                
                # Draw button background with rounded corners
                pygame.draw.rect(button_surface, color, (0, 0, self.rect.width, self.rect.height), 
                                border_radius=10)
                
                # Add subtle gradient effect
                for y in range(0, self.rect.height//2):
                    highlight_alpha = 40 - y
                    if highlight_alpha > 0:
                        highlight_color = (255, 255, 255, highlight_alpha)
                        pygame.draw.rect(button_surface, highlight_color, 
                                        (2, 2 + y, self.rect.width - 4, 1), 
                                        border_radius=8)
                
                # Add button border with subtle glow
                if self.is_hovered:
                    # Glowing border when hovered
                    border_color = (100, 180, 255, 200)
                    pygame.draw.rect(button_surface, border_color, 
                                    (0, 0, self.rect.width, self.rect.height), 
                                    2, border_radius=10)
                else:
                    # Subtle border when not hovered
                    border_color = (100, 140, 200, 150)
                    pygame.draw.rect(button_surface, border_color, 
                                    (0, 0, self.rect.width, self.rect.height), 
                                    1, border_radius=10)
                
                # Draw text with shadow for better visibility
                text_color = (240, 240, 255)
                shadow_color = (0, 0, 0, 100)
                
                # Draw text shadow
                text_surf, text_rect = self.font.render(self.text, shadow_color)
                text_rect.center = (self.rect.width // 2 + 1, self.rect.height // 2 + 1)
                button_surface.blit(text_surf, text_rect)
                
                # Draw main text
                text_surf, text_rect = self.font.render(self.text, text_color)
                text_rect.center = (self.rect.width // 2, self.rect.height // 2)
                button_surface.blit(text_surf, text_rect)
                
                # Draw the button surface to the screen
                screen.blit(button_surface, self.rect)
            
            def is_over(self, pos):
                return self.rect.collidepoint(pos)
        
        # Store custom button class for use in other methods
        self.MenuButton = MenuButton
        
        # Create menu buttons using the custom class
        self.buttons = [
            MenuButton(
                (button_x, height // 2 - 30, button_width, button_height),
                "New Simulation",
                self._new_simulation
            ),
            MenuButton(
                (button_x, height // 2 + 40, button_width, button_height),
                "Load Simulation",
                self._load_simulation
            ),
            MenuButton(
                (button_x, height // 2 + 110, button_width, button_height),
                "Exit",
                self._exit_game
            )
        ]
        
        self.result = None
        self.input_active = False
        self.input_purpose = None  # 'new' or 'load'
        self.input_text = ""
        self.input_rect = pygame.Rect(width // 2 - 200, height // 2 + 180, 400, 50)
        self.input_error = None
        self.input_warning = None
        
    def draw(self):
        # Draw background instead of clearing screen
        self.screen.blit(self.background, (0, 0))
        
        # draw title with shadow effect for better visibility
        title_text = "Welcome to CIVSIM"
        title_x = self.screen.get_width() // 2 - 150
        title_y = 100
        
        # Draw shadow
        self.font_large.render_to(
            self.screen,
            (title_x + 2, title_y + 2),
            title_text,
            (0, 0, 0, 180)
        )
        
        # Draw main title
        self.font_large.render_to(
            self.screen,
            (title_x, title_y),
            title_text,
            (255, 255, 255)
        )
        
        subtitle_text = "Watch societies evolve, compete, and collapse"
        subtitle_x = self.screen.get_width() // 2 - 200
        subtitle_y = 150
        
        # Draw shadow for subtitle
        self.font.render_to(
            self.screen,
            (subtitle_x + 1, subtitle_y + 1),
            subtitle_text,
            (0, 0, 0, 180)
        )
        
        # Draw subtitle
        self.font.render_to(
            self.screen,
            (subtitle_x, subtitle_y),
            subtitle_text,
            (220, 220, 220)
        )
        
        # draw buttons (unless in input mode)
        if not self.input_active:
            for button in self.buttons:
                button.draw(self.screen)
        else:
            # Add semi-transparent overlay for input mode
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            self.screen.blit(overlay, (0, 0))
            
            # Create a stylish input dialog box
            dialog_width = 500
            dialog_height = 250
            dialog_x = (self.screen.get_width() - dialog_width) // 2
            dialog_y = (self.screen.get_height() - dialog_height) // 2
            
            # Create dialog surface with alpha
            dialog_surface = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
            
            # Draw dialog background with rounded corners and gradient
            # Main background - dark blue semi-transparent
            pygame.draw.rect(dialog_surface, (20, 40, 80, 220), 
                           (0, 0, dialog_width, dialog_height), 
                           border_radius=15)
            
            # Add subtle highlight at the top
            for y in range(15):
                highlight_alpha = 25 - y
                if highlight_alpha > 0:
                    pygame.draw.rect(dialog_surface, (100, 150, 250, highlight_alpha), 
                                   (10, 10 + y, dialog_width - 20, 1), 
                                   border_radius=5)
            
            # Add glowing border
            pygame.draw.rect(dialog_surface, (100, 150, 250, 150), 
                           (0, 0, dialog_width, dialog_height), 
                           2, border_radius=15)
            
            # Blit dialog to screen
            self.screen.blit(dialog_surface, (dialog_x, dialog_y))
            
            # Show different prompts based on input purpose
            if self.input_purpose == "new":
                prompt_text = "Enter a name for your new simulation:"
            else:  # load
                prompt_text = "Enter the name of the simulation to load:"
            
            # Draw prompt text with shadow
            self.font.render_to(
                self.screen,
                (dialog_x + dialog_width//2 - 170, dialog_y + 40),
                prompt_text,
                (240, 240, 255)
            )
            
            # Create input field
            input_field_width = 400
            input_field_height = 50
            input_field_x = dialog_x + (dialog_width - input_field_width) // 2
            input_field_y = dialog_y + 80
            self.input_rect = pygame.Rect(input_field_x, input_field_y, input_field_width, input_field_height)
            
            # Draw input field with glowing effect
            input_surface = pygame.Surface((input_field_width, input_field_height), pygame.SRCALPHA)
            pygame.draw.rect(input_surface, (40, 60, 100, 180), 
                           (0, 0, input_field_width, input_field_height), 
                           border_radius=8)
            pygame.draw.rect(input_surface, (100, 170, 255, 150), 
                           (0, 0, input_field_width, input_field_height), 
                           2, border_radius=8)
            self.screen.blit(input_surface, (input_field_x, input_field_y))
            
            # Draw input text with shadow
            if self.input_text:
                # Shadow
                self.font.render_to(
                    self.screen,
                    (input_field_x + 11, input_field_y + 16),
                    self.input_text,
                    (0, 0, 0, 180)
                )
                # Main text
                self.font.render_to(
                    self.screen,
                    (input_field_x + 10, input_field_y + 15),
                    self.input_text,
                    (255, 255, 255)
                )
            else:
                # Show placeholder text if empty
                self.font_small.render_to(
                    self.screen,
                    (input_field_x + 10, input_field_y + 18),
                    "Type a name...",
                    (150, 150, 200, 150)  # semi-transparent hint text
                )
            
            # Show error message if any
            if self.input_error:
                self.font_small.render_to(
                    self.screen,
                    (input_field_x, input_field_y + 60),
                    self.input_error,
                    (255, 100, 100)
                )
            
            # Show warning message if any
            if self.input_warning:
                self.font_small.render_to(
                    self.screen,
                    (input_field_x, input_field_y + 85),
                    self.input_warning,
                    (255, 200, 0)
                )
            
            # Draw instruction text with shadow
            # Shadow
            self.font.render_to(
                self.screen,
                (dialog_x + dialog_width//2 - 137, dialog_y + dialog_height - 40),
                "Press ENTER to confirm, ESC to cancel",
                (0, 0, 0, 150)
            )
            # Main text
            self.font.render_to(
                self.screen,
                (dialog_x + dialog_width//2 - 138, dialog_y + dialog_height - 41),
                "Press ENTER to confirm, ESC to cancel",
                (200, 220, 255)
            )
    
    def handle_event(self, event):
        if self.input_active:
            return self._handle_input_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # left click
                for button in self.buttons:
                    if button.is_over(event.pos):
                        return button.action()
        elif event.type == pygame.MOUSEMOTION:
            for button in self.buttons:
                button.is_hovered = button.is_over(event.pos)
                
        return None
    
    def _handle_input_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # cancel input
                self.input_active = False
                self.input_text = ""
                self.input_error = None
                self.input_warning = None
                return None
            
            elif event.key == pygame.K_RETURN:
                # validate and process input
                if not self.input_text.strip():
                    self.input_error = "Please enter a valid name."
                    return None
                
                # check for existing files if creating new simulation
                if self.input_purpose == "new":
                    save_path = f"data/{self.input_text}.pickle"
                    if os.path.exists(save_path):
                        self.input_warning = f"A simulation named '{self.input_text}' already exists. Press ENTER again to replace it."
                        # change purpose to confirm overwrite
                        self.input_purpose = "new_confirm"
                        return None
                
                # process the input
                if self.input_purpose == "new" or self.input_purpose == "new_confirm":
                    self.input_active = False
                    sim_name = self.input_text
                    self.input_text = ""
                    self.input_error = None
                    self.input_warning = None
                    return ("new", sim_name)
                
                elif self.input_purpose == "load":
                    save_path = f"data/{self.input_text}.pickle"
                    if not os.path.exists(save_path):
                        self.input_error = f"No simulation found with name '{self.input_text}'."
                        return None
                    
                    self.input_active = False
                    sim_name = self.input_text
                    self.input_text = ""
                    self.input_error = None
                    return ("load", sim_name)
            
            elif event.key == pygame.K_BACKSPACE:
                # delete last character
                self.input_text = self.input_text[:-1]
                self.input_error = None
                self.input_warning = None
                
            else:
                # add character if it's printable and not too long
                if len(self.input_text) < 30 and event.unicode.isprintable():
                    self.input_text += event.unicode
                    self.input_error = None
                    # clear warning only if we're not in confirmation mode
                    if self.input_purpose != "new_confirm":
                        self.input_warning = None
        
        return None
    
    def _new_simulation(self):
        self.input_active = True
        self.input_purpose = "new"
        return None
    
    def _load_simulation(self):
        self.input_active = True
        self.input_purpose = "load"
        return None
    
    def _exit_game(self):
        return "exit"

def run_menu(screen):
    menu = MainMenu(screen)
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not menu.input_active:
                pygame.quit()
                sys.exit()
            
            result = menu.handle_event(event)
            if result:
                return result
        
        menu.draw()
        pygame.display.flip()
        clock.tick(30)

def main():
    # make sure folders exist
    ensure_directories()
    
    # fire up pygame
    pygame.init()
    
    # set up display with larger dimensions
    width, height = 1400, 900  # increased from 1200x800
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("CIVSIM")
    try:
        pygame_icon = pygame.image.load('assets/CIVSIM.png')
        pygame.display.set_icon(pygame_icon)
    except Exception as e:
        try:
            pygame.display.set_icon(pygame.image.load('CIVSIM/assets/CIVSIM.png'))
        except Exception as e:
            print(f"Failed to load icon: {e}")

    
    # show menu
    menu_result = run_menu(screen)
    if menu_result == "exit":
        pygame.quit()
        sys.exit()
    
    simulation_name = None
    
    if isinstance(menu_result, tuple):
        action, sim_name = menu_result
        simulation_name = sim_name
        
        if action == "load":
            # load existing simulation
            try:
                # create world and simulation objects
                world_size = (100, 100)
                world = World(world_size)
                simulation = Simulation(world)
                simulation.name = sim_name
                
                # load saved state
                success, message = simulation.load_state(filename=f"{sim_name}.pickle")
                if success:
                    print(f"Successfully loaded simulation '{sim_name}'")
                else:
                    print(f"Failed to load simulation '{sim_name}': {message}")
                    # fall back to creating a new world
                    world.generate()
                    simulation.initialize(num_civs=5)
            except Exception as e:
                print(f"Error loading simulation: {e}")
                # fall back to creating a new world
                world_size = (100, 100)
                world = World(world_size)
                world.generate()
                simulation = Simulation(world)
                simulation.initialize(num_civs=5)
        else:  # action == "new"
            # create new world and simulation
            print("Generating world...")
            world_size = (100, 100)
            world = World(world_size)
            world.generate()
            
            # create simulation
            print("Setting up simulation...")
            simulation = Simulation(world)
            try:
                simulation.initialize(num_civs=5)
                print(f"Successfully created {len(world.civilizations)} civilizations")
            except Exception as e:
                print(f"Error initializing civilizations: {e}")
                # make sure at least one civ exists
                if not world.civilizations:
                    print("Attempting to create one civilization manually...")
                    simulation.add_civilization()
                    print(f"Now have {len(world.civilizations)} civilizations")
    else:
        # backwards compatibility with old menu results
        # create world (100x100 grid)
        print("Generating world...")
        world_size = (100, 100)
        world = World(world_size)
        world.generate()
        
        # create simulation
        print("Setting up simulation...")
        simulation = Simulation(world)
        try:
            simulation.initialize(num_civs=5)
            print(f"Successfully created {len(world.civilizations)} civilizations")
        except Exception as e:
            print(f"Error initializing civilizations: {e}")
            # make sure at least one civ exists
            if not world.civilizations:
                print("Attempting to create one civilization manually...")
                simulation.add_civilization()
                print(f"Now have {len(world.civilizations)} civilizations")
    
    # initial setup of visualizer and ui elements
    visualizer = Visualizer(simulation)
    renderer = Renderer(screen, world)
    renderer.set_simulation(simulation)  # add simulation reference for lore generation
    controls = Controls(simulation)
    controls.set_renderer(renderer)
    
    # store simulation name for saving
    if simulation_name:
        simulation.name = simulation_name
    
    # override save_state to use the current simulation name
    original_save_state = simulation.save_state
    def save_state_with_name():
        if hasattr(simulation, 'name'):
            success, filename = original_save_state(f"{simulation.name}")
            if success:
                return success, filename
            else:
                return False, filename  # filename contains the error message
        else:
            return original_save_state()
    simulation.save_state = save_state_with_name
    
    # create function references for charts and reports
    def gen_chart(chart_type):
        generate_chart(visualizer, chart_type, controls)
    
    def gen_report(report_type):
        generate_report(visualizer, report_type, controls)
    
    # add visualization buttons
    vis_buttons = [
        Button((10, 570, 180, 30), "Population Chart", lambda: gen_chart("population")),
        Button((10, 610, 180, 30), "Territory Chart", lambda: gen_chart("territory")),
        Button((10, 650, 180, 30), "Tech Charts", lambda: gen_chart("tech_belief")),
        Button((10, 690, 180, 30), "History Report", lambda: gen_report("history")),
        Button((10, 730, 180, 30), "Civ Report", lambda: gen_report("civilization")),
        Button((10, 770, 180, 30), "Export All Data", lambda: visualizer.export_simulation_data())
    ]
    controls.buttons.extend(vis_buttons)
    
    # show the civilization list by default to help users see what's happening
    renderer.showing_civ_list = True
    
    # create help overlay
    help_showing = True
    help_font = pygame.freetype.SysFont("Arial", 18)
    help_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    help_overlay.fill((0, 0, 0, 180))  # semi-transparent background
    
    # add welcome text
    welcome_text = [
        "Welcome to Civilization Simulator!",
        "",
        "• Colored areas are civilizations, white circles are cities",
        "• The simulation starts PAUSED - press SPACE or click Play/Pause to start",
        "• Click on civilizations to see their details",
        "• Use UP/DOWN arrows to change simulation speed",
        "• Press C to see all civilizations",
        "• Press H to show/hide this help overlay"
    ]
    
    for i, line in enumerate(welcome_text):
        help_font.render_to(help_overlay, (width // 2 - 200, height // 2 - 100 + i * 30), line, (255, 255, 255))
    
    # main game loop
    print("Starting simulation...")
    clock = pygame.time.Clock()
    running = True
    simulation_speed = 3  # default to middle speed (what was previously 5x)
    speed_values = [0.1, 0.25, 0.5, 1, 2, 3, 4, 5]  # new speed values (0.1x to 5x)
    frame_counter = 0
    
    # help text for keyboard shortcuts
    keyboard_shortcuts = [
        "SPACE - Play/Pause simulation",
        "UP/DOWN - Change simulation speed",
        "C - Toggle civilization list",
        "G - Toggle God Mode",
        "H - Toggle help overlay",
        "M - Return to main menu",
        "V - Toggle city visibility",
        "L - Toggle all civilization labels",
        "P - Toggle auto-pause on events",
        "ESC - Exit game"
    ]
    
    # add info about ui buttons
    button_instructions = [
        "",
        "UI Buttons:",
        "• 'Toggle Info Panel' button - Hides/Shows the bottom panel for full map view",
        "• God Mode buttons appear on the left after activating God Mode"
    ]
    
    keyboard_shortcuts.extend(button_instructions)
    
    while running:
        # increment frame counter for optimized rendering
        frame_counter += 1
        
        # handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    simulation.paused = not simulation.paused
                    controls._show_feedback("Simulation " + ("PAUSED" if simulation.paused else "RUNNING"))
                elif event.key == pygame.K_UP:
                    simulation_speed = min(len(speed_values) - 1, simulation_speed + 1)
                    controls._show_feedback(f"Speed: {speed_values[simulation_speed]}x")
                elif event.key == pygame.K_DOWN:
                    simulation_speed = max(0, simulation_speed - 1)
                    controls._show_feedback(f"Speed: {speed_values[simulation_speed]}x")
                elif event.key == pygame.K_c:
                    renderer.toggle_civilization_list()
                    controls._show_feedback("Civilization list " + ("shown" if renderer.showing_civ_list else "hidden"))
                elif event.key == pygame.K_s:
                    gen_chart("population")
                elif event.key == pygame.K_h:
                    help_showing = not help_showing
                    controls._show_feedback("Help " + ("shown" if help_showing else "hidden"))
                elif event.key == pygame.K_m:
                    menu_result = run_menu(screen)
                    if menu_result == "exit":
                        running = False
                elif event.key == pygame.K_g:
                    toggle_god_mode(controls, renderer)
                elif event.key == pygame.K_v:
                    show_cities = renderer.toggle_city_visibility()
                    controls._show_feedback("City markers " + ("shown" if show_cities else "hidden"))
                elif event.key == pygame.K_l:
                    show_labels = renderer.toggle_labels()
                    controls._show_feedback("All labels " + ("shown" if show_labels else "hidden"))
                elif event.key == pygame.K_p:
                    auto_pause = simulation.toggle_auto_pause()
                    if hasattr(controls, 'auto_pause_button'):
                        controls.auto_pause_button.text = f"Auto-Pause: {'ON' if auto_pause else 'OFF'}"
                    controls._show_feedback(f"Auto-pause on events {'enabled' if auto_pause else 'disabled'}")

            # START --- mouse event handling block
            # prioritize civ detail popup interactions if it's showing
            civ_details_consumed_event = False
            if renderer.showing_civ_details:
                if event.type == pygame.MOUSEWHEEL: 
                    renderer.handle_civ_detail_scroll(event)
                    civ_details_consumed_event = True 
                elif event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                    # pass event to scroll handler first
                    # handle_civ_detail_scroll will internally check if it's a scrollbar drag or relevant click
                    renderer.handle_civ_detail_scroll(event) 
                    # check if the main civ_details popup (e.g. close button) consumed the click
                    if event.type == pygame.MOUSEBUTTONDOWN and renderer.check_civ_details_click(event.pos):
                        civ_details_consumed_event = True
                    # if dragging scrollbar, it consumes the event
                    elif renderer.dragging_scrollbar:
                         civ_details_consumed_event = True
            
            if not civ_details_consumed_event: # if civ details didn't handle it, process other ui
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not help_showing:
                        action_taken = controls._handle_mouse_click(event.pos)
                        if action_taken == "return_to_menu":
                            menu_result = run_menu(screen)
                            if menu_result == "exit":
                                running = False
                            # 'continue' might skip essential end-of-loop processing, manage 'running' instead
                            if not running: break # exit event loop if game exited via menu
                        elif action_taken: # a ui button was clicked
                            pass # action handled by controls
                        else: # no ui button clicked, check other interactions
                            if renderer.check_notification_click(event.pos):
                                pass # notification dismissed
                            elif renderer.set_selected_position(event.pos):
                                controls.set_selected_position(renderer.selected_position)
                                controls.set_selected_civilization(renderer.selected_civilization)
                                controls.more_info_button_active = renderer.selected_civilization is not None
                
                elif event.type == pygame.MOUSEMOTION: # general hover for controls if not dragging scrollbar
                    if not (renderer.showing_civ_details and renderer.dragging_scrollbar):
                        controls.handle_event(event) 
            # END --- mouse event handling block
        
        # update simulation if not paused
        if not simulation.paused:
            # only process simulation at appropriate frames based on speed setting
            current_speed = speed_values[simulation_speed]
            
            # convert speed value to tick frequency
            if current_speed >= 1:
                # for speeds 1x and higher, process multiple ticks per frame
                for _ in range(int(current_speed)):
                    auto_paused = simulation.tick()
                    
                    # check for major events that should show notification
                    major_events = simulation.get_major_events()
                    if major_events:
                        # show notification for the first major event
                        event = major_events[0]
                        renderer.show_notification(event["title"], event["message"], event["civ"])
                        
                        if auto_paused:
                            controls._show_feedback("Simulation paused due to major event")
                            # only process one tick if we auto-paused
                            break
            else:
                # for speeds below 1x, process ticks less frequently
                if frame_counter % int(1/current_speed) == 0:
                    auto_paused = simulation.tick()
                    
                    # check for major events
                    major_events = simulation.get_major_events()
                    if major_events:
                        event = major_events[0]
                        renderer.show_notification(event["title"], event["message"], event["civ"])
                        
                        if auto_paused:
                            controls._show_feedback("Simulation paused due to major event")
        
        # render everything
        renderer.render()
        controls.draw(screen)
        
        # display simulation info
        current_civ_count = len(world.civilizations)
        font = pygame.freetype.SysFont("Arial", 16)
        # position info at the top of the map area (not in either panel)
        info_x = renderer.offset_x
        info_y = 10
        font.render_to(screen, (info_x, info_y), 
                    f"Year: {simulation.year} | Civs: {current_civ_count} | " +
                    f"{'PAUSED' if simulation.paused else 'RUNNING'} | Speed: {speed_values[simulation_speed]}x", 
                    (0, 0, 0))  # changed to black for better visibility
        
        # add fps counter (performance monitoring)
        fps = clock.get_fps()
        font.render_to(screen, (info_x + 500, info_y), f"FPS: {fps:.1f}", (0, 0, 0))  # changed to black
        
        # update help overlay with new keyboard shortcuts
        if help_showing:
            # recreate help overlay to include new shortcuts
            help_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            help_overlay.fill((0, 0, 0, 180))  # semi-transparent background
            
            # add welcome text
            welcome_text = [
                "Welcome to Civilization Simulator!",
                "",
                "Keyboard Controls:"
            ]
            
            # add all keyboard shortcuts
            for i, shortcut in enumerate(keyboard_shortcuts):
                welcome_text.append(f"• {shortcut}")
            
            for i, line in enumerate(welcome_text):
                help_font.render_to(help_overlay, (width // 2 - 200, height // 2 - 200 + i * 25), line, (255, 255, 255))
            
            screen.blit(help_overlay, (0, 0))
        
        # update the display
        pygame.display.flip()
        
        # cap the frame rate
        clock.tick(60)
    
    # clean up
    print("Exporting final simulation data...")
    visualizer.export_simulation_data()
    pygame.quit()
    sys.exit()

def generate_chart(visualizer, chart_type, controls):
    """generate and save charts"""
    try:
        if chart_type == "population":
            path = visualizer.generate_population_chart()
            controls._show_feedback(f"Population chart saved to {path}")
            print(f"Population chart saved to {path}")
        elif chart_type == "territory":
            path = visualizer.generate_territory_chart()
            controls._show_feedback(f"Territory chart saved to {path}")
            print(f"Territory chart saved to {path}")
        elif chart_type == "tech_belief":
            path1 = visualizer.generate_technology_chart()
            path2 = visualizer.generate_belief_distribution_chart()
            controls._show_feedback(f"Technology and belief charts saved")
            print(f"Technology chart saved to {path1}")
            print(f"Belief chart saved to {path2}")
        
        # check if any civilizations exist
        if not visualizer.simulation.world.civilizations:
            controls._show_feedback("No civilizations to chart! Add some first.")
    except Exception as e:
        error_msg = f"Error generating chart: {str(e)}"
        controls._show_feedback(error_msg)
        print(error_msg)

def generate_report(visualizer, report_type, controls):
    """generate and save reports"""
    try:
        if report_type == "history":
            path = visualizer.generate_historical_report()
            controls._show_feedback(f"Historical report saved to {path}")
            print(f"Historical report saved to {path}")
        elif report_type == "civilization":
            path = visualizer.generate_civilization_report()
            controls._show_feedback(f"Civilization report saved to {path}")
            print(f"Civilization report saved to {path}")
            
        # check if any civilizations exist
        if not visualizer.simulation.world.civilizations:
            controls._show_feedback("No civilizations in report! Add some first.")
    except Exception as e:
        error_msg = f"Error generating report: {str(e)}"
        controls._show_feedback(error_msg)
        print(error_msg)

def toggle_god_mode(controls, renderer):
    # toggle god mode state
    controls.showing_god_mode = not controls.showing_god_mode
    renderer.set_god_mode(controls.showing_god_mode)
    
    # show/hide god mode buttons from the main button list in controls
    if controls.showing_god_mode:
        for button in controls.god_mode_buttons:
            if button not in controls.buttons:
                controls.buttons.append(button)
    else:
        for button in controls.god_mode_buttons:
            if button in controls.buttons:
                controls.buttons.remove(button)
    
    controls._show_feedback("God Mode " + ("ENABLED" if controls.showing_god_mode else "DISABLED"))

if __name__ == "__main__":
    main() 