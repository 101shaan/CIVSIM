"""
civilization module for civ simulator
"""
import random
import uuid
import math

class CivilizationTrait:
    AGGRESSIVE = "aggressive"
    TECH_SAVVY = "tech_savvy"
    RELIGIOUS = "religious"
    WEIRD = "weird"
    PEACEFUL = "peaceful"
    EXPANSIONIST = "expansionist"
    ISOLATIONIST = "isolationist"
    TRADING = "trading"
    
    @classmethod
    def get_random_traits(cls, count=3):
        """grab some random traits for a civ"""
        all_traits = [cls.AGGRESSIVE, cls.TECH_SAVVY, cls.RELIGIOUS, cls.WEIRD, 
                     cls.PEACEFUL, cls.EXPANSIONIST, cls.ISOLATIONIST, cls.TRADING]
        
        # gotta make sure we don't pick traits that don't make sense together
        opposites = {
            cls.AGGRESSIVE: cls.PEACEFUL,
            cls.PEACEFUL: cls.AGGRESSIVE,
            cls.EXPANSIONIST: cls.ISOLATIONIST,
            cls.ISOLATIONIST: cls.EXPANSIONIST
        }
        
        selected = []
        for _ in range(count):
            if not selected:
                # first trait can be anything
                trait = random.choice(all_traits)
                selected.append(trait)
            else:
                # filter out opposites of already selected traits
                filtered_traits = [t for t in all_traits if t not in selected and 
                                  not any(t == opposites.get(s, "") for s in selected)]
                
                if filtered_traits:
                    trait = random.choice(filtered_traits)
                    selected.append(trait)
        
        return selected

class BeliefSystem:
    def __init__(self):
        self.name = self._generate_name()
        self.values = self._generate_core_values()
        self.foreign_stance = self._generate_foreign_stance()
    
    def _generate_name(self):
        """come up with a random name for the belief system"""
        prefixes = ["Church of", "Cult of", "Order of", "Way of", "Faith of", 
                   "Followers of", "Ideology of", "Believers in"]
        subjects = ["Eternal Light", "Cosmic Balance", "Divine Wisdom", "Blessed Harmony", 
                   "Sacred Knowledge", "Mighty Mountains", "Flowing Water", "Golden Sun", 
                   "Silver Moon", "Whispered Secrets", "Endless Cycles", "Unbounded Nature"]
        
        return f"{random.choice(prefixes)} {random.choice(subjects)}"
    
    def _generate_core_values(self):
        """generate core values for the belief system"""
        possible_values = {
            "peace": random.uniform(0, 1),
            "war": random.uniform(0, 1),
            "knowledge": random.uniform(0, 1),
            "tradition": random.uniform(0, 1),
            "wealth": random.uniform(0, 1),
            "spirituality": random.uniform(0, 1)
        }
        
        # normalize values
        total = sum(possible_values.values())
        return {k: v/total for k, v in possible_values.items()}
    
    def _generate_foreign_stance(self):
        """figure out how this belief system deals with foreign beliefs"""
        stances = ["open", "neutral", "hostile", "convert"]
        weights = [0.25, 0.35, 0.25, 0.15]  # more neutral than extreme
        return random.choices(stances, weights=weights)[0]
    
    def get_similarity(self, other_belief):
        """calculate how similar two belief systems are (0-1)"""
        similarity = 0
        
        # compare core values
        for value, strength in self.values.items():
            other_strength = other_belief.values.get(value, 0)
            similarity += 1 - abs(strength - other_strength)
        
        # normalize to 0-1 range
        return similarity / len(self.values)

