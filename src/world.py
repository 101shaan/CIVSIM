"""
world generation module for civ simulator
"""
import random
import numpy as np
import math

class TerrainType:
    WATER = 0
    LAND = 1
    MOUNTAIN = 2
    FOREST = 3
    DESERT = 4

class World:
    def __init__(self, size=(100, 100)):
        self.width, self.height = size
        self.terrain = np.zeros((self.width, self.height), dtype=int)
        self.civilizations = []
        self.resources = {}  # maps positions to resource availability

    def generate(self, seed=None):
        """generate a procedural world with terrain features"""
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        
        self._generate_terrain()
        self._place_resources()
        
        return self
    
    def _generate_terrain(self):
        """generate terrain using perlin-like noise"""
        # simple noise for demo purposes
        # land vs water (70% land)
        for x in range(self.width):
            for y in range(self.height):
                # basic terrain generation
                if random.random() < 0.3:
                    self.terrain[x, y] = TerrainType.WATER
                else:
                    self.terrain[x, y] = TerrainType.LAND

        # create some mountain clusters
        for _ in range(int(self.width * self.height * 0.01)):  # 1% mountains
            cx, cy = random.randint(5, self.width-5), random.randint(5, self.height-5)
            
            if self.terrain[cx, cy] == TerrainType.LAND:
                self.terrain[cx, cy] = TerrainType.MOUNTAIN
                
                # create some surrounding mountains
                for i in range(-2, 3):
                    for j in range(-2, 3):
                        if 0 <= cx+i < self.width and 0 <= cy+j < self.height:
                            if random.random() < 0.7:
                                if self.terrain[cx+i, cy+j] == TerrainType.LAND:
                                    self.terrain[cx+i, cy+j] = TerrainType.MOUNTAIN
        
        # create forest areas
        for _ in range(int(self.width * self.height * 0.03)):  # 3% starting forest points
            cx, cy = random.randint(5, self.width-5), random.randint(5, self.height-5)
            
            if self.terrain[cx, cy] == TerrainType.LAND:
                self.terrain[cx, cy] = TerrainType.FOREST
                
                # create forest clusters
                for i in range(-3, 4):
                    for j in range(-3, 4):
                        if 0 <= cx+i < self.width and 0 <= cy+j < self.height:
                            if random.random() < 0.6:
                                if self.terrain[cx+i, cy+j] == TerrainType.LAND:
                                    self.terrain[cx+i, cy+j] = TerrainType.FOREST
        
        # create desert regions
        for _ in range(int(self.width * self.height * 0.02)):  # 2% deserts
            cx, cy = random.randint(5, self.width-5), random.randint(5, self.height-5)
            
            if self.terrain[cx, cy] == TerrainType.LAND:
                self.terrain[cx, cy] = TerrainType.DESERT
                
                # create desert regions
                for i in range(-5, 6):
                    for j in range(-5, 6):
                        if 0 <= cx+i < self.width and 0 <= cy+j < self.height:
                            if random.random() < 0.7:
                                if self.terrain[cx+i, cy+j] == TerrainType.LAND:
                                    self.terrain[cx+i, cy+j] = TerrainType.DESERT
    
    def _place_resources(self):
        """place resources across the world map"""
        resource_types = ["food", "metal", "gold", "stone"]
        
        # place resources with varying abundance
        for x in range(self.width):
            for y in range(self.height):
                if self.terrain[x, y] != TerrainType.WATER:
                    self.resources[(x, y)] = {}
                    
                    # different terrain has different resource distributions
                    for resource in resource_types:
                        if self.terrain[x, y] == TerrainType.MOUNTAIN:
                            # mountains have more metal and stone
                            if resource in ["metal", "stone"]:
                                self.resources[(x, y)][resource] = random.uniform(0.5, 1.0)
                            else:
                                self.resources[(x, y)][resource] = random.uniform(0, 0.2)
                        
                        elif self.terrain[x, y] == TerrainType.FOREST:
                            # forests have more food
                            if resource == "food":
                                self.resources[(x, y)][resource] = random.uniform(0.7, 1.0)
                            else:
                                self.resources[(x, y)][resource] = random.uniform(0.2, 0.5)
                        
                        elif self.terrain[x, y] == TerrainType.DESERT:
                            # deserts have more gold but less food
                            if resource == "gold":
                                self.resources[(x, y)][resource] = random.uniform(0.5, 0.9)
                            elif resource == "food":
                                self.resources[(x, y)][resource] = random.uniform(0, 0.1)
                            else:
                                self.resources[(x, y)][resource] = random.uniform(0.2, 0.4)
                        
                        else:  # regular land
                            self.resources[(x, y)][resource] = random.uniform(0.3, 0.6)

    def is_valid_position(self, position):
        """check if a position is within world bounds"""
        x, y = position
        return 0 <= x < self.width and 0 <= y < self.height
    
    def get_terrain_at(self, position):
        """get terrain type at a position"""
        x, y = position
        if self.is_valid_position(position):
            return self.terrain[x, y]
        return None
    
    def find_settlement_location(self):
        """find a suitable location for a new civilization to settle"""
        # try to find a good spot (land with resources, away from other civs)
        attempts = 0
        max_attempts = 500
        min_distance = 12  # minimum distance from other civs
        
        while attempts < max_attempts:
            x = random.randint(5, self.width - 5)
            y = random.randint(5, self.height - 5)
            
            if self.terrain[x, y] == TerrainType.LAND:
                # check if there's enough land area around
                land_count = 0
                for i in range(-3, 4):
                    for j in range(-3, 4):
                        if 0 <= x+i < self.width and 0 <= y+j < self.height:
                            if self.terrain[x+i, y+j] == TerrainType.LAND:
                                land_count += 1
                
                # check distance from other civilizations
                too_close = False
                for civ in self.civilizations:
                    for city_pos in civ.cities.keys():
                        cx, cy = city_pos
                        distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                        if distance < min_distance:
                            too_close = True
                            break
                    
                    # also check general territory
                    if not too_close:
                        for pos in civ.territory:
                            cx, cy = pos
                            distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                            if distance < min_distance * 0.5:  # less restrictive for territory
                                too_close = True
                                break
                    
                    if too_close:
                        break
                
                # if we have at least 30 land tiles in the vicinity AND we're not too close to others
                if land_count >= 30 and not too_close:
                    return (x, y)
            
            attempts += 1
        
        # if no ideal spot found, relax constraints but still respect minimum distance
        attempts = 0
        while attempts < max_attempts:
            x = random.randint(2, self.width - 2)
            y = random.randint(2, self.height - 2)
            
            if self.terrain[x, y] == TerrainType.LAND:
                # check distance from other civilizations
                too_close = False
                for civ in self.civilizations:
                    for city_pos in civ.cities.keys():
                        cx, cy = city_pos
                        distance = math.sqrt((x - cx)**2 + (y - cy)**2)
                        if distance < min_distance * 0.5:  # relaxed distance constraint
                            too_close = True
                            break
                        
                    if too_close:
                        break
                
                if not too_close:
                    return (x, y)
            
            attempts += 1
        
        # absolute fallback - just find any land tile
        for _ in range(100):
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if self.terrain[x, y] == TerrainType.LAND:
                return (x, y)
                
        # if we somehow still failed, just return the center of the map
        return (self.width // 2, self.height // 2)
    
    def add_civilization(self, civilization):
        """add a civilization to the world"""
        self.civilizations.append(civilization)
        
    def get_civilizations_at(self, position):
        """get all civilizations at a specific position"""
        return [civ for civ in self.civilizations if civ.has_territory_at(position)] 