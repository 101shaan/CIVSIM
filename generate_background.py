#!/usr/bin/env python3
"""
Generate a background image for the Civilization Simulator main menu
"""
import os
import pygame
import random
import math
import numpy as np
from pygame import gfxdraw

def generate_background():
    # Set up the dimensions - same as the game window
    width, height = 1400, 900
    
    # Create a new surface
    background = pygame.Surface((width, height))
    
    # Create a gradient background (dark blue to deeper blue)
    for y in range(height):
        # Calculate gradient color (from dark blue at top to deeper blue at bottom)
        r = int(10 + (y / height) * 15)  # Very dark blue
        g = int(20 + (y / height) * 20)  # Slight green tint
        b = int(50 + (y / height) * 30)  # Blue base
        
        # Draw a horizontal line with this color
        pygame.draw.line(background, (r, g, b), (0, y), (width, y))
    
    # Add subtle star field in the background
    draw_stars(background, width, height)
    
    # Add a subtle world map silhouette in the background
    draw_world_map(background, width, height)
    
    # Add some subtle grid lines to represent latitude/longitude
    draw_grid_lines(background, width, height)
    
    # Add some civilization markers (small glowing dots)
    draw_civilization_markers(background, width, height)
    
    # Add some subtle ancient symbols and patterns
    draw_ancient_symbols(background, width, height)
    
    # Add some subtle moving light beams (like aurora)
    draw_light_beams(background, width, height)
    
    # Add a vignette effect (darker corners)
    add_vignette(background, width, height)
    
    # Make sure the directory exists
    os.makedirs("assets/backgrounds", exist_ok=True)
    
    # Save the background
    pygame.image.save(background, "assets/backgrounds/main_menu_bg.png")
    print("Background saved to assets/backgrounds/main_menu_bg.png")
    
    return "assets/backgrounds/main_menu_bg.png"

def draw_stars(surface, width, height):
    """Draw a subtle star field in the background"""
    # Create a surface for the stars with alpha
    stars_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Generate stars with varying brightness
    num_stars = 300
    for _ in range(num_stars):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Vary star size and brightness
        size = random.randint(1, 3)
        brightness = random.randint(100, 255)
        
        # Draw star
        if size == 1:
            # Single pixel star
            stars_surface.set_at((x, y), (brightness, brightness, brightness, random.randint(100, 180)))
        else:
            # Larger star with glow
            pygame.gfxdraw.filled_circle(stars_surface, x, y, size - 1, 
                                        (brightness, brightness, brightness, 150))
            pygame.gfxdraw.aacircle(stars_surface, x, y, size, 
                                   (brightness, brightness, brightness, 70))
    
    # Add a few brighter stars with subtle glow
    for _ in range(20):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        # Draw the star with a subtle glow
        for radius in range(4, 0, -1):
            alpha = 150 if radius == 1 else 40 - radius * 10
            if alpha > 0:
                pygame.gfxdraw.filled_circle(stars_surface, x, y, radius, 
                                           (255, 255, 255, alpha))
    
    # Blit the stars onto the main surface
    surface.blit(stars_surface, (0, 0))

def draw_world_map(surface, width, height):
    # Simple world map silhouette - just basic continent outlines
    continents = [
        # North America (simplified polygon points)
        [(0.1, 0.2), (0.2, 0.15), (0.3, 0.2), (0.25, 0.35), (0.15, 0.4), (0.1, 0.3)],
        # South America
        [(0.2, 0.4), (0.25, 0.4), (0.3, 0.5), (0.25, 0.6), (0.2, 0.55)],
        # Europe
        [(0.45, 0.2), (0.55, 0.15), (0.6, 0.25), (0.5, 0.3)],
        # Africa
        [(0.45, 0.3), (0.55, 0.3), (0.6, 0.5), (0.5, 0.6), (0.4, 0.5)],
        # Asia
        [(0.55, 0.15), (0.8, 0.15), (0.85, 0.3), (0.75, 0.4), (0.6, 0.35)],
        # Australia
        [(0.8, 0.5), (0.9, 0.5), (0.85, 0.6), (0.75, 0.6)]
    ]
    
    # Draw each continent as a subtle shape
    for continent in continents:
        # Convert relative coordinates to actual pixels
        points = [(int(x * width), int(y * height)) for x, y in continent]
        
        # Create a surface for the continent with alpha
        continent_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw the continent with a subtle blue color
        pygame.draw.polygon(continent_surface, (60, 100, 150, 40), points)
        
        # Add a subtle glow effect
        for i in range(3):
            pygame.draw.polygon(continent_surface, (60, 100, 150, 5), points, 3 + i*2)
        
        # Blit the continent onto the main surface
        surface.blit(continent_surface, (0, 0))

def draw_grid_lines(surface, width, height):
    # Draw subtle longitude lines
    for x in range(0, width, 100):
        # Create a surface for the line with alpha
        line_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw a vertical line with low opacity
        pygame.draw.line(line_surface, (100, 150, 200, 10), (x, 0), (x, height))
        
        # Blit the line onto the main surface
        surface.blit(line_surface, (0, 0))
    
    # Draw subtle latitude lines
    for y in range(0, height, 100):
        # Create a surface for the line with alpha
        line_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw a horizontal line with low opacity
        pygame.draw.line(line_surface, (100, 150, 200, 10), (0, y), (width, y))
        
        # Blit the line onto the main surface
        surface.blit(line_surface, (0, 0))