class Civilization:
    def __init__(self, world, position=None):
        self.id = str(uuid.uuid4())
        self.world = world
        
        # generate a name for the civilization
        self.name = self._generate_name()
        
        # find a suitable position if none provided
        if position is None:
            self.position = world.find_settlement_location()
        else:
            self.position = position
            
        # basic properties
        self.population = random.randint(50, 200)
        self.age = 0  # age in ticks
        
        # initialize territory with the starting position and some surrounding area
        self.territory = set()
        self._initialize_starting_territory()
        
        # create the first city
        self.cities = {self.position: {"name": self.name, "population": self.population}}
        
        # traits and beliefs
        self.traits = CivilizationTrait.get_random_traits()
        self.belief_system = BeliefSystem()
        
        # relations with other civilizations
        self.relations = {}  # maps civ_id -> relation_value (-1 to 1)
        
        # technology level (0-50000) - much higher cap now
        self.technology = random.randint(10, 30)
        
        # resources and production
        self.resources = {
            "food": 100,
            "metal": 50,
            "gold": 20,
            "stone": 50
        }
        
        self.production = {
            "food": 0,
            "metal": 0,
            "gold": 0, 
            "stone": 0
        }
        
        # event log
        self.event_log = []
        
        # battle victories and territory gains
        self.battle_victories = 0
        self.territory_last_tick = set()  # initialize as an empty set instead of an integer
        
        # add founding event
        self._add_event(f"Founded at {self.position}")
    
    def _generate_name(self):
        """come up with a random name for the civilization"""
        prefixes = ["Glorious ", "Ancient ", "Mighty ", "Sacred ", "Golden ", 
                   "Silver ", "Eternal ", "Rising ", "United ", ""]
        
        nouns = ["Empire", "Kingdom", "Republic", "Tribes", "Federation", "Realm",
                "Dominion", "Alliance", "States", "Confederation"]
        
        names = ["Zephyr", "Aetheria", "Lumina", "Solara", "Terran", "Aquila", 
               "Drakon", "Orion", "Lyra", "Nimbus", "Zenith", "Nexus", "Nova"]
        
        name_type = random.choice(["prefix_noun", "name_noun", "name"])
        
        if name_type == "prefix_noun":
            return f"{random.choice(prefixes)}{random.choice(nouns)}"
        elif name_type == "name_noun":
            return f"{random.choice(names)} {random.choice(nouns)}"
        else:
            return random.choice(names)
    
    def tick(self, full_update=True):
        """progress the civilization one time step
        
        args:
            full_update (bool): if true, do all updates. if false, only do basic resource/population updates.
        """
        self.age += 1
        
        # store territory size before update for tracking
        old_territory_size = len(self.territory)
        self.territory_last_tick = set(self.territory)  # store a copy of the territory as a set
        
        # these operations always happen
        # grow or shrink population based on resources and demographics
        self._update_population()
        
        # gather resources from territory
        self._gather_resources()
        
        # only perform expensive operations during full update
        if full_update:
            # consider expanding territory
            self._consider_expansion()
            
            # check for interactions with other civilizations
            self._check_interactions()
        
        # advance technology randomly, influenced by traits (cheaper operation)
        # tech growth is much slower now
        if self._has_trait(CivilizationTrait.TECH_SAVVY):
            tech_gain = random.uniform(0.05, 0.15)
        else:
            tech_gain = random.uniform(0.01, 0.05)
            
        self.technology = min(50000, self.technology + tech_gain)  # increased cap to 50,000
        
        # debug tracking for territory changes
        new_territory_size = len(self.territory)
        territory_gained = max(0, new_territory_size - old_territory_size)
        
        # record significant territory gains
        if territory_gained > 5:
            self._add_event(f"Expanded territory significantly, gaining {territory_gained} tiles")
            # gaining territory boosts population
            pop_boost = int(territory_gained * random.uniform(2, 5))
            self.population += pop_boost
        
        if new_territory_size < old_territory_size:
            print(f"WARNING: {self.name} lost territory: {old_territory_size} -> {new_territory_size}")
        
        # safety check to ensure civilization doesn't disappear
        if not self.territory:
            print(f"CRITICAL: {self.name} has no territory, attempting to restore")
            self._initialize_starting_territory()
    
    def _update_population(self):
        """Update population based on available resources, territory size, and demographics"""
        # Calculate food per person
        food_per_person = self.resources["food"] / max(1, self.population)
        
        # Calculate territory-based population capacity
        # Each territory tile can support a limited population
        # This creates a hard cap on population based on territory size
        base_capacity_per_tile = 1000  # Base population capacity per territory tile
        tech_capacity_modifier = math.sqrt(min(100, self.technology)) / 5  # Tech increases capacity but with diminishing returns
        
        # Calculate effective capacity
        total_capacity = len(self.territory) * base_capacity_per_tile * tech_capacity_modifier
        
        # Calculate how close we are to capacity (affects growth rate)
        capacity_ratio = self.population / max(1, total_capacity)
        
        # If we're over capacity, force population decline
        if capacity_ratio > 1.1:  # 10% over capacity triggers decline
            base_growth_rate = -0.05  # Significant decline due to overcrowding
        
        # Otherwise use realistic demographic patterns based on food availability
        elif food_per_person >= 1.5:  # Abundant food
            base_growth_rate = random.uniform(0.01, 0.015)  # 1-1.5% annual growth (realistic pre-industrial rate)
        elif food_per_person >= 1.0:  # Plenty of food
            base_growth_rate = random.uniform(0.005, 0.01)  # 0.5-1% growth
        elif food_per_person >= 0.75:  # Sufficient food
            base_growth_rate = random.uniform(0.002, 0.005)  # 0.2-0.5% growth (subsistence level)
        elif food_per_person >= 0.5:  # Minimal food
            base_growth_rate = random.uniform(-0.002, 0.002)  # -0.2% to 0.2% (stagnation)
        else:  # Food shortage
            base_growth_rate = random.uniform(-0.02, -0.01)  # -1% to -2% (decline)
        
        # Capacity-based modifiers
        if capacity_ratio > 0.9:  # Approaching capacity
            base_growth_rate = base_growth_rate * (1.0 - capacity_ratio)  # Reduce growth as we approach capacity
        
        # Size-dependent growth: natural demographic transition
        size_factor = 1.0
        if self.population > 10000:
            size_factor = 0.8  # Slower growth for developing civilizations
        elif self.population > 50000:
            size_factor = 0.6  # Industrial transition
        elif self.population > 100000:
            size_factor = 0.4  # Post-industrial growth pattern
        elif self.population > 500000:
            size_factor = 0.2  # Modern growth patterns
        
        # Technology increases food efficiency, not raw growth rate
        tech_factor = 1.0 + (math.log(self.technology + 1) / 20)  # Much smaller technology impact
        
        # Traits modify growth rate
        trait_factor = 1.0
        if self._has_trait(CivilizationTrait.AGGRESSIVE):
            trait_factor *= 0.8  # Aggressive civilizations grow slower
        if self._has_trait(CivilizationTrait.PEACEFUL):
            trait_factor *= 1.1  # Peaceful civilizations grow slightly faster (reduced from 1.2)
        if self._has_trait(CivilizationTrait.EXPANSIONIST):
            # Expansionist civs grow faster if they have a lot of territory
            if len(self.territory) > 50:
                trait_factor *= 1.05
        
        # Protected civilizations get a growth boost
        protection_factor = 1.0
        if hasattr(self, 'protected_until_tick') and self.age < self.protected_until_tick:
            protection_factor = 1.2  # 20% growth bonus while protected
        
        # Apply all factors to calculate final growth rate
        growth_rate = base_growth_rate * size_factor * tech_factor * trait_factor * protection_factor
        
        # Calculate growth with absolute values for larger populations
        old_population = self.population
        
        # Make growth strictly proportional to population with small realistic percentages
        if self.population < 1000:
            # Small villages/tribes
            raw_population_change = int(self.population * growth_rate)
        elif self.population < 10000:
            # Early cities
            raw_population_change = int(self.population * growth_rate * 0.8)  # Reduced multiplier
        else:
            # Larger civilizations
            raw_population_change = int(self.population * growth_rate * 0.6)  # Even smaller multiplier for big populations
        
        # Apply population change with realistic numbers
        self.population = max(1, old_population + raw_population_change)
        
        # Enforce the hard capacity limit
        if self.population > total_capacity * 1.1:  # Allow temporary exceeding by 10%
            self.population = int(total_capacity * 1.1)
        
        # Only log truly significant population changes to reduce notifications
        if raw_population_change < -2000:  # Higher threshold for notification
            self._add_event(f"Population decreased significantly: {-raw_population_change} lost")
        elif raw_population_change > 2000:  # Higher threshold for notification
            self._add_event(f"Population increased significantly: +{raw_population_change}")
        
        # Consume food - proportional to population, modified by traits and efficiency
        food_consumption_rate = 0.5  # Base food consumption per person
        
        # Efficiency increases with technology (logarithmic scaling for diminishing returns)
        food_efficiency = 1.0 - (math.log(self.technology + 1) / 20)  
        
        # Young civilizations get help with food consumption
        if self.age < 20:
            food_efficiency *= 0.8  # 20% more efficient for young civilizations
        
        # Protected civilizations get additional help
        if hasattr(self, 'protected_until_tick') and self.age < self.protected_until_tick:
            food_efficiency *= 0.7  # 30% more efficient while protected
        
        # Special case: ensure minimum food consumption doesn't exhaust all food
        # This helps prevent starvation cycles
        if self.population <= 10:  # Much smaller threshold for minimum population
            food_consumption_rate *= 0.7  # Reduced consumption for struggling civs
        
        # Calculate actual food consumption
        food_consumed = min(self.resources["food"], 
                           self.population * food_consumption_rate * food_efficiency)
        self.resources["food"] -= food_consumed
    
    def _gather_resources(self):
        """Gather resources from controlled territory"""
        self.production = {resource: 0 for resource in self.resources.keys()}
        
        # If this is a very young civilization, boost resource gathering to help it survive
        young_bonus = max(0, (10 - self.age) / 10) if self.age < 10 else 0  # Bonus for first 10 years
        
        for position in self.territory:
            if position in self.world.resources:
                for resource, abundance in self.world.resources[position].items():
                    # Base gathering rate depends on population and technology
                    base_rate = (self.population / 100) * (self.technology / 50)
                    
                    # Apply young civilization bonus
                    base_rate *= (1 + young_bonus * 2)  # Up to 3x gathering rate for new civs
                    
                    # Traits affect resource gathering
                    rate_modifier = 1.0
                    if self._has_trait(CivilizationTrait.TECH_SAVVY) and resource in ["metal", "stone"]:
                        rate_modifier += 0.2
                    
                    # Gather resources
                    gathered = base_rate * abundance * rate_modifier
                    self.resources[resource] += gathered
                    self.production[resource] += gathered
        
        # Ensure minimum food production for young civilizations to prevent immediate starvation
        if self.age < 10 and self.production["food"] < self.population * 0.6:
            bonus_food = self.population * 0.6 - self.production["food"]
            self.resources["food"] += bonus_food
            self.production["food"] += bonus_food
    
    def _consider_expansion(self):
        """Consider expanding territory"""
        # All civilizations try to expand gradually
        # Base expansion pressure increases over time
        age_factor = min(1.0, self.age / 100)  # Ramps up over first 100 years
        
        # Expansion more likely with larger population and if expansionist
        # Lower base threshold to ensure expansion happens more regularly
        expansion_threshold = 80
        if self._has_trait(CivilizationTrait.EXPANSIONIST):
            expansion_threshold = 30
        elif self._has_trait(CivilizationTrait.ISOLATIONIST):
            expansion_threshold = 150
        
        # Scale threshold by current territory size to ensure continued expansion
        territory_factor = math.sqrt(len(self.territory) + 1) / 2
        adjusted_threshold = expansion_threshold * territory_factor
        
        # Always expand if population/territory ratio is high enough
        population_density = self.population / max(1, len(self.territory))
        
        should_expand = False
        if self.population >= adjusted_threshold:
            should_expand = True
        elif population_density > 30:  # High population density forces expansion
            should_expand = True
        elif random.random() < age_factor * 0.2:  # Random chance for expansion increases with civilization age
            should_expand = True
            
        if should_expand:
            # Get possible expansion targets
            expansion_candidates = self._get_expansion_candidates()
            
            if expansion_candidates:
                # Pick a random candidate
                new_territory = random.choice(expansion_candidates)
                self.territory.add(new_territory)
                
                # Sometimes establish a new city, but only if we don't have too many
                # and the population is large enough
                max_cities = max(3, int(math.sqrt(len(self.territory)))) 
                
                city_creation_chance = 0.05  # Base 5% chance
                
                # Adjust based on traits
                if self._has_trait(CivilizationTrait.EXPANSIONIST):
                    city_creation_chance += 0.05
                if self._has_trait(CivilizationTrait.ISOLATIONIST):
                    city_creation_chance -= 0.03
                    
                if (random.random() < city_creation_chance and 
                    len(self.cities) < max_cities and 
                    self.population > len(self.cities) * 100):
                    
                    # Check if location is suitable for a city
                    # Better locations: near water, on plains, not mountains
                    terrain = self.world.get_terrain_at(new_territory)
                    has_water_nearby = False
                    
                    # Check surrounding tiles for water (good for city)
                    x, y = new_territory
                    for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                        check_pos = (x + dx, y + dy)
                        if self.world.is_valid_position(check_pos):
                            if self.world.get_terrain_at(check_pos) == 0:  # Water
                                has_water_nearby = True
                                break
                    
                    # Score the location
                    location_score = 0
                    if has_water_nearby:
                        location_score += 2
                    if terrain == 1:  # Plains
                        location_score += 1
                    if terrain == 3:  # Forest
                        location_score += 0.5
                    if terrain == 2:  # Mountains
                        location_score -= 1
                        
                    # Only create city if the location is decent
                    if location_score > 0 or random.random() < 0.2:  # 20% chance even if location isn't great
                        new_city_pop = int(self.population * 0.2)
                        self.population -= new_city_pop
                        
                        # Generate a city name based on trait and location
                        city_name = self._generate_city_name(new_territory, terrain)
                        
                        self.cities[new_territory] = {"name": city_name, "population": new_city_pop}
                        
                        self._add_event(f"Established new city {city_name} at {new_territory}")
                else:
                    # Only log significant territorial expansions to avoid spam
                    if len(self.territory) % 10 == 0:
                        self._add_event(f"Expanded territory to {len(self.territory)} tiles")
        
        # Occasionally merge or abandon very small cities
        self._optimize_cities()
    
    def _optimize_cities(self):
        """Periodically optimize cities to reduce clutter and improve performance"""
        if random.random() < 0.05:  # 5% chance per tick
            cities_to_remove = []
            
            # Identify very small cities for potential removal
            for pos, city_info in self.cities.items():
                # Skip the main city (highest population)
                if city_info["population"] < 50 and len(self.cities) > 1:
                    cities_to_remove.append(pos)
            
            # Remove small cities, transfer population back to largest city
            if cities_to_remove:
                # Find the largest city
                largest_city_pos = max(self.cities.items(), key=lambda x: x[1]["population"])[0]
                
                for pos in cities_to_remove[:2]:  # Limit to 2 cities per tick
                    # Transfer population
                    self.cities[largest_city_pos]["population"] += self.cities[pos]["population"]
                    
                    # Log the event
                    self._add_event(f"Abandoned small settlement {self.cities[pos]['name']}")
                    
                    # Remove the city
                    del self.cities[pos]
    
    def _generate_city_name(self, position, terrain):
        """Generate a name for a city based on traits and terrain"""
        # Base name components
        prefixes = ["New ", "Fort ", "Port ", "Mount ", ""]
        suffixes = ["City", "Town", "Village", "Settlement", "Station", "Post", "Camp", "Heights", "Point"]
        
        # Terrain-specific prefixes
        terrain_prefixes = {
            0: ["Bay ", "Harbor ", "Port "],  # Water
            1: ["Green ", "Plains ", "Field "],  # Land
            2: ["Mount ", "Peak ", "High "],  # Mountain
            3: ["Forest ", "Wood ", "Green "],  # Forest
            4: ["Dune ", "Desert ", "Sand "]   # Desert
        }
        
        # Name based on traits
        trait_words = {
            CivilizationTrait.RELIGIOUS: ["Holy ", "Sacred ", "Temple ", "Shrine "],
            CivilizationTrait.AGGRESSIVE: ["Fort ", "Guard ", "Battle ", "Warrior "],
            CivilizationTrait.TECH_SAVVY: ["New ", "Tech ", "Innovation ", "Academy "],
            CivilizationTrait.TRADING: ["Market ", "Trade ", "Commerce ", "Exchange "],
            CivilizationTrait.PEACEFUL: ["Harmony ", "Peace ", "Garden ", "Serene "],
            CivilizationTrait.WEIRD: ["Strange ", "Mystic ", "Void ", "Ethereal "]
        }
        
        # Combine elements to create name
        if random.random() < 0.3:  # 30% chance for trait-based name
            for trait in self.traits:
                if trait in trait_words:
                    options = trait_words[trait]
                    prefix = random.choice(options)
                    suffix = random.choice(suffixes)
                    return f"{prefix}{suffix}"
        
        # Otherwise use terrain-based name
        if terrain in terrain_prefixes and random.random() < 0.5:
            prefix = random.choice(terrain_prefixes[terrain])
        else:
            prefix = random.choice(prefixes)
        
        # Add some of the civilization's name to make it cohesive
        if random.random() < 0.3 and " " in self.name:
            parts = self.name.split()
            civ_part = random.choice(parts)
            return f"{prefix}{civ_part} {random.choice(suffixes)}"
        
        # Use a letter from the alphabet combined with the city count
        letter = chr(65 + len(self.cities) % 26)
        if random.random() < 0.2:
            return f"{prefix}{letter}-{random.randint(1, 9)}"
        
        # Basic naming
        suffix = random.choice(suffixes)
        return f"{prefix}{suffix}"
    
    def _get_expansion_candidates(self):
        """Get possible positions for territory expansion"""
        if not self.territory:
            return []
            
        # Find all valid adjacent tiles to current territory
        candidates = set()
        for pos in self.territory:
            x, y = pos
            
            # Check all adjacent positions (including diagonals)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                new_pos = (x + dx, y + dy)
                
                # Skip if out of bounds
                if not self.world.is_valid_position(new_pos):
                    continue
                    
                # Skip if already in our territory
                if new_pos in self.territory:
                    continue
                    
                # Skip water tiles
                if self.world.get_terrain_at(new_pos) == 0:  # Water
                    continue
                    
                # Skip if claimed by another civilization
                already_claimed = False
                for other_civ in self.world.civilizations:
                    if other_civ.id != self.id and new_pos in other_civ.territory:
                        already_claimed = True
                        break
                        
                if not already_claimed:
                    candidates.add(new_pos)
        
        return list(candidates)
    
    def _check_interactions(self):
        """Check for interactions with neighboring civilizations"""
        for civ in self.world.civilizations:
            if civ.id == self.id:
                continue
                
            # Check if territories are adjacent
            if self._territories_adjacent(civ):
                # Initialize relation if needed
                if civ.id not in self.relations:
                    initial_relation = random.uniform(-0.3, 0.3)
                    
                    # Traits affect initial relations
                    if self._has_trait(CivilizationTrait.AGGRESSIVE) or civ._has_trait(CivilizationTrait.AGGRESSIVE):
                        initial_relation -= 0.2
                    
                    if self._has_trait(CivilizationTrait.PEACEFUL) and civ._has_trait(CivilizationTrait.PEACEFUL):
                        initial_relation += 0.3
                    
                    # Belief similarity affects initial relations
                    belief_similarity = self.belief_system.get_similarity(civ.belief_system)
                    initial_relation += belief_similarity - 0.5  # -0.5 to 0.5 adjustment
                    
                    self.relations[civ.id] = max(-1.0, min(1.0, initial_relation))
                    civ.relations[self.id] = self.relations[civ.id]
                    
                    self._add_event(f"First contact with {civ.name}")
                
                # Consider diplomatic actions or war
                self._consider_diplomacy(civ)
    
    def _territories_adjacent(self, other_civ):
        """Check if two civilizations' territories are adjacent"""
        for pos1 in self.territory:
            x1, y1 = pos1
            for pos2 in other_civ.territory:
                x2, y2 = pos2
                # Check if positions are adjacent (including diagonals)
                if abs(x1 - x2) <= 1 and abs(y1 - y2) <= 1:
                    return True
        return False
    
    def _consider_diplomacy(self, other_civ):
        """Consider diplomatic actions with another civilization"""
        # Don't interact with collapsed civilizations
        if hasattr(other_civ, 'has_collapsed') and other_civ.has_collapsed:
            return
        
        # First contact case
        if other_civ.id not in self.relations:
            # Initialize relations based on traits and beliefs
            base_relation = random.uniform(-0.3, 0.3)  # Base randomness
            
            # Trait compatibility affects initial relations
            trait_factor = 0
            if self._has_trait(CivilizationTrait.AGGRESSIVE) and other_civ._has_trait(CivilizationTrait.AGGRESSIVE):
                trait_factor -= 0.2  # Aggressive civs don't like competition
            if self._has_trait(CivilizationTrait.PEACEFUL) and other_civ._has_trait(CivilizationTrait.PEACEFUL):
                trait_factor += 0.3  # Peaceful civs like other peaceful civs
            if self._has_trait(CivilizationTrait.ISOLATIONIST):
                trait_factor -= 0.2  # Isolationists are suspicious of everyone
            if self._has_trait(CivilizationTrait.TRADING) and other_civ._has_trait(CivilizationTrait.TRADING):
                trait_factor += 0.3  # Trading civs like other trading civs
                
            # Belief system compatibility
            belief_similarity = self.belief_system.get_similarity(other_civ.belief_system)
            belief_factor = (belief_similarity - 0.5) * 0.4  # -0.2 to +0.2 based on beliefs
            
            # Set initial relations
            initial_relation = base_relation + trait_factor + belief_factor
            initial_relation = max(-0.7, min(0.7, initial_relation))  # Cap initial relations
            
            self.relations[other_civ.id] = initial_relation
            
            # Log the first contact
            self._add_event(f"First contact with {other_civ.name} - initial relations: {initial_relation:.2f}")
            
            # First contact is a major event - potential for war or unification
            self._evaluate_first_contact(other_civ, initial_relation)
            
            return
            
        # Update existing relations based on interactions
        current_relation = self.relations[other_civ.id]
        
        # Random drift in relations over time
        drift = random.uniform(-0.05, 0.05)
        
        # Territory pressure affects relations (civs don't like neighbors getting too big)
        territory_ratio = len(other_civ.territory) / max(1, len(self.territory))
        territory_pressure = 0
        if territory_ratio > 2:
            territory_pressure = -0.1  # They're much bigger than us, we're threatened
        elif territory_ratio < 0.5:
            territory_pressure = 0.05  # They're much smaller, we don't fear them
            
        # Technology difference
        tech_difference = other_civ.technology - self.technology
        tech_factor = 0
        if abs(tech_difference) > 100:
            if tech_difference > 0:
                tech_factor = -0.05  # They're more advanced, we're threatened
            else:
                tech_factor = 0.05  # We're more advanced, we're confident
                
        # Update relation
        new_relation = current_relation + drift + territory_pressure + tech_factor
        new_relation = max(-1.0, min(1.0, new_relation))  # Constrain to -1.0 to 1.0
        self.relations[other_civ.id] = new_relation
        
        # Consider major actions based on relations
        if new_relation < -0.7:
            # Very negative relations might lead to war
            if not hasattr(self, 'at_war_with') or other_civ.id not in self.at_war_with:
                # Higher chance of war for aggressive civs, lower for peaceful
                war_threshold = 0.3
                if self._has_trait(CivilizationTrait.AGGRESSIVE):
                    war_threshold = 0.5
                elif self._has_trait(CivilizationTrait.PEACEFUL):
                    war_threshold = 0.1
                    
                if random.random() < war_threshold:
                    self._declare_war(other_civ)
                    
        elif new_relation > 0.7:
            # Very positive relations might lead to unification or alliance
            # Unification is a major, rare event
            unification_threshold = 0.05  # Base 5% chance
            
            # Adjust based on traits
            if self._has_trait(CivilizationTrait.PEACEFUL) and other_civ._has_trait(CivilizationTrait.PEACEFUL):
                unification_threshold = 0.1  # 10% chance if both peaceful
                
            if self._has_trait(CivilizationTrait.ISOLATIONIST) or other_civ._has_trait(CivilizationTrait.ISOLATIONIST):
                unification_threshold = 0.01  # Very unlikely if either is isolationist
            
            # Adjust based on relative size
            size_ratio = self.population / max(1, other_civ.population)
            if 0.5 <= size_ratio <= 2.0:
                # More likely if civilizations are of comparable size
                unification_threshold *= 2
            
            if random.random() < unification_threshold:
                self._propose_unification(other_civ)
        
        elif 0.3 <= new_relation <= 0.7:
            # Positive relations might lead to trade
            trade_threshold = 0.3
            if self._has_trait(CivilizationTrait.TRADING) or other_civ._has_trait(CivilizationTrait.TRADING):
                trade_threshold = 0.6
                
            if random.random() < trade_threshold:
                self._engage_trade(other_civ)

    def _evaluate_first_contact(self, other_civ, initial_relation):
        """Evaluate what happens on first contact between civilizations"""
        # This is a major event - could be peaceful, hostile, or neutral
        
        # Check aggressive traits - much higher chance of immediate conflict
        war_chance = 0.1  # Base chance
        
        if self._has_trait(CivilizationTrait.AGGRESSIVE) or other_civ._has_trait(CivilizationTrait.AGGRESSIVE):
            war_chance = 0.3  # Higher if either is aggressive
            
        if self._has_trait(CivilizationTrait.AGGRESSIVE) and other_civ._has_trait(CivilizationTrait.AGGRESSIVE):
            war_chance = 0.6  # Much higher if both aggressive
        
        # Peaceful traits reduce war chance
        if self._has_trait(CivilizationTrait.PEACEFUL) or other_civ._has_trait(CivilizationTrait.PEACEFUL):
            war_chance *= 0.5  # Reduce by half if either is peaceful
            
        if self._has_trait(CivilizationTrait.PEACEFUL) and other_civ._has_trait(CivilizationTrait.PEACEFUL):
            war_chance *= 0.2  # Reduce to 20% if both are peaceful
        
        # Check for immediate war
        if initial_relation < -0.4 and random.random() < war_chance:
            self._declare_war(other_civ)
            return
        
        # Check for immediate unification (rare but possible with very aligned civilizations)
        if initial_relation > 0.5:
            # Unification is more complex - depends on relative size and traits
            unification_chance = 0.05  # Base 5% chance
            
            # Very small chance unless both have compatible traits
            if self._has_trait(CivilizationTrait.PEACEFUL) and other_civ._has_trait(CivilizationTrait.PEACEFUL):
                unification_chance = 0.15
            
            # Size similarity check (unification more likely between similar-sized civs)
            size_ratio = self.population / max(1, other_civ.population)
            if size_ratio < 0.3 or size_ratio > 3.0:
                unification_chance *= 0.2  # Very unlikely if big size difference
                
            # Cultural/belief similarity check
            belief_similarity = self.belief_system.get_similarity(other_civ.belief_system)
            if belief_similarity > 0.7:  # Very similar beliefs
                unification_chance *= 2
            
            if random.random() < unification_chance:
                self._propose_unification(other_civ)
                return
                
        # Most common outcome - neutral/mixed first contact
        reaction = "neutral"
        if initial_relation > 0.3:
            reaction = "positive"
        elif initial_relation < -0.3:
            reaction = "tense"
            
        self._add_event(f"First contact with {other_civ.name} established - {reaction} relations")
    
    def _declare_war(self, other_civ):
        """Declare war on another civilization"""
        # Initialize war state if doesn't exist
        if not hasattr(self, 'at_war_with'):
            self.at_war_with = set()
            
        # Add to war list
        self.at_war_with.add(other_civ.id)
        
        # Set reciprocal war state for other civ
        if not hasattr(other_civ, 'at_war_with'):
            other_civ.at_war_with = set()
        other_civ.at_war_with.add(self.id)
        
        # Set relations to minimum
        self.relations[other_civ.id] = -1.0
        other_civ.relations[self.id] = -1.0
        
        # Log the event
        war_desc = f"War declared between {self.name} and {other_civ.name}"
        self._add_event(war_desc)
        other_civ._add_event(war_desc)
        
        # War continues until peace is made or one side is conquered
        # This will be processed in the simulation update
        
    def _propose_unification(self, other_civ):
        """Propose unification between civilizations"""
        # Determine which civilization will be dominant in the merger
        # Generally the larger or more advanced one
        our_score = self.population * (1 + self.technology / 1000)
        their_score = other_civ.population * (1 + other_civ.technology / 1000)
        
        if our_score >= their_score:
            dominant_civ = self
            absorbed_civ = other_civ
        else:
            dominant_civ = other_civ
            absorbed_civ = self
        
        # Create unified name
        unified_name = f"United {dominant_civ.name}"
        
        # Log the event for both civilizations
        unification_desc = f"{dominant_civ.name} and {absorbed_civ.name} have unified to form {unified_name}"
        self._add_event(unification_desc)
        other_civ._add_event(unification_desc)
        
        # Merge territories
        dominant_civ.territory = dominant_civ.territory.union(absorbed_civ.territory)
        
        # Merge populations
        dominant_civ.population += absorbed_civ.population
        
        # Merge cities
        for pos, city in absorbed_civ.cities.items():
            if pos not in dominant_civ.cities:
                dominant_civ.cities[pos] = city
            else:
                # If both have a city at the same position, combine them
                dominant_civ.cities[pos]["population"] += city["population"]
        
        # Merge resources
        for resource in dominant_civ.resources:
            dominant_civ.resources[resource] += absorbed_civ.resources.get(resource, 0)
        
        # Average technology levels (with dominant civ weighted more)
        dominant_civ.technology = (dominant_civ.technology * 2 + absorbed_civ.technology) / 3
        
        # Update name to reflect unification
        dominant_civ.name = unified_name
        
        # Mark the absorbed civilization as collapsed
        absorbed_civ.has_collapsed = True
        absorbed_civ.population = 0
        absorbed_civ.territory = set()
        absorbed_civ.cities = {}
        
        # Return true to indicate a major event occurred
        return True
    
    def _engage_trade(self, other_civ):
        """Engage in trade with another civilization"""
        # Simple trade simulation
        resource_types = list(self.resources.keys())
        trade_resource = random.choice(resource_types)
        
        trade_amount = min(10, self.resources[trade_resource] * 0.1)
        self.resources[trade_resource] -= trade_amount
        other_civ.resources[trade_resource] += trade_amount
        
        # Get something in return
        return_resource = random.choice([r for r in resource_types if r != trade_resource])
        return_amount = min(10, other_civ.resources[return_resource] * 0.1)
        
        other_civ.resources[return_resource] -= return_amount
        self.resources[return_resource] += return_amount
        
        # Improve relations slightly
        self.relations[other_civ.id] = min(1.0, self.relations[other_civ.id] + 0.05)
        other_civ.relations[self.id] = min(1.0, other_civ.relations[self.id] + 0.05)
        
        self._add_event(f"Traded {trade_amount:.1f} {trade_resource} for {return_amount:.1f} {return_resource} with {other_civ.name}")
        other_civ._add_event(f"Traded {return_amount:.1f} {return_resource} for {trade_amount:.1f} {trade_resource} with {self.name}")
    
    def _has_trait(self, trait):
        """Check if civilization has a specific trait"""
        return trait in self.traits
    
    def has_territory_at(self, position):
        """Check if civilization has territory at a position"""
        return position in self.territory
    
    def _add_event(self, description):
        """Add an event to the civilization's event log"""
        self.event_log.append({"tick": self.age, "description": description})
    
    def get_status(self):
        """Get a summary of the civilization's current status"""
        return {
            "id": self.id,
            "name": self.name,
            "population": self.population,
            "age": self.age,
            "territory_size": len(self.territory),
            "traits": self.traits,
            "belief_system": {
                "name": self.belief_system.name,
                "values": self.belief_system.values,
                "foreign_stance": self.belief_system.foreign_stance
            },
            "technology": self.technology,
            "resources": self.resources
        }
    
    def _initialize_starting_territory(self):
        """Initialize the civilization's starting territory with some surrounding land"""
        # Start with the center position
        self.territory.add(self.position)
        
        # Add some surrounding territory based on a small radius (3-5 tiles)
        radius = random.randint(3, 5)  # Increased radius for more starting territory
        x0, y0 = self.position
        
        # Count how many tiles we add
        added_tiles = 1  # Start with 1 for the center position
        
        for x in range(x0 - radius, x0 + radius + 1):
            for y in range(y0 - radius, y0 + radius + 1):
                # Only add if within world bounds and is land
                if self.world.is_valid_position((x, y)):
                    terrain = self.world.get_terrain_at((x, y))
                    # Check if it's land, forest, or desert (not water or mountain)
                    if terrain in [1, 3, 4]:  # Land, Forest, Desert
                        # Add with decreasing probability based on distance from center
                        distance = ((x - x0) ** 2 + (y - y0) ** 2) ** 0.5
                        if distance <= 2 or random.random() < (2.0 - distance / radius):
                            self.territory.add((x, y))
                            added_tiles += 1
        
        print(f"Initialized {self.name} with {added_tiles} territory tiles") 