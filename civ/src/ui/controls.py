"""
ui controls module for civ simulator
"""
# Example content - file may not exist or have different content

import pygame
import pygame.freetype
import random

class Button:
    def __init__(self, rect, text, action=None, color=(80, 80, 80), hover_color=(120, 120, 120)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.freetype.SysFont("Arial", 14)
    
    def draw(self, screen):
        # draw button background
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        
        # draw text
        text_surf, text_rect = self.font.render(self.text, (255, 255, 255))
        text_rect.center = self.rect.center
        screen.blit(text_surf, text_rect)
    
    def is_over(self, pos):
        return self.rect.collidepoint(pos)

class Controls:
    def __init__(self, simulation):
        self.simulation = simulation
        self.world = simulation.world
        self.buttons = []
        self.god_mode_buttons = []
        self.showing_god_mode = False
        self.renderer = None # for calling renderer methods like show_civ_details
        
        # ui state
        self.selected_civ = None
        self.selected_position = None
        
        # create ui elements
        self._create_ui_elements()
        
        # add "more info" button when civilization is selected
        # positioned dynamically in draw() method, within the bottom panel
        self.more_info_button = Button((0,0,0,0), "More Info", self._show_civ_details) 
        self.more_info_button_active = False
        
    def _create_ui_elements(self):
        """create ui buttons and elements"""
        # main buttons - moved to left panel in vertical layout
        self.buttons = [
            Button((10, 50, 180, 30), "Play/Pause", self._toggle_pause),
            Button((10, 90, 180, 30), "Step", self._step_simulation),
            Button((10, 130, 180, 30), "God Mode", self._toggle_god_mode),
            Button((10, 170, 180, 30), "Save", self._save_game),
            Button((10, 210, 180, 30), "Return to Menu", self._return_to_menu), # changed from load
            # Button((10, 250, 180, 30), "Help", self._toggle_help), # original help button (removed as per request)
            # the more info button is now handled dynamically when a civ is selected and drawn in the bottom panel
            # the auto-pause button is added directly in main.py to the controls.buttons list
        ]
        
        # auto-pause button added here
        self.auto_pause_button = Button(
            (10, 250, 180, 30), # adjusted y position
            f"Auto-Pause: {'ON' if self.simulation.auto_pause_on_events else 'OFF'}", 
            self._toggle_auto_pause_action
        )
        self.buttons.append(self.auto_pause_button)
        
        # toggle bottom panel button
        self.toggle_panel_button = Button(
            (10, 290, 180, 30),
            "Toggle Info Panel",
            self._toggle_bottom_panel
        )
        self.buttons.append(self.toggle_panel_button)
        
        # god mode buttons (initially hidden) - moved to left panel
        self.god_mode_buttons = [
            Button((10, 330, 180, 30), "Add Civilization", self._add_civilization),
            Button((10, 370, 180, 30), "Trigger Disaster", self._trigger_disaster),
            Button((10, 410, 180, 30), "Grant Blessing", self._grant_blessing),
            Button((10, 450, 180, 30), "Tech Boost", self._tech_boost),
            Button((10, 490, 180, 30), "Shift Ideology", self._shift_ideology),
            Button((10, 530, 180, 30), "Influence War", self._influence_war)
        ]
        
        # feedback message variables
        self.show_feedback = False
        self.feedback_message = ""
        self.feedback_timer = 0
    
    def handle_event(self, event):
        """handle a pygame event"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # left click
                self._handle_mouse_click(event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            # update button hover states
            for button in self.buttons:
                button.is_hovered = button.is_over(event.pos)
            
            if self.showing_god_mode:
                for button in self.god_mode_buttons:
                    button.is_hovered = button.is_over(event.pos)
            
            # update hover state for more info button
            if self.more_info_button_active:
                self.more_info_button.is_hovered = self.more_info_button.is_over(event.pos)
    
    def draw(self, screen):
        """draw ui controls"""
        for button in self.buttons:
            button.draw(screen)
        
        if self.showing_god_mode:
            for button in self.god_mode_buttons:
                button.draw(screen)
        
        if self.show_feedback and self.feedback_timer > 0:
            font = pygame.freetype.SysFont("Arial", 14)
            panel_width = 200 
            msg_background = pygame.Surface((panel_width - 20, 30), pygame.SRCALPHA)
            msg_background.fill((50, 50, 50, 220))
            screen.blit(msg_background, (10, self.buttons[-1].rect.bottom + 10 if self.buttons else 550))
            
            words = self.feedback_message.split()
            lines = []
            current_line = words[0] if words else ""
            for word in words[1:]:
                test_line = current_line + " " + word
                width, _ = font.get_rect(test_line)[2:4]
                if width < panel_width - 30:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
            
            for i, line in enumerate(lines):
                font.render_to(screen, (15, (self.buttons[-1].rect.bottom + 15 if self.buttons else 555) + i*20), line, (255, 255, 100))
            
            self.feedback_timer -= 1
            if self.feedback_timer <= 0:
                self.show_feedback = False
        
        # draw "more info" button in the right-side panel if a civ is selected and renderer is available
        if self.selected_civ and self.more_info_button_active and self.renderer:
            # position at the bottom of the right-side panel
            right_panel_x = screen.get_width() - self.renderer.side_panel_width
            button_x_pos = right_panel_x + (self.renderer.side_panel_width - 100) // 2 # centered in side panel
            button_y_pos = screen.get_height() - 40 # 40px from the bottom of the screen
            
            self.more_info_button.rect = pygame.Rect(button_x_pos, button_y_pos, 100, 30)
            self.more_info_button.draw(screen)
    
    def _handle_mouse_click(self, pos):
        """handle mouse click at position. returns true if a button was actioned, or a string for special actions."""
        # check main buttons first (includes auto-pause button)
        for button in self.buttons:
            if button.is_over(pos) and button.action:
                action_result = button.action()
                if action_result == "return_to_menu":
                    return "return_to_menu"
                return True # a button was clicked and actioned
        
        # check god mode buttons if they're visible
        if self.showing_god_mode:
            for button in self.god_mode_buttons:
                if button.is_over(pos) and button.action:
                    button.action()  # call the god mode button action
                    return True  # god mode button was clicked and actioned
        
        # handle clicks on the more info button if active and not handled above
        if self.selected_civ and self.more_info_button_active and self.more_info_button.is_over(pos):
            if self.more_info_button.action:
                 self.more_info_button.action()
                 return True # more info button was clicked
        
        return False # no button handled the click
    
    def _toggle_pause(self):
        """toggle simulation pause state"""
        self.simulation.paused = not self.simulation.paused
        self._show_feedback("Simulation " + ("PAUSED" if self.simulation.paused else "RUNNING"))
    
    def _step_simulation(self):
        """step the simulation forward one tick"""
        self.simulation.tick()
        self._show_feedback(f"Advanced to year {self.simulation.year}")
    
    def _toggle_god_mode(self):
        """toggle god mode panel"""
        self.showing_god_mode = not self.showing_god_mode
        self._show_feedback("God Mode " + ("ENABLED" if self.showing_god_mode else "DISABLED"))
    
    def _toggle_help(self):
        """Show help overlay"""
        # This is handled in main.py
        self._show_feedback("Showing help overlay")
    
    def _save_game(self):
        """Save the current game"""
        try:
            success, message = self.simulation.save_state()
            if success:
                self._show_feedback(f"Game saved successfully as '{message}'")
            else:
                self._show_feedback(f"Error saving game: {message}")
        except Exception as e:
            print(f"Error saving game: {e}")
            self._show_feedback(f"Error saving game: {str(e)}")
    
    def _load_game(self):
        """Load a saved game"""
        try:
            # This is now primarily handled through the menu,
            # but here we could add a popup or dialog to select a saved game
            self._show_feedback("Use the main menu to load a saved game")
            return "return_to_menu"
        except Exception as e:
            print(f"Error loading game: {e}")
            self._show_feedback(f"Error loading game: {str(e)}")
    
    def _return_to_menu(self):
        """Signal to return to the main menu."""
        self._show_feedback("Returning to main menu...")
        return "return_to_menu"
    
    def _toggle_auto_pause_action(self):
        """Action for the auto-pause button."""
        auto_pause = self.simulation.toggle_auto_pause()
        self.auto_pause_button.text = f"Auto-Pause: {'ON' if auto_pause else 'OFF'}"
        self._show_feedback(f"Auto-pause on events {'enabled' if auto_pause else 'disabled'}")
    
    def _add_civilization(self):
        """Add a new civilization (God mode)"""
        pos = self.selected_position if self.selected_position else None
        
        try:
            # Check if the limit is already met before attempting to add
            # This is a redundant check if simulation.add_civilization always raises an error,
            # but provides a slightly more graceful UI experience by checking first.
            if len(self.simulation.world.civilizations) >= self.simulation.max_civilizations:
                self._show_feedback(f"Max civilization count ({self.simulation.max_civilizations}) reached.")
                return

            # If there's a selected position, use it; otherwise let the simulation choose randomly
            if pos:
                self._show_feedback(f"Creating civilization at selected position {pos}")
                new_civ = self.simulation.add_civilization(position=pos)
            else:
                self._show_feedback("Creating civilization at random position")
                new_civ = self.simulation.add_civilization()
            
            if not self.simulation.paused:
                self.simulation.paused = True
                self._show_feedback(f"New civilization '{new_civ.name}' created! Sim paused.")
            else:
                self._show_feedback(f"New civilization '{new_civ.name}' created!")
            
            print(f"Added new civilization: {new_civ.name}")
        except ValueError as e:
            # Catch the error from simulation.add_civilization if the max limit was hit
            self._show_feedback(str(e))
            print(f"Error adding civ: {e}")
        except Exception as e:
            error_msg = f"Failed to add civilization: {str(e)}"
            self._show_feedback(error_msg)
            print(error_msg)
    
    def _trigger_disaster(self):
        """Trigger a natural disaster (God mode)"""
        # If a civilization is selected, target them
        target_civ = self.selected_civ
        position = self.selected_position
        
        # Make sure we have at least a position if no target_civ
        if not target_civ and not position:
            # Pick a random position on the map if neither civ nor position is selected
            position = (
                random.randint(0, self.simulation.world.width - 1),
                random.randint(0, self.simulation.world.height - 1)
            )
            
        if target_civ:
            self._show_feedback(f"Disaster unleashed on {target_civ.name}!")
        elif position:
            self._show_feedback(f"Disaster unleashed at position {position}!")
        else:
            self._show_feedback("Disaster unleashed at random location!")
            
        self.simulation.trigger_god_event("disaster", target_civ, position)
    
    def _grant_blessing(self):
        """Grant a blessing to a civilization (God mode)"""
        # Need a selected civilization
        if self.selected_civ:
            self.simulation.trigger_god_event("blessing", self.selected_civ)
            self._show_feedback(f"Blessing granted to {self.selected_civ.name}!")
        else:
            # If no civilization is selected, choose a random one
            if self.world.civilizations:
                random_civ = random.choice(self.world.civilizations)
                self.simulation.trigger_god_event("blessing", random_civ)
                self._show_feedback(f"Blessing granted to random civilization: {random_civ.name}!")
            else:
                self._show_feedback("No civilizations exist to bless!")
    
    def _tech_boost(self):
        """Boost a civilization's technology (God mode)"""
        # Need a selected civilization
        if self.selected_civ:
            self.simulation.trigger_god_event("tech_boost", self.selected_civ)
            self._show_feedback(f"Tech boost granted to {self.selected_civ.name}!")
        else:
            self._show_feedback("Select a civilization first!")
    
    def _shift_ideology(self):
        """Shift a civilization's ideology (God mode)"""
        # Need a selected civilization
        if self.selected_civ:
            self.simulation.trigger_god_event("shift_ideology", self.selected_civ)
            self._show_feedback(f"Ideology shifted for {self.selected_civ.name}!")
        else:
            self._show_feedback("Select a civilization first!")
    
    def _influence_war(self):
        """Influence war between civilizations (God mode)"""
        # Need at least two civilizations for a war
        if len(self.world.civilizations) < 2:
            self._show_feedback("Need at least two civilizations for war!")
            return
            
        # If a civilization is selected, use it as the primary target
        if self.selected_civ:
            # Find all other civilizations to pick an enemy
            other_civs = [civ for civ in self.world.civilizations if civ.id != self.selected_civ.id]
            if other_civs:
                self.simulation.trigger_god_event("war_influence", self.selected_civ)
                self._show_feedback(f"War influence applied to {self.selected_civ.name}!")
            else:
                self._show_feedback(f"No other civilizations for {self.selected_civ.name} to fight!")
        else:
            # Pick two random civilizations
            if len(self.world.civilizations) >= 2:
                civ1, civ2 = random.sample(self.world.civilizations, 2)
                self.simulation.trigger_god_event("war_influence", civ1)
                self._show_feedback(f"War influence applied between {civ1.name} and another civilization!")
            else:
                self._show_feedback("Need at least two civilizations for war!")
    
    def set_selected_civilization(self, civ):
        """Set the selected civilization"""
        self.selected_civ = civ
        self.more_info_button_active = (civ is not None)
        if civ:
            self._show_feedback(f"Selected {civ.name}")
    
    def set_selected_position(self, position):
        """Set the selected position"""
        self.selected_position = position
    
    def _show_feedback(self, message):
        """Show a feedback message"""
        self.show_feedback = True
        self.feedback_message = message
        self.feedback_timer = 180  # Show for 3 seconds at 60 fps 

    def _show_detailed_info(self):
        """Show detailed civilization information if a civ is selected."""
        if self.selected_civ and self.renderer:
            self.renderer.show_civ_details(self.selected_civ)
            self._show_feedback(f"Showing details for {self.selected_civ.name}")
        elif not self.selected_civ:
            self._show_feedback("Select a civilization to see more info.")
        else:
            self._show_feedback("Renderer not available for details.")

    def _show_civ_details(self):
        """Callback for the 'More Info' button, calls _show_detailed_info"""
        self._show_detailed_info()

    def set_renderer(self, renderer):
        self.renderer = renderer 
        
    def _toggle_bottom_panel(self):
        """Toggle the visibility of the bottom information panel"""
        if self.renderer:
            is_visible = self.renderer.toggle_bottom_panel()
            self._show_feedback(f"Information Panel {'Hidden' if not is_visible else 'Shown'}")
        else:
            self._show_feedback("Renderer not available") 