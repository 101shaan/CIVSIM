"""
ui renderer module for civ simulator
"""
# Example content - file may not exist or have different content

import pygame
import pygame.freetype
import math
from src.world import TerrainType
import random

class Renderer:
    def __init__(self, screen, world):
        self.screen = screen
        self.world = world
        self.width, self.height = screen.get_size()
        
        # grid cell size for rendering
        self.grid_cell_size = min(10, min(self.width // self.world.width, 
                                         self.height // self.world.height))
        
        # ui elements - move to sides instead of bottom
        self.side_panel_width = 250  # right side panel width
        self.left_panel_width = 200  # new left panel width
        self.bottom_panel_height = 120  # reduced bottom panel height
        self.show_bottom_panel = True  # new property to toggle bottom panel visibility
        
        # offset to center the grid in the remaining space
        map_width = self.width - self.left_panel_width - self.side_panel_width
        self.offset_x = self.left_panel_width + (map_width - self.world.width * self.grid_cell_size) // 2
        self.offset_y = 10  # move map to the top to make room for ui at bottom
        
        # ui elements
        self.font = pygame.freetype.SysFont("Arial", 14)
        self.font_small = pygame.freetype.SysFont("Arial", 12)
        self.font_large = pygame.freetype.SysFont("Arial", 16)
        self.selected_position = None
        self.selected_civilization = None
        self.showing_civ_list = False
        
        # performance optimization - caching
        self.terrain_surface = None
        self.last_render_tick = -1
        self.territory_surfaces = {}  # caches territory rendering per civ
        
        # special location types
        self.location_types = {
            "city": {"symbol": "○", "min_pop": 100},  # basic city
            "capital": {"symbol": "⬤", "min_pop": 1000},  # capital city (largest)
            "temple": {"symbol": "▲", "min_pop": 50, "traits": ["religious"]},  # religious building
            "trade_hub": {"symbol": "◆", "min_pop": 150, "traits": ["trading"]},  # market/trading post
            "fortress": {"symbol": "■", "min_pop": 200, "traits": ["aggressive"]},  # military fort
            "library": {"symbol": "★", "min_pop": 100, "traits": ["tech_savvy"]},  # library/university
        }
        
        # event notification system
        self.event_notification = None
        self.notification_timer = 0
        
        # colors
        self.terrain_colors = {
            TerrainType.WATER: (0, 105, 148),      # blue
            TerrainType.LAND: (76, 187, 23),       # green
            TerrainType.MOUNTAIN: (140, 140, 140),  # gray
            TerrainType.FOREST: (0, 128, 0),        # dark green
            TerrainType.DESERT: (194, 178, 128)     # tan
        }
        
        self.civilization_colors = [
            (200, 0, 0),    # red
            (0, 0, 200),    # blue
            (200, 200, 0),  # yellow
            (200, 0, 200),  # purple
            (0, 200, 200),  # cyan
            (255, 128, 0),  # orange
            (128, 0, 255),  # violet
            (0, 255, 128),  # mint
            (255, 0, 128),  # pink
            (128, 128, 0),  # olive
        ]
        
        # highlight animation
        self.highlight_timer = 0
        self.highlight_direction = 1
        
        # rendering flags
        self.god_mode_active = False
        self.show_cities = True  # toggle for city visibility
        self.show_all_labels = False  # toggle for showing all labels
        
        # pre-render the terrain
        self._prerender_terrain()
        
        # for civilization detail popup
        self.showing_civ_details = False
        self.detail_civ = None
        self.detail_surface = None
        self.detail_rect = None
        self.detail_close_button = None
        self.detail_scroll_y = 0  # Current scroll position (y-offset)
        self.detail_max_scroll_y = 0 # max scrollable amount
        self.detail_content_height = 0 # actual height of all content
        self.scroll_bar_rect = None
        self.scroll_thumb_rect = None
        self.dragging_scrollbar = False
        self.drag_offset_y = 0  # Added for scroll dragging
        
        # reference to the simulation object for lore generation
        self.simulation = None

        # Starfield properties
        self.stars = []
        self._initialize_stars()

    def _initialize_stars(self):
        """Initialize star properties for the background starfield."""
        self.stars = []
        num_stars = 150  # Adjust for density
        for _ in range(num_stars):
            star = {
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'size': random.uniform(0.5, 2.0), # More variation in size
                'brightness': random.uniform(0.3, 1.0), # Base brightness (0.0 to 1.0)
                'twinkle_speed': random.uniform(0.01, 0.05), # How fast it twinkles
                'twinkle_phase': random.uniform(0, 2 * math.pi), # Initial phase for twinkling
                'dx': random.uniform(-0.05, 0.05), # Slow horizontal drift
                'dy': random.uniform(-0.05, 0.05)  # Slow vertical drift
            }
            self.stars.append(star)

    def _update_and_draw_stars(self):
        """Update star positions and brightness, then draw them."""
        map_rect = pygame.Rect(
            self.offset_x, 
            self.offset_y, 
            self.world.width * self.grid_cell_size,
            self.world.height * self.grid_cell_size
        )

        for star in self.stars:
            # Update position
            star['x'] += star['dx']
            star['y'] += star['dy']

            # Wrap stars around the screen
            if star['x'] < 0: star['x'] = self.width
            if star['x'] > self.width: star['x'] = 0
            if star['y'] < 0: star['y'] = self.height
            if star['y'] > self.height: star['y'] = 0
            
            # Update twinkle
            star['twinkle_phase'] += star['twinkle_speed']
            if star['twinkle_phase'] > 2 * math.pi:
                star['twinkle_phase'] -= 2 * math.pi
            
            # Calculate current brightness based on sin wave
            current_brightness_factor = (math.sin(star['twinkle_phase']) + 1) / 2 # Range 0 to 1
            # Modulate base brightness with twinkle factor
            final_brightness = star['brightness'] * (0.5 + current_brightness_factor * 0.5) # Ensure stars don't get too dim

            # Create star color (white-ish with varying brightness)
            color_val = int(final_brightness * 200) + 55 # Range 55 to 255
            star_color = (min(255,color_val), min(255,color_val + 10), min(255,color_val + 20))

            # Only draw stars in the background areas (not over map or panels)
            star_pos = (int(star['x']), int(star['y']))
            if not map_rect.collidepoint(star_pos) and \
               not (star_pos[0] < self.left_panel_width or \
                    star_pos[0] > self.width - self.side_panel_width or \
                    (self.show_bottom_panel and star_pos[1] > self.height - self.bottom_panel_height and \
                     star_pos[0] > self.left_panel_width and star_pos[0] < self.width - self.side_panel_width)):
                
                current_size = star['size'] * (0.7 + current_brightness_factor * 0.3) # Size also varies with twinkle
                if current_size >= 1: # Draw circles for larger stars
                    pygame.draw.circle(self.screen, star_color, star_pos, int(current_size))
                else: # Draw single pixels for very small/dim stars
                     self.screen.set_at(star_pos, star_color)

    def _prerender_terrain(self):
        """pre-render the terrain to a surface for performance"""
        self.terrain_surface = pygame.Surface((self.world.width * self.grid_cell_size, 
                                              self.world.height * self.grid_cell_size))
        
        for x in range(self.world.width):
            for y in range(self.world.height):
                # calculate surface position
                surface_x = x * self.grid_cell_size
                surface_y = y * self.grid_cell_size
                
                # get terrain type at this position
                terrain_type = self.world.get_terrain_at((x, y))
                
                # draw terrain
                if terrain_type is not None:
                    color = self.terrain_colors.get(terrain_type, (100, 100, 100))
                    pygame.draw.rect(
                        self.terrain_surface,
                        color,
                        (surface_x, surface_y, self.grid_cell_size, self.grid_cell_size)
                    )

    def _cache_civilization_territory(self, civ, civ_index, force_update=False):
        """cache the territory rendering for a civilization"""
        if civ.id in self.territory_surfaces and not force_update:
            return self.territory_surfaces[civ.id]
            
        # create new surface for this civilization's territory
        territory_surface = pygame.Surface((self.world.width * self.grid_cell_size, 
                                           self.world.height * self.grid_cell_size), 
                                           pygame.SRCALPHA)
        
        # get color for this civilization
        color = self.civilization_colors[civ_index % len(self.civilization_colors)]
        
        # make selected civilization stand out
        is_selected = (civ == self.selected_civilization)
        
        # check if this civilization is protected
        is_protected = hasattr(civ, 'protected_until_tick')
        
        # adjust brightness for selected and protected status
        brightness = 1.0
        if is_selected:
            brightness += 0.3 * self.highlight_timer
        if is_protected:
            brightness += 0.5 + 0.2 * self.highlight_timer
        
        # enhanced brightness color
        draw_color = (
            min(255, int(color[0] * brightness)),
            min(255, int(color[1] * brightness)),
            min(255, int(color[2] * brightness))
        )
        
        # special border for protected civilizations
        if is_protected:
            border_color = (255, 255, 255)  # white border for protected
        else:
            border_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        
        # draw territory
        for pos in civ.territory:
            x, y = pos
            surface_x = x * self.grid_cell_size
            surface_y = y * self.grid_cell_size
            
            pygame.draw.rect(
                territory_surface,
                draw_color,
                (surface_x, surface_y, self.grid_cell_size, self.grid_cell_size)
            )
            
            pygame.draw.rect(
                territory_surface,
                border_color,
                (surface_x, surface_y, self.grid_cell_size, self.grid_cell_size),
                1
            )
        
        # store in cache
        self.territory_surfaces[civ.id] = territory_surface
        return territory_surface

    def _get_civilization_color(self, civ):
        """Get the color for a civilization.
        
        Args:
            civ: The civilization object
            
        Returns:
            A RGB tuple representing the color
        """
        # Find the index of this civilization in the world's list
        try:
            civ_index = self.world.civilizations.index(civ)
        except ValueError:
            # If civilization isn't in the list (might be collapsed), use its ID as index
            civ_index = civ.id
            
        # Return the color, using modulo to cycle through available colors
        return self.civilization_colors[civ_index % len(self.civilization_colors)]

    def render(self):
        """Render the entire simulation"""
        # Create a background similar to main menu
        map_bg_color_top = (10, 20, 50)
        map_bg_color_bottom = (30, 40, 80)
        
        # Fill the whole screen with gradient background
        for y in range(self.height):
            # Calculate gradient colors
            r = int(map_bg_color_top[0] + (map_bg_color_bottom[0] - map_bg_color_top[0]) * (y / self.height))
            g = int(map_bg_color_top[1] + (map_bg_color_bottom[1] - map_bg_color_top[1]) * (y / self.height))
            b = int(map_bg_color_top[2] + (map_bg_color_bottom[2] - map_bg_color_top[2]) * (y / self.height))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (self.width, y))
        
        # Update and draw the starfield
        self._update_and_draw_stars()
        
        # Render the world grid
        self._render_world_grid()
        
        # Render left panel with buttons and controls
        self._render_left_panel()
        
        # Render right side panel
        self._render_side_panel()
        
        # Render bottom panel if visible
        if self.show_bottom_panel:
            self._render_bottom_panel()
        
        # Render notification if any
        if self.event_notification:
            self._render_notification()
        
        # Update highlight animation
        self.highlight_timer += 0.05 * self.highlight_direction
        if self.highlight_timer > 1.0:
            self.highlight_direction = -1
            self.highlight_timer = 1.0
        elif self.highlight_timer < 0.3:
            self.highlight_direction = 1
            self.highlight_timer = 0.3
        
        # Draw civilization details popup if active
        if self.showing_civ_details and self.detail_civ:
            self._draw_civ_details()
    
    def _render_world_grid(self):
        """Render the world grid with civilizations"""
        # Draw the pre-rendered terrain
        self.screen.blit(self.terrain_surface, (self.offset_x, self.offset_y))
        
        # Track new territories to highlight them
        new_territories = {}
        for civ in self.world.civilizations:
            if hasattr(civ, 'territory_last_tick'):
                new_territories[civ.id] = set()
                for pos in civ.territory:
                    if civ.territory_last_tick and pos not in civ.territory_last_tick:
                        new_territories[civ.id].add(pos)
        
        # Draw civilization territories
        for civ in self.world.civilizations:
            # Skip drawing collapsed civs
            if hasattr(civ, 'has_collapsed') and civ.has_collapsed:
                continue
                
            # Get civilization color
            civ_color = self._get_civilization_color(civ)
            
            # Draw territory with border effect
            for pos in civ.territory:
                x, y = pos
                screen_x = x * self.grid_cell_size + self.offset_x
                screen_y = y * self.grid_cell_size + self.offset_y
                
                # Draw main territory with transparency
                territory_surface = pygame.Surface((self.grid_cell_size, self.grid_cell_size), pygame.SRCALPHA)
                territory_surface.fill((civ_color[0], civ_color[1], civ_color[2], 160))
                self.screen.blit(territory_surface, (screen_x, screen_y))
                
                # Highlight newly acquired territories with pulsing effect
                if civ.id in new_territories and pos in new_territories[civ.id]:
                    # Create pulsing border effect
                    highlight_alpha = int(128 + 127 * abs(math.sin(self.highlight_timer * 10)))
                    pygame.draw.rect(self.screen, 
                                    (255, 255, 255, highlight_alpha), 
                                    pygame.Rect(screen_x, screen_y, self.grid_cell_size, self.grid_cell_size), 2)
                    
                # Add civilization borders
                borders = []
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    adj_pos = (x + dx, y + dy)
                    # Check if adjacent tile is outside civ territory
                    if adj_pos not in civ.territory:
                        if dx == 0 and dy == 1:  # Bottom
                            borders.append(((0, self.grid_cell_size-1), (self.grid_cell_size, self.grid_cell_size-1)))
                        elif dx == 1 and dy == 0:  # Right
                            borders.append(((self.grid_cell_size-1, 0), (self.grid_cell_size-1, self.grid_cell_size)))
                        elif dx == 0 and dy == -1:  # Top
                            borders.append(((0, 0), (self.grid_cell_size, 0)))
                        elif dx == -1 and dy == 0:  # Left
                            borders.append(((0, 0), (0, self.grid_cell_size)))
                
                # Draw borders
                for (x1, y1), (x2, y2) in borders:
                    pygame.draw.line(self.screen, (0, 0, 0, 200), 
                                     (screen_x + x1, screen_y + y1),
                                     (screen_x + x2, screen_y + y2), 2)
        
        # Draw cities
        if self.show_cities:
            for civ in self.world.civilizations:
                if hasattr(civ, 'has_collapsed') and civ.has_collapsed:
                    continue
                    
                civ_color = self._get_civilization_color(civ)
                
                for pos, city in civ.cities.items():
                    x, y = pos
                    screen_x = x * self.grid_cell_size + self.offset_x + self.grid_cell_size // 2
                    screen_y = y * self.grid_cell_size + self.offset_y + self.grid_cell_size // 2
                    
                    # Draw city dot (white circle with black outline)
                    city_radius = min(8, max(4, int(math.log(city["population"] + 1, 10) * 2)))
                    pygame.draw.circle(self.screen, (255, 255, 255), (screen_x, screen_y), city_radius)
                    pygame.draw.circle(self.screen, civ_color, (screen_x, screen_y), city_radius, 2)
                    
                    # Draw city name if showing labels or this city is selected
                    if self.show_all_labels or (self.selected_position == pos):
                        name_font = pygame.freetype.SysFont("Arial", 12)
                        name_surface, name_rect = name_font.render(city["name"], (0, 0, 0))
                        
                        # Position name above city
                        name_x = screen_x - name_rect.width // 2
                        name_y = screen_y - name_rect.height - 10
                        
                        # Draw background for better visibility
                        bg_rect = pygame.Rect(name_x - 2, name_y - 2, name_rect.width + 4, name_rect.height + 4)
                        pygame.draw.rect(self.screen, (255, 255, 255, 180), bg_rect)
                        pygame.draw.rect(self.screen, (0, 0, 0), bg_rect, 1)
                        
                        self.screen.blit(name_surface, (name_x, name_y))
        
        # Draw highlighted position if any
        if self.selected_position:
            x, y = self.selected_position
            screen_x = x * self.grid_cell_size + self.offset_x
            screen_y = y * self.grid_cell_size + self.offset_y
            
            # Create pulsing highlight effect
            highlight_alpha = int(128 + 127 * abs(math.sin(self.highlight_timer * 5)))
            highlight_surface = pygame.Surface((self.grid_cell_size, self.grid_cell_size), pygame.SRCALPHA)
            highlight_surface.fill((255, 255, 255, highlight_alpha // 2))
            self.screen.blit(highlight_surface, (screen_x, screen_y))
            
            # Draw selection border
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           pygame.Rect(screen_x, screen_y, self.grid_cell_size, self.grid_cell_size), 2)
            
        # Update highlight animation
        self.highlight_timer -= 0.016  # Assuming 60fps
        if self.highlight_timer <= 0:
            self.highlight_timer = 0.3
            self.highlight_direction *= -1

    def _render_left_panel(self):
        """Render left panel with buttons and controls"""
        # Draw left panel background with gradient similar to main menu
        panel_rect = pygame.Rect(0, 0, self.left_panel_width, self.height)
        
        # Create gradient background
        panel_surface = pygame.Surface((self.left_panel_width, self.height))
        for y in range(self.height):
            r = int(10 + (y / self.height) * 15)
            g = int(20 + (y / self.height) * 20)
            b = int(50 + (y / self.height) * 30)
            pygame.draw.line(panel_surface, (r, g, b), (0, y), (self.left_panel_width, y))
        
        # Blit the gradient background
        self.screen.blit(panel_surface, (0, 0))
        
        # Add border with glow effect
        pygame.draw.rect(self.screen, (100, 150, 250, 150), panel_rect, 1)
        
        # Title with shadow
        title_shadow_pos = (11, 11)
        title_pos = (10, 10)
        self.font_large.render_to(
            self.screen, 
            title_shadow_pos,
            "",
            (0, 0, 0)
        )
        self.font_large.render_to(
            self.screen, 
            title_pos,
            "",
            (255, 255, 255)
        )
        
        # Note: The actual buttons are managed by the Controls class
        # This space is reserved for them

    def _render_side_panel(self):
        """Render side panel with civilization list and controls"""
        # Draw side panel background with gradient similar to main menu
        panel_rect = pygame.Rect(self.width - self.side_panel_width, 0, 
                                self.side_panel_width, self.height)
        
        # Create gradient background
        panel_surface = pygame.Surface((self.side_panel_width, self.height))
        for y in range(self.height):
            r = int(15 + (y / self.height) * 15)
            g = int(25 + (y / self.height) * 20)
            b = int(60 + (y / self.height) * 30)
            pygame.draw.line(panel_surface, (r, g, b), (0, y), (self.side_panel_width, y))
        
        # Blit the gradient background
        self.screen.blit(panel_surface, (self.width - self.side_panel_width, 0))
        
        # Add border with glow effect
        pygame.draw.rect(self.screen, (100, 150, 250, 150), panel_rect, 1)
        
        # Draw title with shadow
        title_shadow_pos = (self.width - self.side_panel_width + 11, 11)
        title_pos = (self.width - self.side_panel_width + 10, 10)
        self.font_large.render_to(
            self.screen, 
            title_shadow_pos,
            "Civilization Info",
            (0, 0, 0)
        )
        self.font_large.render_to(
            self.screen, 
            title_pos,
            "Civilization Info",
            (255, 255, 255)
        )
        
        # If civilization list is showing, render it
        if self.showing_civ_list:
            self._render_civilization_list()
        
        # If a civilization is selected, show detailed info
        elif self.selected_civilization:
            self._render_civilization_info()
        
        # Otherwise show a hint
        else:
            self.font.render_to(
                self.screen,
                (self.width - self.side_panel_width + 10, 50),
                "Click on the map to select",
                (220, 220, 255)
            )
            self.font.render_to(
                self.screen,
                (self.width - self.side_panel_width + 10, 70),
                "a civilization or press C",
                (220, 220, 255)
            )
            self.font.render_to(
                self.screen,
                (self.width - self.side_panel_width + 10, 90),
                "to show civilization list.",
                (220, 220, 255)
            )
            
    def _render_bottom_panel(self):
        """Render bottom panel with position information"""
        # Draw bottom panel background with gradient similar to main menu
        panel_rect = pygame.Rect(self.left_panel_width, self.height - self.bottom_panel_height, 
                                self.width - self.left_panel_width - self.side_panel_width, self.bottom_panel_height)
        
        # Create gradient background
        panel_surface = pygame.Surface((panel_rect.width, panel_rect.height))
        for y in range(panel_rect.height):
            r = int(15 + (y / panel_rect.height) * 15)
            g = int(25 + (y / panel_rect.height) * 20)
            b = int(60 + (y / panel_rect.height) * 30)
            pygame.draw.line(panel_surface, (r, g, b), (0, y), (panel_rect.width, y))
        
        # Blit the gradient background
        self.screen.blit(panel_surface, (panel_rect.x, panel_rect.y))
        
        # Add border with glow effect
        pygame.draw.rect(self.screen, (100, 150, 250, 150), panel_rect, 1)
        
        # If a position is selected, show info about it
        if self.selected_position:
            self._render_position_info()
        else:
            # Show a hint when nothing is selected
            self.font.render_to(
                self.screen,
                (self.left_panel_width + 10, self.height - self.bottom_panel_height + 10),
                "Click on the map to select a tile or civilization",
                (220, 220, 255)
            )

    def _render_civilization_label(self, civ, civ_index):
        """Render civilization name label"""
        # Find a good position for the label (center of territory)
        sum_x = sum(pos[0] for pos in civ.territory)
        sum_y = sum(pos[1] for pos in civ.territory)
        avg_x = sum_x // len(civ.territory)
        avg_y = sum_y // len(civ.territory)
        
        label_x = self.offset_x + avg_x * self.grid_cell_size
        label_y = self.offset_y + avg_y * self.grid_cell_size - 25  # Position further above cities/icons to avoid overlap
        
        # Get color
        color = self.civilization_colors[civ_index % len(self.civilization_colors)]
        
        # Check if this civilization is protected or selected
        is_protected = hasattr(civ, 'protected_until_tick')
        is_selected = (civ == self.selected_civilization)
        
        # Only show labels for larger civilizations or when selected, protected, or show_all_labels is true
        if len(civ.territory) > 10 or is_selected or is_protected or self.show_all_labels:
            # Draw background for label
            label_width = min(120, len(civ.name) * 6 + 10)
            if is_protected:
                # Add width for "Protected" text
                label_width += 20
            
            label_rect = pygame.Rect(
                label_x - label_width // 2,
                label_y - 20,
                label_width,
                20
            )
            
            # Semi-transparent background for better visibility
            label_bg = pygame.Surface((label_width, 20), pygame.SRCALPHA)
            label_bg.fill((0, 0, 0, 180))  # Semi-transparent black
            self.screen.blit(label_bg, (label_x - label_width // 2, label_y - 20))
            
            if is_protected:
                # Gold/white border for protected civilizations
                pygame.draw.rect(self.screen, (255, 215, 0), label_rect, 2)
            else:
                pygame.draw.rect(self.screen, color, label_rect, 1)
            
            # Draw label
            label_text = civ.name
            if is_protected:
                label_text += " ⛨"  # Protection symbol
            
            self.font.render_to(
                self.screen,
                (label_x - label_width // 2 + 5, label_y - 17),
                label_text,
                (255, 255, 255) if is_protected else color
            )

    def _render_civilization_list(self):
        """Render a list of all civilizations"""
        # Render in the side panel
        list_start_y = 50
        list_width = self.side_panel_width - 20
        
        # Title
        self.font.render_to(
            self.screen, 
            (self.width - self.side_panel_width + 10, list_start_y), 
            "Active Civilizations", 
            (255, 255, 255)
        )
        
        # Counter
        total = len(self.world.civilizations)
        self.font.render_to(
            self.screen,
            (self.width - self.side_panel_width + 10, list_start_y + 25),
            f"Total: {total} civilization{'s' if total != 1 else ''}",
            (200, 200, 200)
        )
        
        # If no civilizations, show a message
        if total == 0:
            self.font.render_to(
                self.screen,
                (self.width - self.side_panel_width + 10, list_start_y + 55),
                "No civilizations yet!",
                (255, 100, 100)
            )
            self.font.render_to(
                self.screen,
                (self.width - self.side_panel_width + 10, list_start_y + 75),
                "Use God Mode to add some.",
                (200, 200, 200)
            )
            return
        
        # Calculate how many civilizations can fit in the panel
        max_visible = min(total, (self.height - self.bottom_panel_height - list_start_y - 40) // 70)
        
        # List civilizations with more details
        for i in range(max_visible):
            civ = self.world.civilizations[i]
            color = self.civilization_colors[i % len(self.civilization_colors)]
            
            y_pos = list_start_y + 55 + i * 70
            
            # Highlight if this is the selected civilization
            if civ == self.selected_civilization:
                highlight_rect = pygame.Rect(
                    self.width - self.side_panel_width + 5, 
                    y_pos - 5, 
                    list_width, 
                    65
                )
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    highlight_rect
                )
                pygame.draw.rect(
                    self.screen,
                    color,
                    highlight_rect,
                    1
                )
            
            # Draw color indicator
            pygame.draw.rect(
                self.screen,
                color,
                (self.width - self.side_panel_width + 10, y_pos, 15, 15)
            )
            
            # Draw civilization name and basic info
            civ_text = f"{civ.name}"
            self.font.render_to(
                self.screen, 
                (self.width - self.side_panel_width + 30, y_pos), 
                civ_text, 
                (255, 255, 255)
            )
            
            # Format population with commas and handle large numbers
            if civ.population > 1000000000:
                pop_text = f"{civ.population/1000000000:.1f}B"
            elif civ.population > 1000000:
                pop_text = f"{civ.population/1000000:.1f}M"
            elif civ.population > 1000:
                pop_text = f"{civ.population/1000:.1f}K"
            else:
                pop_text = f"{civ.population}"
                
            # Population and territory
            pop_text = f"Pop: {pop_text} | Territory: {len(civ.territory)}"
            self.font_small.render_to(
                self.screen, 
                (self.width - self.side_panel_width + 30, y_pos + 20), 
                pop_text, 
                (200, 200, 200)
            )
            
            # Technology and resources
            tech_text = f"Tech: {civ.technology:.1f} | Cities: {len(civ.cities)}"
            self.font_small.render_to(
                self.screen, 
                (self.width - self.side_panel_width + 30, y_pos + 35), 
                tech_text, 
                (200, 200, 200)
            )
            
            # Traits
            if civ.traits:
                traits_text = "Traits: " + ", ".join(civ.traits[:2])
                if len(civ.traits) > 2:
                    traits_text += "..."
                self.font_small.render_to(
                    self.screen, 
                    (self.width - self.side_panel_width + 30, y_pos + 50), 
                    traits_text, 
                    (180, 180, 220)
                )
        
        # If there are more civilizations than can fit, show a message
        if total > max_visible:
            self.font_small.render_to(
                self.screen,
                (self.width - self.side_panel_width + 10, list_start_y + 55 + max_visible * 70),
                f"+ {total - max_visible} more...",
                (200, 200, 200)
            )

    def _render_civilization_info(self):
        """Render information about the selected civilization"""
        civ = self.selected_civilization
        
        # Start position for rendering
        start_y = 50
        start_x = self.width - self.side_panel_width + 10
        
        # Civilization name and color
        civ_index = self.world.civilizations.index(civ)
        color = self.civilization_colors[civ_index % len(self.civilization_colors)]
        
        # Draw color box
        pygame.draw.rect(
            self.screen,
            color,
            (start_x, start_y, 15, 15)
        )
        
        # Civilization name
        self.font_large.render_to(
            self.screen, 
            (start_x + 25, start_y), 
            civ.name, 
            (255, 255, 255)
        )
        
        # Basic info
        start_y += 30
        
        # Format population with commas and handle large numbers
        if civ.population > 1000000000:
            pop_text = f"{civ.population/1000000000:.1f} billion"
        elif civ.population > 1000000:
            pop_text = f"{civ.population/1000000:.1f} million"
        elif civ.population > 1000:
            pop_text = f"{civ.population/1000:.1f} thousand"
        else:
            pop_text = f"{civ.population}"
            
        basic_info = f"Population: {pop_text}"
        self.font.render_to(self.screen, (start_x, start_y), basic_info, (255, 255, 255))
        
        start_y += 20
        territory_info = f"Territory: {len(civ.territory)} tiles | Cities: {len(civ.cities)}"
        self.font.render_to(self.screen, (start_x, start_y), territory_info, (255, 255, 255))
        
        start_y += 20
        tech_info = f"Technology: {civ.technology:.1f}"
        self.font.render_to(self.screen, (start_x, start_y), tech_info, (255, 255, 255))
        
        # Traits and belief system
        start_y += 30
        traits_text = f"Traits:"
        self.font.render_to(self.screen, (start_x, start_y), traits_text, (255, 255, 255))
        
        start_y += 20
        for trait in civ.traits:
            self.font_small.render_to(self.screen, (start_x + 10, start_y), trait, (200, 200, 200))
            start_y += 15
        
        start_y += 15
        belief_text = f"Belief System:"
        self.font.render_to(self.screen, (start_x, start_y), belief_text, (255, 255, 255))
        
        start_y += 20
        self.font_small.render_to(
            self.screen, 
            (start_x + 10, start_y), 
            civ.belief_system.name, 
            (200, 200, 200)
        )
        
        start_y += 15
        self.font_small.render_to(
            self.screen, 
            (start_x + 10, start_y), 
            f"Stance: {civ.belief_system.foreign_stance}", 
            (200, 200, 200)
        )
        
        # Resources
        start_y += 30
        resources_text = "Resources:"
        self.font.render_to(self.screen, (start_x, start_y), resources_text, (255, 255, 255))
        
        start_y += 20
        for resource, amount in civ.resources.items():
            resource_text = f"{resource}: {amount:.1f}"
            self.font_small.render_to(
                self.screen, 
                (start_x + 10, start_y), 
                resource_text, 
                (200, 200, 200)
            )
            start_y += 15
            
        # Draw "God Mode Actions Available" if god mode is active
        if self.god_mode_active:
            start_y += 20
            self.font.render_to(
                self.screen,
                (start_x, start_y),
                "God Mode Actions Available!",
                (255, 200, 0)
            )

    def show_notification(self, title, message, civ=None):
        """Show a notification popup"""
        self.event_notification = {
            "title": title,
            "message": message,
            "civ": civ,
            "time": 300  # Show for 300 frames (5 seconds at 60 fps)
        }
        
    def _render_notification(self):
        """Render the event notification popup"""
        if not self.event_notification:
            return
            
        # Update timer
        self.event_notification["time"] -= 1
        if self.event_notification["time"] <= 0:
            self.event_notification = None
            return
        
        # Get dimensions
        w, h = self.width, self.height
        popup_width = 500
        popup_height = 200
        
        # Position in center of screen
        popup_x = (w - popup_width) // 2
        popup_y = (h - popup_height) // 2
        
        # Draw popup background with transparency
        popup_surface = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
        popup_surface.fill((30, 30, 30, 230))  # Dark, semi-transparent background
        
        # Draw border
        border_color = (150, 150, 150)
        if self.event_notification["civ"]:
            # Check if civilization still exists before trying to get its color
            civ = self.event_notification["civ"]
            try:
                if civ in self.world.civilizations:
                    civ_index = self.world.civilizations.index(civ)
                    border_color = self.civilization_colors[civ_index % len(self.civilization_colors)]
                else:
                    # Civilization no longer exists (likely collapsed), use a default color
                    border_color = (200, 100, 100)  # Reddish color for collapsed civs
            except ValueError:
                # Handle case where civ can't be found in list
                border_color = (200, 100, 100)
        
        pygame.draw.rect(popup_surface, border_color, (0, 0, popup_width, popup_height), 3)
        
        # Draw title
        title_font = pygame.freetype.SysFont("Arial", 24)
        title_font.render_to(
            popup_surface,
            (20, 20),
            self.event_notification["title"],
            (255, 255, 255)
        )
        
        # Draw underline
        pygame.draw.line(
            popup_surface,
            border_color,
            (20, 50),
            (popup_width - 20, 50),
            2
        )
        
        # Draw message with word wrap
        message_font = pygame.freetype.SysFont("Arial", 18)
        message = self.event_notification["message"]
        
        # Simple word wrap
        words = message.split(' ')
        lines = []
        current_line = words[0]
        
        for word in words[1:]:
            test_line = current_line + ' ' + word
            text_width, _ = message_font.get_rect(test_line)[2:4]
            
            if text_width < popup_width - 40:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        
        # Render each line
        for i, line in enumerate(lines):
            message_font.render_to(
                popup_surface,
                (20, 70 + i * 25),
                line,
                (220, 220, 220)
            )
        
        # Draw "Click to dismiss" message
        dismiss_font = pygame.freetype.SysFont("Arial", 14)
        dismiss_font.render_to(
            popup_surface,
            (popup_width - 150, popup_height - 30),
            "Click to dismiss",
            (180, 180, 180)
        )
        
        # Blit the popup to the screen
        self.screen.blit(popup_surface, (popup_x, popup_y))

    def _render_position_info(self):
        """Render information about the selected position"""
        x, y = self.selected_position
        terrain = self.world.get_terrain_at((x, y))
        terrain_names = ["Water", "Land", "Mountain", "Forest", "Desert"]
        terrain_name = terrain_names[terrain] if terrain < len(terrain_names) else "Unknown"
        
        # Get resource info if available
        resource_text = ""
        if (x, y) in self.world.resources:
            resources = self.world.resources[(x, y)]
            resource_text = " | Resources: " + ", ".join(f"{k}: {v:.2f}" for k, v in resources.items())
        
        # Get civilizations at this position
        civs_at_pos = self.world.get_civilizations_at((x, y))
        civ_text = ""
        city_info = None
        
        if civs_at_pos:
            civ_text = " | Owner: " + civs_at_pos[0].name
            
            # Check if this is a specialized location
            for civ in civs_at_pos:
                if (x, y) in civ.cities:
                    city_info = civ.cities[(x, y)]
                    location_type = self._determine_location_type(civ.traits, city_info["population"])
                    
                    civ_text += f" | {location_type.replace('_', ' ').title()}: {city_info['name']} (Pop: {city_info['population']})"
                    break
        
        # Draw position info - adjusted for new panel position
        pos_x = self.left_panel_width + 10
        pos_y = self.height - self.bottom_panel_height + 10
        text = f"Position: ({x}, {y}) | Terrain: {terrain_name}{resource_text}"
        self.font.render_to(self.screen, (pos_x, pos_y), text, (255, 255, 255))
        
        # Continue with owner info on next line if needed
        if civ_text:
            self.font.render_to(self.screen, (pos_x, pos_y + 20), civ_text, (255, 255, 255))
        
        # If it's a city, show additional details
        if city_info:
            details = f"City Details - Name: {city_info['name']} | Population: {city_info['population']}"
            self.font.render_to(self.screen, (pos_x, pos_y + 40), details, (220, 220, 255))
            
            # Additional city details if available
            if len(civ_text) > 0:
                civ = civs_at_pos[0]
                city_traits = f"City Owner Traits: {', '.join(civ.traits)}"
                self.font.render_to(self.screen, (pos_x, pos_y + 60), city_traits, (200, 200, 255))
                
                belief_text = f"Belief System: {civ.belief_system.name} ({civ.belief_system.foreign_stance})"
                self.font.render_to(self.screen, (pos_x, pos_y + 80), belief_text, (200, 200, 255))

    def check_notification_click(self, pos):
        """Check if a notification was clicked and dismiss it if so"""
        if not self.event_notification:
            return False
            
        # Get popup dimensions
        popup_width = 500
        popup_height = 200
        popup_x = (self.width - popup_width) // 2
        popup_y = (self.height - popup_height) // 2
        
        # Check if click is within popup
        popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        if popup_rect.collidepoint(pos):
            self.event_notification = None
            return True
            
        return False

    def _render_civilization_locations(self, civ, civ_index):
        """Render specialized locations for civilizations with reduced density"""
        # Get civilization traits to determine location types
        civ_traits = civ.traits
        color = self.civilization_colors[civ_index % len(self.civilization_colors)]
        
        # Limit number of locations to reduce clutter
        # Use a deterministic approach based on territory position and city population
        visible_locations = {}
        
        # First pass - identify potential locations
        for pos, city_info in civ.cities.items():
            x, y = pos
            population = city_info["population"]
            
            # Skip if population too small to show anything
            if population < 50:
                continue
                
            # Determine the type of location based on traits and population
            location_type = self._determine_location_type(civ_traits, population)
            
            # Store location info for second pass
            visible_locations[pos] = {
                "type": location_type,
                "population": population,
                "name": city_info["name"]
            }
        
        # Second pass - reduce density (show ~1 location per 25 territory tiles)
        max_locations = max(3, len(civ.territory) // 25)  # At least 3, or 1 per 25 tiles
        
        # Sort by population to prioritize larger settlements
        sorted_locations = sorted(
            visible_locations.items(), 
            key=lambda x: x[1]["population"], 
            reverse=True
        )
        
        # Take top N locations
        visible_locations = dict(sorted_locations[:max_locations])
        
        # Now render the visible locations
        for pos, location_info in visible_locations.items():
            x, y = pos
            screen_x = self.offset_x + x * self.grid_cell_size + self.grid_cell_size // 2
            screen_y = self.offset_y + y * self.grid_cell_size + self.grid_cell_size // 2
            
            location_type = location_info["type"]
            location_symbol = self.location_types[location_type]["symbol"]
            
            # Draw the symbol in white with colored border
            font_size = max(12, min(int(math.log10(location_info["population"]) * 3), self.grid_cell_size))
            symbol_font = pygame.freetype.SysFont("Arial", font_size)
            
            text_surf, text_rect = symbol_font.render(location_symbol, (255, 255, 255))
            text_rect.center = (screen_x, screen_y)
            
            # Add a shadow for better visibility
            shadow_surf, shadow_rect = symbol_font.render(location_symbol, (0, 0, 0))
            shadow_rect.center = (screen_x + 1, screen_y + 1)
            self.screen.blit(shadow_surf, shadow_rect)
            
            # Then draw the actual symbol
            self.screen.blit(text_surf, text_rect)
            
            # Draw a border around the symbol using the civilization's color
            pygame.draw.circle(
                self.screen,
                color,
                (screen_x, screen_y),
                font_size // 2 + 1,
                1
            )

    def _determine_location_type(self, civ_traits, population):
        """Determine the type of location based on civilization traits and population"""
        # Check for trait-specific locations
        for loc_type, props in self.location_types.items():
            if "traits" in props and population >= props["min_pop"]:
                if any(trait in civ_traits for trait in props["traits"]):
                    return loc_type
        
        # Fallback to basic city types based on population
        if population >= 1000:
            return "capital"
        elif population >= 100:
            return "city"
        else:
            return "city"  # Small village

    def toggle_city_visibility(self):
        """Toggle whether cities are visible on the map"""
        self.show_cities = not self.show_cities
        return self.show_cities
        
    def toggle_labels(self):
        """Toggle whether all labels are visible"""
        self.show_all_labels = not self.show_all_labels
        return self.show_all_labels
        
    def toggle_civilization_list(self):
        """Toggle civilization list visibility"""
        self.showing_civ_list = not self.showing_civ_list
        return self.showing_civ_list
        
    def set_god_mode(self, active):
        """Set whether God Mode is active"""
        self.god_mode_active = active
        return self.god_mode_active

    def set_selected_position(self, screen_pos):
        """Set the selected position based on screen coordinates
        
        Args:
            screen_pos: (x, y) tuple of screen coordinates
            
        Returns:
            bool: True if a position was selected, False otherwise
        """
        # Convert screen coordinates to grid coordinates
        x, y = screen_pos
        
        # Check if click is within the map area
        map_rect = pygame.Rect(
            self.offset_x, 
            self.offset_y, 
            self.world.width * self.grid_cell_size,
            self.world.height * self.grid_cell_size
        )
        
        if not map_rect.collidepoint(x, y):
            return False
            
        # Calculate grid coordinates
        grid_x = (x - self.offset_x) // self.grid_cell_size
        grid_y = (y - self.offset_y) // self.grid_cell_size
        
        # Ensure we're within the world bounds
        if 0 <= grid_x < self.world.width and 0 <= grid_y < self.world.height:
            # Set the selected position
            self.selected_position = (grid_x, grid_y)
            
            # Check if there's a civilization at this position
            civs_at_pos = self.world.get_civilizations_at(self.selected_position)
            self.selected_civilization = civs_at_pos[0] if civs_at_pos else None
            
            return True
            
        return False 

    def handle_civ_detail_scroll(self, event):
        """Handle mouse wheel scroll and scrollbar interaction for the civ details popup."""
        if not self.showing_civ_details or not self.detail_surface or not self.detail_rect:
            return False

        mouse_pos = pygame.mouse.get_pos()
        # Convert mouse_pos to be relative to the detail_surface for easier calculations
        relative_mouse_pos = (mouse_pos[0] - self.detail_rect.left, mouse_pos[1] - self.detail_rect.top)

        # Check if the mouse is even within the bounds of the popup
        # Otherwise, wheel events outside shouldn't scroll it.
        mouse_over_popup = self.detail_rect.collidepoint(mouse_pos)

        # Mouse Wheel Scrolling
        if event.type == pygame.MOUSEWHEEL and mouse_over_popup:
            if self.detail_content_height > self.detail_surface.get_height(): # Only scroll if content exceeds view
                scroll_amount = -event.y * 40  # event.y is 1 for up, -1 for down; 40px per tick
                self.detail_scroll_y += scroll_amount
                self.detail_scroll_y = max(0, min(self.detail_scroll_y, self.detail_max_scroll_y))
                return True # Event handled

        # Scrollbar Interaction
        if self.scroll_bar_rect and self.scroll_thumb_rect: # Ensure scrollbar elements exist
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.scroll_thumb_rect.collidepoint(relative_mouse_pos):
                    self.dragging_scrollbar = True
                    self.drag_offset_y = relative_mouse_pos[1] - self.scroll_thumb_rect.top
                    return True # Event handled
                elif self.scroll_bar_rect.collidepoint(relative_mouse_pos):
                    # Clicked on the track, not the thumb
                    popup_view_height = self.detail_surface.get_height()
                    content_height = self.detail_content_height
                    thumb_h = max(40, int(self.scroll_bar_rect.height * (popup_view_height / content_height)))
                    track_clickable_height = self.scroll_bar_rect.height - thumb_h
                    
                    # Position of click relative to the top of the scrollbar track
                    click_on_track_y = relative_mouse_pos[1] - self.scroll_bar_rect.top
                    
                    if track_clickable_height > 0:
                        scroll_ratio = (click_on_track_y - thumb_h / 2) / track_clickable_height
                        scroll_ratio = max(0, min(1, scroll_ratio))
                        self.detail_scroll_y = scroll_ratio * self.detail_max_scroll_y
                    return True # Event handled

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging_scrollbar:
                    self.dragging_scrollbar = False
                    return True # Event handled

            elif event.type == pygame.MOUSEMOTION and self.dragging_scrollbar:
                popup_view_height = self.detail_surface.get_height()
                content_height = self.detail_content_height
                thumb_h = max(40, int(self.scroll_bar_rect.height * (popup_view_height / content_height)))
                track_clickable_height = self.scroll_bar_rect.height - thumb_h

                if track_clickable_height > 0:
                    # Mouse position relative to the scrollbar track's top
                    mouse_y_on_track = relative_mouse_pos[1] - self.scroll_bar_rect.top - self.drag_offset_y
                    scroll_ratio = mouse_y_on_track / track_clickable_height
                    scroll_ratio = max(0, min(1, scroll_ratio))
                    self.detail_scroll_y = scroll_ratio * self.detail_max_scroll_y
                return True # Event handled
        
        # If the event was a click within the popup but not handled by scroll elements, still consume it
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_over_popup:
            return True
            
        return False # Event not handled by this function

    def _draw_civ_details(self):
        """Draw detailed information about selected civilization with scrolling."""
        if not self.detail_civ or not hasattr(self.detail_civ, 'name'):
            self.showing_civ_details = False
            return
        
        # Check for simulation reference
        if not self.simulation:
            print("Error: Simulation not set in renderer, cannot generate lore")
            self.showing_civ_details = False
            return
        
        # Import lore generator with error handling
        try:
            from src.lore import get_detailed_civilization_info
        except ImportError as e:
            print(f"Error importing lore module: {e}")
            get_detailed_civilization_info = None
        
        screen_width, screen_height = self.screen.get_size()
        
        # Create detail surface if needed
        if not self.detail_surface or self.detail_surface.get_width() != int(screen_width * 0.7):
            popup_width = int(screen_width * 0.7)
            popup_height = int(screen_height * 0.8)
            self.detail_surface = pygame.Surface((popup_width, popup_height))
            self.detail_rect = pygame.Rect(
                (screen_width - popup_width) // 2,
                (screen_height - popup_height) // 2,
                popup_width,
                popup_height
            )
            
            # Create close button
            close_button_size = 30
            self.detail_close_button = pygame.Rect(
                popup_width - close_button_size - 10,
                10,
                close_button_size,
                close_button_size
            )
            
            # Reset scroll position
            self.detail_scroll_y = 0
        
        # Fill with solid deep blue background (no transparency)
        primary_bg_color = (20, 35, 65)
        self.detail_surface.fill(primary_bg_color)
        
        # Add subtle gradient at the top
        for y in range(40):
            gradient_strength = 40 - y
            if gradient_strength > 0:
                gradient_color = (
                    min(255, primary_bg_color[0] + gradient_strength),
                    min(255, primary_bg_color[1] + gradient_strength),
                    min(255, primary_bg_color[2] + gradient_strength*2)
                )
                pygame.draw.line(self.detail_surface, gradient_color,
                               (0, y), (self.detail_surface.get_width(), y))
        
        # Draw an elegant border
        border_color = (80, 120, 200)
        pygame.draw.rect(self.detail_surface, border_color,
                       (0, 0, self.detail_surface.get_width(), self.detail_surface.get_height()),
                       2, border_radius=12)
        
        # Draw stylish close button
        close_button_color = (40, 60, 100)
        close_hover_color = (60, 100, 180)
        
        # Check if mouse is over close button
        mouse_pos = pygame.mouse.get_pos()
        rel_mouse_pos = (mouse_pos[0] - self.detail_rect.x, mouse_pos[1] - self.detail_rect.y)
        close_button_hovered = self.detail_close_button.collidepoint(rel_mouse_pos)
        
        # Draw close button background with glow effect when hovered
        pygame.draw.rect(self.detail_surface, 
                       close_hover_color if close_button_hovered else close_button_color,
                       self.detail_close_button, border_radius=8)
        
        # Add subtle highlight to close button
        if close_button_hovered:
            # Add glow effect
            for i in range(2):
                glow_rect = self.detail_close_button.inflate(i*2, i*2)
                pygame.draw.rect(self.detail_surface, (100, 180, 255),
                               glow_rect, 1, border_radius=8)
        
        # Draw X with shadow for close button
        x_color = (240, 240, 255)
        x_shadow = (0, 0, 0)
        
        # Shadow for X
        pygame.draw.line(
            self.detail_surface,
            x_shadow,
            (self.detail_close_button.left + 6, self.detail_close_button.top + 6),
            (self.detail_close_button.right - 6, self.detail_close_button.bottom - 6),
            3
        )
        pygame.draw.line(
            self.detail_surface,
            x_shadow,
            (self.detail_close_button.right - 6, self.detail_close_button.top + 6),
            (self.detail_close_button.left + 6, self.detail_close_button.bottom - 6),
            3
        )
        
        # Main X
        pygame.draw.line(
            self.detail_surface,
            x_color,
            (self.detail_close_button.left + 5, self.detail_close_button.top + 5),
            (self.detail_close_button.right - 5, self.detail_close_button.bottom - 5),
            2
        )
        pygame.draw.line(
            self.detail_surface,
            x_color,
            (self.detail_close_button.right - 5, self.detail_close_button.top + 5),
            (self.detail_close_button.left + 5, self.detail_close_button.bottom - 5),
            2
        )
        
        # Set up fonts - using more modern fonts
        title_font = pygame.freetype.SysFont("Segoe UI", 32, bold=True)
        header_font = pygame.freetype.SysFont("Segoe UI", 22, bold=True)
        text_font = pygame.freetype.SysFont("Segoe UI", 16)
        
        # Draw title with shadow and underline
        title_shadow, _ = title_font.render(f"{self.detail_civ.name}", (0, 0, 0, 100))
        title_text, _ = title_font.render(f"{self.detail_civ.name}", (255, 255, 255))
        
        # Add shadow effect
        self.detail_surface.blit(title_shadow, (22, 22))
        self.detail_surface.blit(title_text, (20, 20))
        
        # Add decorative underline
        pygame.draw.line(
            self.detail_surface,
            (100, 180, 255, 180),
            (20, 60),
            (min(300, 20 + title_text.get_width() + 20), 60),
            2
        )
        
        # Draw basic info section
        y_pos = 70  # Start position for content
        
        # Draw basic statistics with an enhanced look
        header_shadow, _ = header_font.render("Basic Information", (0, 0, 0, 80))
        header_text, _ = header_font.render("Basic Information", (200, 220, 255))
        
        self.detail_surface.blit(header_shadow, (22, y_pos - self.detail_scroll_y + 2))
        self.detail_surface.blit(header_text, (20, y_pos - self.detail_scroll_y))
        y_pos += header_text.get_height() + 10
        
        # Create a subtle background box for basic info
        # We'll calculate the height of this box dynamically based on wrapped text content
        info_box_content_start_y = y_pos + 10 # 10px padding inside the box
        current_info_box_y = info_box_content_start_y
        
        basic_info_items = [
            f"Age: {self.detail_civ.age} years",
            f"Population: {self.detail_civ.population:,}",
            f"Territory: {len(self.detail_civ.territory)} tiles",
            f"Cities: {len(self.detail_civ.cities)}",
            f"Technology Level: {self.detail_civ.technology:.1f}",
            f"Traits: {', '.join(self.detail_civ.traits)}",
            f"Belief System: {self.detail_civ.belief_system.name} ({self.detail_civ.belief_system.foreign_stance})",
        ]
        
        max_info_width = self.detail_surface.get_width() - 80 # 40px padding on each side of the info text itself
        
        for item_text in basic_info_items:
            wrapped_lines = self._wrap_text(item_text, text_font, max_info_width)
            for line in wrapped_lines:
                text_shadow, _ = text_font.render(line, (0, 0, 0, 60))
                text_surface, line_rect = text_font.render(line, (220, 240, 255))
                
                # Check if the line is visible before blitting
                if current_info_box_y - self.detail_scroll_y > 0 and \
                   current_info_box_y - self.detail_scroll_y < self.detail_surface.get_height() - header_text.get_height(): # ensure not drawing over footer/next section
                    self.detail_surface.blit(text_shadow, (42, current_info_box_y - self.detail_scroll_y + 1))
                    self.detail_surface.blit(text_surface, (40, current_info_box_y - self.detail_scroll_y))
                
                current_info_box_y += line_rect.height + 3 # Small spacing between lines
            current_info_box_y += 2 # Extra spacing between items
        
        info_box_height = current_info_box_y - info_box_content_start_y + 10 # Add bottom padding
        info_box_rect = pygame.Rect(20, info_box_content_start_y -10 , self.detail_surface.get_width() - 40, info_box_height)
        pygame.draw.rect(self.detail_surface, (30, 45, 75, 160), info_box_rect, border_radius=8)
        pygame.draw.rect(self.detail_surface, (60, 100, 180, 100), info_box_rect, 1, border_radius=8)
        
        # Redraw the text on top of the now-drawn box (if visible)
        current_info_box_y = info_box_content_start_y # Reset y for redrawing text
        for item_text in basic_info_items:
            wrapped_lines = self._wrap_text(item_text, text_font, max_info_width)
            for line in wrapped_lines:
                text_shadow, _ = text_font.render(line, (0, 0, 0, 60))
                text_surface, line_rect = text_font.render(line, (220, 240, 255))
                
                # Check if the line is visible before blitting
                # Adjusted visibility check relative to the drawn info_box_rect top and bottom
                line_abs_y_on_surface = current_info_box_y - self.detail_scroll_y
                if line_abs_y_on_surface + line_rect.height > info_box_rect.top - self.detail_scroll_y and \
                   line_abs_y_on_surface < info_box_rect.bottom - self.detail_scroll_y and \
                   line_abs_y_on_surface > 0 and line_abs_y_on_surface < self.detail_surface.get_height() - text_font.get_sized_height():
                    self.detail_surface.blit(text_shadow, (42, line_abs_y_on_surface + 1))
                    self.detail_surface.blit(text_surface, (40, line_abs_y_on_surface))
                
                current_info_box_y += line_rect.height + 3
            current_info_box_y += 2
        
        y_pos = info_box_rect.bottom + 20 # Update y_pos to be after the info box + padding
        
        # Generate lore content if available
        lore_content = {}
        try:
            if get_detailed_civilization_info:
                lore_content = get_detailed_civilization_info(self.detail_civ, self.simulation)
        except Exception as e:
            print(f"Error generating lore: {e}")
            lore_content = {
                "error": f"Could not generate lore: {str(e)[:100]}..."
            }
        
        # Draw lore content with enhanced styling
        if lore_content:
            # Function to render a section with consistent styling
            def render_section(title, content, y_position):
                # Render section header with shadow
                header_shadow, _ = header_font.render(title, (0, 0, 0, 80))
                header_text, _ = header_font.render(title, (200, 220, 255))
                
                if y_position - self.detail_scroll_y > -header_text.get_height() and y_position - self.detail_scroll_y < self.detail_surface.get_height():
                    self.detail_surface.blit(header_shadow, (22, y_position - self.detail_scroll_y + 2))
                    self.detail_surface.blit(header_text, (20, y_position - self.detail_scroll_y))
                
                section_y = y_position + header_text.get_height() + 5
                
                # Draw section underline
                if section_y - self.detail_scroll_y > 0 and section_y - self.detail_scroll_y < self.detail_surface.get_height():
                    pygame.draw.line(
                        self.detail_surface,
                        (100, 180, 255, 100),
                        (20, section_y - self.detail_scroll_y),
                        (min(280, 20 + header_text.get_width() + 40), section_y - self.detail_scroll_y),
                        1
                    )
                
                section_y += 10
                
                # Wrap and draw the text with shadow
                wrapped_text = self._wrap_text(content, text_font, self.detail_surface.get_width() - 60)
                for line in wrapped_text:
                    # Only render if would be visible
                    if section_y - self.detail_scroll_y > -text_font.get_sized_height() and section_y - self.detail_scroll_y < self.detail_surface.get_height():
                        shadow_surf, _ = text_font.render(line, (0, 0, 0, 60))
                        text_surf, _ = text_font.render(line, (220, 240, 255))
                        
                        self.detail_surface.blit(shadow_surf, (42, section_y - self.detail_scroll_y + 1))
                        self.detail_surface.blit(text_surf, (40, section_y - self.detail_scroll_y))
                    
                    section_y += text_surf.get_height() + 2
                
                return section_y + 20  # Return updated y position with spacing
            
            # Draw general lore
            if "general_lore" in lore_content:
                y_pos = render_section("Civilization History & Culture", lore_content["general_lore"], y_pos)
            
            # Draw leaders section
            if "leaders" in lore_content:
                y_pos = render_section("Notable Leaders", lore_content["leaders"], y_pos)
            
            # Draw cultural facts
            if "cultural_facts" in lore_content:
                y_pos = render_section("Cultural Practices & Innovations", lore_content["cultural_facts"], y_pos)
            
            # Draw cities section
            if "cities" in lore_content and lore_content["cities"]:
                # Section header
                header_shadow, _ = header_font.render("Major Cities", (0, 0, 0, 80))
                header_text, _ = header_font.render("Major Cities", (200, 220, 255))
                
                if y_pos - self.detail_scroll_y > -header_text.get_height() and y_pos - self.detail_scroll_y < self.detail_surface.get_height():
                    self.detail_surface.blit(header_shadow, (22, y_pos - self.detail_scroll_y + 2))
                    self.detail_surface.blit(header_text, (20, y_pos - self.detail_scroll_y))
                y_pos += header_text.get_height() + 15
                
                for city_name, city_description in lore_content["cities"].items():
                    # Check if city section would be visible before rendering
                    if y_pos - self.detail_scroll_y < self.detail_surface.get_height():
                        # Create a subtle box for each city
                        city_box_start = y_pos
                        
                        # Calculate city box height
                        city_text_height = text_font.get_sized_height() + 5
                        wrapped_city = self._wrap_text(city_description, text_font, self.detail_surface.get_width() - 80)
                        city_box_height = city_text_height + len(wrapped_city) * (text_font.get_sized_height() + 2) + 15
                        
                        # Draw city box if it would be visible
                        if (y_pos - self.detail_scroll_y + city_box_height > 0):
                            city_box = pygame.Rect(40, y_pos - self.detail_scroll_y, 
                                                  self.detail_surface.get_width() - 80, city_box_height)
                            pygame.draw.rect(self.detail_surface, (30, 45, 75, 120), city_box, border_radius=8)
                            pygame.draw.rect(self.detail_surface, (60, 100, 180, 80), city_box, 1, border_radius=8)
                            
                            # Add 5px padding
                            y_pos += 10
                            
                            # City name with shadow and slight emphasis
                            city_name_shadow, _ = text_font.render(f"{city_name}:", (0, 0, 0, 60))
                            city_name_text, _ = text_font.render(f"{city_name}:", (240, 250, 190))
                            
                            self.detail_surface.blit(city_name_shadow, (52, y_pos - self.detail_scroll_y + 1))
                            self.detail_surface.blit(city_name_text, (50, y_pos - self.detail_scroll_y))
                            y_pos += city_name_text.get_height() + 5
                            
                            # City description
                            for line in wrapped_city:
                                text_shadow, _ = text_font.render(line, (0, 0, 0, 60))
                                text_surface, _ = text_font.render(line, (210, 230, 255))
                                
                                self.detail_surface.blit(text_shadow, (62, y_pos - self.detail_scroll_y + 1))
                                self.detail_surface.blit(text_surface, (60, y_pos - self.detail_scroll_y))
                                y_pos += text_surface.get_height() + 2
                            
                            # Add padding at bottom
                            y_pos += 10
                        else:
                            # Skip this city if it wouldn't be visible
                            y_pos += city_box_height
                    else:
                        # Calculate approximate height and skip
                        y_pos += 100  # Approximate height for invisible city
        
        # Create a fading effect at the top and bottom to indicate scrolling
        if self.detail_scroll_y > 0:
            # Top fade when scrolled down
            for i in range(20):
                alpha = min(180, i * 9)
                fade_color = (*primary_bg_color[:3], alpha)
                pygame.draw.rect(self.detail_surface, fade_color, (0, i, self.detail_surface.get_width(), 1))
        
        if self.detail_scroll_y < self.detail_max_scroll_y:
            # Bottom fade when more content below
            for i in range(20):
                alpha = min(180, i * 9)
                fade_color = (*primary_bg_color[:3], alpha)
                bottom_y = self.detail_surface.get_height() - i - 1
                pygame.draw.rect(self.detail_surface, fade_color, 
                               (0, bottom_y, self.detail_surface.get_width(), 1))
        
        # Draw styled scroll bar if needed
        popup_height = self.detail_surface.get_height()
        if self.detail_content_height > popup_height:
            # Calculate the total height of the content
            self.detail_content_height = y_pos
            self.detail_max_scroll_y = max(0, self.detail_content_height - popup_height)
            
            # Calculate scrollbar track dimensions
            scrollbar_width = 8
            scrollbar_height = popup_height - 40  # 20px padding top and bottom
            scrollbar_x = self.detail_surface.get_width() - scrollbar_width - 15  # 15px from right edge
            scrollbar_y = 20  # 20px from top
            
            # Store the scroll bar rect for interaction
            self.scroll_bar_rect = pygame.Rect(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height)
            
            # Draw scrollbar track (subtle background)
            pygame.draw.rect(self.detail_surface, (40, 60, 100, 100), 
                           self.scroll_bar_rect, border_radius=4)
            
            # Calculate thumb dimensions
            thumb_height_ratio = min(1.0, popup_height / self.detail_content_height)
            thumb_height = max(40, int(scrollbar_height * thumb_height_ratio))
            
            # Calculate thumb position
            scroll_ratio = self.detail_scroll_y / max(1, self.detail_max_scroll_y)
            thumb_y = scrollbar_y + int((scrollbar_height - thumb_height) * scroll_ratio)
            
            # Store the scroll thumb rect
            self.scroll_thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
            
            # Check if mouse is over the scrollbar thumb
            mouse_pos = pygame.mouse.get_pos()
            rel_mouse_pos = (mouse_pos[0] - self.detail_rect.x, mouse_pos[1] - self.detail_rect.y)
            scrollbar_hovered = self.scroll_thumb_rect.collidepoint(rel_mouse_pos) or self.dragging_scrollbar
            
            # Draw thumb with appropriate style
            if scrollbar_hovered:
                # Glowing effect when hovered
                for i in range(2):
                    glow_rect = self.scroll_thumb_rect.inflate(i*2, i*2)
                    pygame.draw.rect(self.detail_surface, (100, 180, 255),
                                   glow_rect, border_radius=4)
                
                thumb_color = (100, 180, 255, 220)
            else:
                thumb_color = (80, 140, 220, 180)
            
            # Draw the actual thumb
            pygame.draw.rect(self.detail_surface, thumb_color, 
                           self.scroll_thumb_rect, border_radius=4)
        
        # Blit detail surface to screen
        self.screen.blit(self.detail_surface, self.detail_rect)

    def _wrap_text(self, text, font, max_width):
        """Wrap text to fit within a given width"""
        if not text:
            return ["No information available"]
        
        # Split text by newlines first
        paragraphs = text.split('\n')
        lines = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():  # Skip empty paragraphs
                lines.append("")
                continue
            
            words = paragraph.split(' ')
            current_line = []
            current_width = 0
            
            for word in words:
                # Handle markdown headers (##, ###)
                if word.startswith('#'):
                    if current_line:  # End current line
                        lines.append(' '.join(current_line))
                        current_line = []
                        current_width = 0
                    
                    # Add header as its own line
                    lines.append(word)
                    continue
                
                # Measure word width
                word_surface, _ = font.render(word + " ", (0, 0, 0))
                word_width = word_surface.get_width()
                
                # Check if adding this word exceeds the max width
                if current_width + word_width > max_width:
                    if current_line:  # Don't add empty lines
                        lines.append(' '.join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    current_line.append(word)
                    current_width += word_width
            
            # Add the last line of the paragraph
            if current_line:
                lines.append(' '.join(current_line))
        
        return lines

    def show_civ_details(self, civ):
        """Show detailed information about a civilization"""
        self.showing_civ_details = True
        self.detail_civ = civ
        self.detail_surface = None  # Force recreation of the surface
    
    def close_civ_details(self):
        """Close the civilization details popup"""
        self.showing_civ_details = False
        self.detail_civ = None
        
    def check_civ_details_click(self, pos):
        """Check if a click was on the civilization details popup"""
        if not self.showing_civ_details:
            return False
            
        # Adjust the position to be relative to the popup
        popup_relative_pos = (pos[0] - self.detail_rect.left, pos[1] - self.detail_rect.top)
        
        # Check if click was on the close button (using popup-relative coordinates)
        if self.detail_close_button and self.detail_close_button.collidepoint(popup_relative_pos):
            self.close_civ_details()
            return True
            
        # Check if click was within the popup
        if self.detail_rect and self.detail_rect.collidepoint(pos):
            return True
            
        return False 

    def toggle_bottom_panel(self):
        """Toggle the visibility of the bottom information panel"""
        self.show_bottom_panel = not self.show_bottom_panel
        return self.show_bottom_panel 

    def set_simulation(self, simulation):
        """Set the simulation reference for lore generation"""
        self.simulation = simulation 