def draw_civilization_markers(surface, width, height):
    # Generate some random civilization markers
    num_markers = 20
    
    for _ in range(num_markers):
        # Random position
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        
        # Create a surface for the marker with alpha
        marker_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw a glowing dot
        for radius in range(8, 0, -1):
            alpha = 150 if radius == 1 else 20 - radius * 2
            pygame.gfxdraw.filled_circle(marker_surface, x, y, radius, (200, 220, 255, alpha))
        
        # Draw a small solid center
        pygame.gfxdraw.filled_circle(marker_surface, x, y, 2, (220, 240, 255, 180))
        
        # Blit the marker onto the main surface
        surface.blit(marker_surface, (0, 0))

def draw_ancient_symbols(surface, width, height):
    # Add some subtle ancient symbols and patterns
    num_symbols = 15
    
    for _ in range(num_symbols):
        # Random position
        x = random.randint(100, width - 100)
        y = random.randint(100, height - 100)
        
        # Create a surface for the symbol with alpha
        symbol_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Choose a random symbol type
        symbol_type = random.choice(['circle', 'square', 'triangle', 'hexagon', 'star'])
        
        # Random size and opacity
        size = random.randint(20, 60)
        opacity = random.randint(10, 30)
        
        if symbol_type == 'circle':
            pygame.gfxdraw.circle(symbol_surface, x, y, size, (150, 180, 220, opacity))
            pygame.gfxdraw.circle(symbol_surface, x, y, size - 5, (150, 180, 220, opacity))
        
        elif symbol_type == 'square':
            rect = pygame.Rect(x - size//2, y - size//2, size, size)
            pygame.draw.rect(symbol_surface, (150, 180, 220, opacity), rect, 1)
            pygame.draw.rect(symbol_surface, (150, 180, 220, opacity), rect.inflate(-10, -10), 1)
        
        elif symbol_type == 'triangle':
            points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
            pygame.draw.polygon(symbol_surface, (150, 180, 220, opacity), points, 1)
            
            # Inner triangle
            inner_points = [(x, y - size + 10), (x - size + 10, y + size - 10), (x + size - 10, y + size - 10)]
            pygame.draw.polygon(symbol_surface, (150, 180, 220, opacity), inner_points, 1)
        
        elif symbol_type == 'hexagon':
            points = []
            for i in range(6):
                angle = math.pi * 2 * i / 6
                points.append((x + size * math.cos(angle), y + size * math.sin(angle)))
            pygame.draw.polygon(symbol_surface, (150, 180, 220, opacity), points, 1)
            
            # Inner hexagon
            inner_points = []
            for i in range(6):
                angle = math.pi * 2 * i / 6
                inner_points.append((x + (size-10) * math.cos(angle), y + (size-10) * math.sin(angle)))
            pygame.draw.polygon(symbol_surface, (150, 180, 220, opacity), inner_points, 1)
        
        elif symbol_type == 'star':
            points = []
            for i in range(10):
                angle = math.pi * 2 * i / 10
                r = size if i % 2 == 0 else size // 2
                points.append((x + r * math.cos(angle), y + r * math.sin(angle)))
            pygame.draw.polygon(symbol_surface, (150, 180, 220, opacity), points, 1)
        
        # Blit the symbol onto the main surface
        surface.blit(symbol_surface, (0, 0))

def draw_light_beams(surface, width, height):
    """Draw subtle light beams like aurora in the background"""
    # Create a surface for the light beams with alpha
    beams_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Number of beams
    num_beams = 5
    
    for _ in range(num_beams):
        # Random position and properties
        start_x = random.randint(0, width)
        start_y = random.randint(0, height // 3)  # Start in the upper third
        beam_width = random.randint(100, 300)
        beam_height = random.randint(height // 3, height // 2)
        
        # Create points for a curved beam
        points = []
        for i in range(10):
            # Create a wavy pattern
            x_offset = math.sin(i / 9 * math.pi) * beam_width / 4
            x = start_x + x_offset
            y = start_y + (i / 9) * beam_height
            points.append((x, y))
        
        # Add points to complete the shape
        for i in range(9, -1, -1):
            x_offset = math.sin(i / 9 * math.pi) * beam_width / 4
            x = start_x + beam_width / 2 + x_offset
            y = start_y + (i / 9) * beam_height
            points.append((x, y))
        
        # Choose a color for the beam (blue/teal/purple variations)
        r = random.randint(20, 100)
        g = random.randint(80, 150)
        b = random.randint(150, 220)
        
        # Draw the beam with a gradient
        for i in range(5):
            # Decrease opacity for each layer
            alpha = 30 - i * 5
            if alpha > 0:
                # Scale the points slightly for each layer
                scaled_points = []
                for x, y in points:
                    scaled_x = start_x + (x - start_x) * (1 + i * 0.1)
                    scaled_y = y
                    scaled_points.append((scaled_x, scaled_y))
                
                # Draw the beam
                pygame.draw.polygon(beams_surface, (r, g, b, alpha), scaled_points)
    
    # Blit the beams onto the main surface
    surface.blit(beams_surface, (0, 0))

def add_vignette(surface, width, height):
    # Create a surface for the vignette with alpha
    vignette = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Calculate the maximum distance from center
    max_dist = math.sqrt((width/2)**2 + (height/2)**2)
    center_x, center_y = width/2, height/2
    
    # Create radial gradient using concentric circles
    # This is much faster than pixel-by-pixel
    for r in range(10, int(max_dist), 5):
        # Calculate alpha based on radius (stronger at edges)
        dist_ratio = r / max_dist
        alpha = int(min(255, dist_ratio * dist_ratio * 150))
        
        if alpha > 0:
            pygame.draw.circle(
                vignette, 
                (0, 0, 0, alpha), 
                (int(center_x), int(center_y)), 
                r, 
                5
            )
    
    # Blit the vignette onto the main surface
    surface.blit(vignette, (0, 0))

if __name__ == "__main__":
    pygame.init()
    generate_background()
    pygame.quit() 