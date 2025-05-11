"""
simulation module for civ simulator
"""
import random
import json
import pickle
import time
import math
from src.civilization import Civilization, CivilizationTrait
from src.events import EventLogger

class Simulation:
    def __init__(self, world):
        self.world = world
        self.tick_count = 0
        self.event_logger = EventLogger()
        self.year = 0  # each tick is a year
        self.history = []  # store world state snapshots for history
        self.paused = False
        
        # major event tracking
        self.major_events = []
        self.auto_pause_on_events = True  # can be toggled by the user
        self.max_civilizations = 7 # max number of civs allowed
    
    def initialize(self, num_civs=5):
        """initialize the simulation with a number of civilizations"""
        # make sure num_civs doesn't exceed max_civilizations
        actual_num_civs = min(num_civs, self.max_civilizations)
        if num_civs > self.max_civilizations:
            print(f"Warning: Requested {num_civs} civilizations, but maximum is {self.max_civilizations}. Initializing {actual_num_civs}.")

        for _ in range(actual_num_civs):
            # check if we can add more before calling add_civilization directly
            # this check is more important for god mode additions, but good practice here too
            if len(self.world.civilizations) < self.max_civilizations:
                civ = Civilization(self.world) # create a new civ object
                # the actual addition to world.civilizations happens in self.add_civilization or world.add_civilization
                # for initialization, let's assume it's okay or use a method that respects the cap
                # for now, we're calling a lower-level add that might not check the cap
                # should be safe if called from here due to the loop range
                self.world.add_civilization(civ) # direct add to the world's list
                self.event_logger.add_event(self.year, f"Civilization {civ.name} founded")
            else:
                print("Max civilization count reached during initialization.")
                break # stop trying to add more if cap is met
        
        # save initial state
        self._save_history_snapshot()
    
    def tick(self):
        """progress the simulation by one time step"""
        self.tick_count += 1
        self.year += 1
        
        # clear the major events list from previous tick
        self.major_events = []
        
        # debug info about current civs (but not too frequently)
        if self.tick_count % 50 == 0:
            print(f"Year {self.year}: {len(self.world.civilizations)} civilizations active")
            for civ in self.world.civilizations:
                print(f"  - {civ.name}: pop={civ.population}, food={civ.resources['food']:.1f}, territory={len(civ.territory)}")
        
        # process wars and battles between civs
        self._process_wars_and_battles()
        
        # remove collapsed civs before processing updates
        self._remove_collapsed_civilizations()
        
        # performance optimization: process civs in chunks
        # (each civ gets updated every turn, but not all civ tasks run every turn)
        civs_per_chunk = max(1, len(self.world.civilizations) // 3)
        chunk_start = (self.tick_count % 3) * civs_per_chunk
        chunk_end = min(chunk_start + civs_per_chunk, len(self.world.civilizations))
        
        # full civ processing (expensive operations split across turns)
        for i, civ in enumerate(self.world.civilizations[chunk_start:chunk_end]):
            # full update with territory expansion, etc.
            civ.tick(full_update=True)
            
            # record significant events
            if len(civ.event_log) > 0:
                for event in civ.event_log:
                    if event["tick"] == civ.age:  # only process new events
                        event_desc = f"{civ.name}: {event['description']}"
                        self.event_logger.add_event(self.year, event_desc)
                        
                        # check if this is a major event that should trigger pause and notification
                        # only include truly important events to reduce spam
                        if any(keyword in event['description'].lower() for keyword in 
                              ["collapsed", "war declared", "conquered", "established", "unified", "first contact"]):
                            # skip minor population changes to reduce notification spam
                            if "population" in event['description'].lower() and "significantly" in event['description'].lower():
                                # only notify for truly large population changes
                                if "increased" in event['description'].lower():
                                    if "+5000" not in event['description']:  # only notify for huge increases
                                        continue
                                elif "decreased" in event['description'].lower():
                                    if "-3000" not in event['description']:  # only notify for huge decreases
                                        continue
                                        
                            self.major_events.append({
                                "title": f"Major Event in {civ.name}",
                                "message": event['description'],
                                "civ": civ
                            })
        
        # basic updates for all civs (always run)
        for civ in self.world.civilizations:
            if chunk_start <= self.world.civilizations.index(civ) < chunk_end:
                # skip civs that got a full update already
                continue
            
            # basic update (resources, population only)
            civ.tick(full_update=False)
        
        # add protection check here to prevent young civs from dying
        for civ in self.world.civilizations:
            if hasattr(civ, 'protected_until_tick') and self.tick_count < civ.protected_until_tick:
                # make sure protected civs have enough resources
                if civ.resources["food"] < 100:
                    civ.resources["food"] = 100
                if civ.population < 50:
                    civ.population = 50
        
        # check for global events every 10 years
        if self.tick_count % 10 == 0:
            self._check_global_events()
        
        # save state every 25 years for history
        if self.tick_count % 25 == 0:
            self._save_history_snapshot()
            
        # auto-pause if there are major events and the feature is enabled
        if self.auto_pause_on_events and self.major_events and not self.paused:
            self.paused = True
            return True  # signal that we paused due to events
            
        return False  # no auto-pause occurred
    
    def _save_history_snapshot(self):
        """save a snapshot of the current world state"""
        snapshot = {
            "year": self.year,
            "civilizations": [civ.get_status() for civ in self.world.civilizations]
        }
        self.history.append(snapshot)
    
    def _check_global_events(self):
        """check for global events that affect multiple civilizations"""
        # random chance for natural disasters
        if random.random() < 0.1:  # 10% chance every 10 years
            self._trigger_natural_disaster()
        
        # check for civilization collapse
        self._check_civilization_collapse()
    
    def _trigger_natural_disaster(self):
        """trigger a random natural disaster"""
        disaster_types = ["earthquake", "flood", "drought", "volcanic_eruption", "disease"]
        disaster = random.choice(disaster_types)
        
        # select affected area
        x = random.randint(0, self.world.width - 1)
        y = random.randint(0, self.world.height - 1)
        radius = random.randint(3, 8)  # affected area radius
        
        # find affected civilizations
        affected_civs_initial = []
        for civ_candidate in self.world.civilizations:
            for pos in civ_candidate.territory:
                dx = abs(pos[0] - x)
                dy = abs(pos[1] - y)
                if (dx*dx + dy*dy) <= radius*radius:  # within circle
                    affected_civs_initial.append(civ_candidate)
                    break
        
        if not affected_civs_initial:
            return

        disaster_name = disaster.replace("_", " ").title()
        event_desc = f"Natural Disaster: {disaster_name} in region around ({x}, {y})"
        self.event_logger.add_event(self.year, event_desc)

        # Calculate effects and prepare major event message
        processed_affected_civs = []
        total_population_loss_for_single_civ_message = 0

        # Temporarily calculate loss for the first civ if only one is affected, for the message
        # The actual effects are applied in the main loop below
        if len(affected_civs_initial) == 1:
            civ = affected_civs_initial[0]
            temp_affected_territory = 0
            temp_affected_cities_in_radius = []
            for pos in civ.territory:
                dx_pos = abs(pos[0] - x)
                dy_pos = abs(pos[1] - y)
                if (dx_pos*dx_pos + dy_pos*dy_pos) <= radius*radius:
                    temp_affected_territory += 1
                    if pos in civ.cities:
                        temp_affected_cities_in_radius.append(pos)
            
            if temp_affected_territory > 0: # Civ must have territory in the disaster zone
                temp_impact_ratio = temp_affected_territory / max(1, len(civ.territory))
                if disaster == "earthquake" or disaster == "volcanic_eruption":
                    temp_city_pop_loss = 0
                    for city_pos in temp_affected_cities_in_radius:
                        city_pop = civ.cities[city_pos]["population"]
                        loss = int(city_pop * 0.05)
                        temp_city_pop_loss += loss
                    non_city_population = civ.population - sum(c["population"] for c in civ.cities.values())
                    temp_general_pop_loss = int(non_city_population * temp_impact_ratio * random.uniform(0.01, 0.05))
                    total_population_loss_for_single_civ_message = temp_city_pop_loss + temp_general_pop_loss
                elif disaster == "disease":
                    tech_factor = max(0.1, 1 - (civ.technology / 150.0))
                    base_disease_impact = random.uniform(0.15, 0.45)
                    final_disease_impact = base_disease_impact * tech_factor
                    total_population_loss_for_single_civ_message = int(civ.population * final_disease_impact * temp_impact_ratio)
                # Drought doesn't directly cause population loss in this calculation, so message remains generic or indicates 0 loss.
                # For message accuracy, explicitly set to 0 if it's a drought for the single civ message part.
                elif disaster == "drought":
                    total_population_loss_for_single_civ_message = 0


        # Construct major event message
        major_event_message = ""
        if len(affected_civs_initial) == 1 and total_population_loss_for_single_civ_message > 0 :
             # If it was a drought and loss is 0, it will fall to the 'else' generic message
            civ_name_for_message = affected_civs_initial[0].name
            major_event_message = f"A {disaster_name.lower()} has struck near ({x}, {y}), killing {total_population_loss_for_single_civ_message} people in {civ_name_for_message}."
        elif len(affected_civs_initial) == 1 and disaster == "drought": # Specific message for drought affecting one civ
            civ_name_for_message = affected_civs_initial[0].name
            major_event_message = f"A {disaster_name.lower()} (drought) has struck near ({x}, {y}), affecting {civ_name_for_message}."
        else: # Multiple civs or single civ with no direct population loss reported (e.g. flood if not implemented for pop loss)
            major_event_message = f"A {disaster_name.lower()} has struck near ({x}, {y}), affecting {len(affected_civs_initial)} civilizations."

        self.major_events.append({
            "title": f"Natural Disaster: {disaster_name}",
            "message": major_event_message,
            "civ": affected_civs_initial[0] if affected_civs_initial else None
        })
        
        # Apply actual disaster effects
        for civ in affected_civs_initial: # Iterate over the originally identified list
            affected_territory = 0
            affected_cities_in_radius = []
            for pos in civ.territory:
                dx = abs(pos[0] - x)
                dy = abs(pos[1] - y)
                if (dx*dx + dy*dy) <= radius*radius:
                    affected_territory += 1
                    if pos in civ.cities:
                        affected_cities_in_radius.append(pos)
            
            impact_ratio = affected_territory / max(1, len(civ.territory))
            total_population_loss_from_disaster = 0 # Reset for each civ
            
            # apply impact based on disaster type
            if disaster == "earthquake" or disaster == "volcanic_eruption":
                # Kill 5% of population for each city in range
                city_population_loss = 0
                for city_pos in affected_cities_in_radius:
                    city_pop = civ.cities[city_pos]["population"]
                    loss = int(city_pop * 0.05)
                    civ.cities[city_pos]["population"] = max(0, city_pop - loss)
                    city_population_loss += loss
                
                # Also apply some general territory-based population loss outside of cities
                # but ensure not to double-count city losses
                non_city_population = civ.population - sum(c["population"] for c in civ.cities.values())
                general_pop_loss = int(non_city_population * impact_ratio * random.uniform(0.01, 0.05)) # Smaller impact outside cities
                total_population_loss_from_disaster = city_population_loss + general_pop_loss
                civ.population = max(10, civ.population - total_population_loss_from_disaster)
                
                # Resources are also affected, especially in cities
                for resource in civ.resources:
                    civ.resources[resource] *= (1 - impact_ratio * random.uniform(0.1, 0.3))
                
                self.event_logger.add_event(
                    self.year, 
                    f"{civ.name} lost {total_population_loss_from_disaster} population to {disaster_name}. Cities heavily affected."
                )
            
            elif disaster == "drought":
                # mainly affects food
                food_loss = civ.resources["food"] * impact_ratio * random.uniform(0.3, 0.6)
                civ.resources["food"] = max(10, civ.resources["food"] - food_loss)
                
                self.event_logger.add_event(
                    self.year, 
                    f"{civ.name} lost {food_loss:.1f} food to {disaster_name}"
                )
            
            elif disaster == "disease":
                # Disease impact is inversely proportional to technology
                # Higher tech level means better healthcare, sanitation, and response
                tech_factor = max(0.1, 1 - (civ.technology / 150.0)) # Scale so high tech (e.g. 150+) greatly reduces impact
                # Base impact of disease, further modified by tech
                base_disease_impact = random.uniform(0.15, 0.45) 
                final_disease_impact = base_disease_impact * tech_factor
                
                population_loss = int(civ.population * final_disease_impact * impact_ratio) # impact_ratio for regional effect
                total_population_loss_from_disaster = population_loss
                civ.population = max(10, civ.population - total_population_loss_from_disaster)
                
                self.event_logger.add_event(
                    self.year, 
                    f"{civ.name} lost {total_population_loss_from_disaster} population to {disaster_name}. Tech level {civ.technology:.1f} influenced severity."
                )
    
    def _check_civilization_collapse(self):
        """check and handle civilization collapse"""
        collapsed = []
        
        for civ in self.world.civilizations:
            # skip newly created civilizations in their grace period
            if hasattr(civ, 'protected_until_tick') and self.tick_count < civ.protected_until_tick:
                # debug output for protected civilizations
                if self.tick_count % 10 == 0:
                    years_left = civ.protected_until_tick - self.tick_count
                    print(f"  * {civ.name} is protected for {years_left} more years")
                continue
            
            # More realistic civilization collapse conditions
            # Historical settlements could survive with very small populations
            # Only truly unsustainable conditions should cause collapse
            
            # Extreme starvation (virtually no food left)
            extreme_starvation = civ.resources["food"] < 2
            
            # Insufficient population for genetic diversity (~10 people is a minimum viable population)
            critical_population = civ.population < 8
            
            # Combination of low population and food issues
            combined_issues = civ.population < 15 and civ.resources["food"] < 10
            
            # Check for collapse conditions
            if extreme_starvation or critical_population or combined_issues:
                # Determine collapse reason
                if extreme_starvation:
                    reason = "starvation"
                elif critical_population:
                    reason = "critically low population"
                else:
                    reason = "unsustainable resources and population"
                
                # Record collapse
                collapse_event = f"{civ.name} has collapsed due to {reason}!"
                self.event_logger.add_event(self.year, collapse_event)
                print(collapse_event)
                civ.has_collapsed = True # mark as collapsed
                collapsed.append(civ)
                
                # add to major events for notification
                self.major_events.append({
                    "title": "Civilization Collapsed!",
                    "message": collapse_event,
                    "civ": civ # pass the collapsed civ object
                })
        
        # remove collapsed civilizations
        for civ in collapsed:
            self.world.civilizations.remove(civ)
    
    def add_civilization(self, position=None):
        """Add a new civilization, respecting the maximum limit."""
        if len(self.world.civilizations) >= self.max_civilizations:
            print(f"Cannot add new civilization: Maximum count of {self.max_civilizations} reached.")
            # Consider throwing an exception or returning a specific value to be handled by UI
            raise ValueError(f"Maximum civilization count ({self.max_civilizations}) reached.")

        new_civ = Civilization(self.world) # Create the civ object
        
        # Handle position parameter - check if world.add_civilization accepts position
        try:
            # Try adding with position param
            self.world.add_civilization(new_civ, position=position)
        except TypeError:
            # Fall back to standard add without position
            self.world.add_civilization(new_civ)
            # Manually set position if possible
            if position and hasattr(new_civ, 'position'):
                new_civ.position = position
        
        self.event_logger.add_event(self.year, f"Civilization {new_civ.name} founded by intervention.")
        print(f"Civilization {new_civ.name} added. Total: {len(self.world.civilizations)}")
        
        # Add a short protection period for newly added civilizations
        new_civ.protected_until_tick = self.tick_count + 20  # Protected for 20 ticks (years)
        print(f"  - {new_civ.name} is protected for 20 years.")

        # Add to major events for notification
        self.major_events.append({
            "title": "New Civilization Founded!",
            "message": f"{new_civ.name} has been established by divine intervention.",
            "civ": new_civ
        })
        return new_civ
    
    def save_state(self, filename=None):
        """Save the current simulation state"""
        try:
            # Generate filename with simulation name if not provided
            if filename is None:
                timestamp = int(time.time())
                filename = f"{self.name}_{timestamp}.pickle" if hasattr(self, 'name') else f"save_game_{timestamp}.pickle"
            
            # Ensure filename has .pickle extension
            if not filename.endswith('.pickle'):
                filename = f"{filename}.pickle"
            
            # Create comprehensive save data
            save_data = {
                "tick_count": self.tick_count,
                "year": self.year,
                "event_log": self.event_logger.get_all_events(),
                "history": self.history,
                "world_data": {
                    "width": self.world.width,
                    "height": self.world.height,
                    "terrain": self.world.terrain,
                    "resources": self.world.resources,
                },
                "simulation_name": self.name if hasattr(self, 'name') else "Unnamed Simulation",
                "civilizations": [],
                "auto_pause_on_events": self.auto_pause_on_events
            }
            
            # Save all civilization data
            for civ in self.world.civilizations:
                civ_data = {
                    "id": civ.id,
                    "name": civ.name,
                    "position": civ.position,
                    "territory": list(civ.territory),
                    "cities": civ.cities,
                    "population": civ.population,
                    "resources": civ.resources,
                    "technology": civ.technology,
                    "traits": civ.traits,
                    "age": civ.age,
                    "event_log": civ.event_log,
                    "belief_system": {
                        "name": civ.belief_system.name,
                        "values": civ.belief_system.values,
                        "foreign_stance": civ.belief_system.foreign_stance
                    },
                    "relations": civ.relations
                }
                
                # Check for war state
                if hasattr(civ, 'at_war_with'):
                    civ_data["at_war_with"] = civ.at_war_with
                
                # Check for protection status
                if hasattr(civ, 'protected_until_tick'):
                    civ_data["protected_until_tick"] = civ.protected_until_tick
                
                save_data["civilizations"].append(civ_data)
            
            # Save the data to file
            with open(f"data/{filename}", "wb") as f:
                pickle.dump(save_data, f)
                
            # Also save a readable event log as JSON
            log_filename = f"data/event_log_{self.name if hasattr(self, 'name') else 'simulation'}_{int(time.time())}.json"
            with open(log_filename, "w") as f:
                json.dump(self.event_logger.get_all_events(), f, indent=2)
                
            print(f"Game saved successfully as '{filename}'")
            return True, filename
            
        except Exception as e:
            error_msg = f"Error saving game: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def load_state(self, filename):
        """Load a simulation state"""
        try:
            # Ensure filename has .pickle extension
            if not filename.endswith('.pickle'):
                filename = f"{filename}.pickle"
                
            # Load the save data
            with open(f"data/{filename}", "rb") as f:
                save_data = pickle.load(f)
            
            # Restore simulation state
            self.tick_count = save_data["tick_count"]
            self.year = save_data["year"]
            self.event_logger.set_events(save_data["event_log"])
            self.history = save_data["history"]
            
            # Restore auto-pause setting if available
            if "auto_pause_on_events" in save_data:
                self.auto_pause_on_events = save_data["auto_pause_on_events"]
            
            # Set simulation name if available
            if "simulation_name" in save_data:
                self.name = save_data["simulation_name"]
            
            # Restore world data if available
            if "world_data" in save_data:
                world_data = save_data["world_data"]
                if world_data["width"] == self.world.width and world_data["height"] == self.world.height:
                    self.world.terrain = world_data["terrain"]
                    self.world.resources = world_data["resources"]
                else:
                    print("Warning: World dimensions in save file do not match current world. Using current terrain.")
            
            # Clear current civilizations
            self.world.civilizations = []
            
            # Restore civilizations
            from src.civilization import Civilization, BeliefSystem
            
            for civ_data in save_data["civilizations"]:
                # Create a new civilization object
                civ = Civilization(self.world, skip_init=True)
                
                # Restore basic properties
                civ.id = civ_data["id"]
                civ.name = civ_data["name"]
                civ.position = civ_data["position"]
                civ.territory = set(civ_data["territory"])
                civ.cities = civ_data["cities"]
                civ.population = civ_data["population"]
                civ.resources = civ_data["resources"]
                civ.technology = civ_data["technology"]
                civ.traits = civ_data["traits"]
                civ.age = civ_data["age"]
                civ.event_log = civ_data["event_log"]
                
                # Restore belief system
                belief_data = civ_data["belief_system"]
                civ.belief_system = BeliefSystem(belief_data["name"])
                civ.belief_system.values = belief_data["values"]
                civ.belief_system.foreign_stance = belief_data["foreign_stance"]
                
                # Restore relations
                civ.relations = civ_data["relations"]
                
                # Restore war state if present
                if "at_war_with" in civ_data:
                    civ.at_war_with = civ_data["at_war_with"]
                
                # Restore protection status if present
                if "protected_until_tick" in civ_data:
                    civ.protected_until_tick = civ_data["protected_until_tick"]
                
                # Add the civilization to the world
                self.world.civilizations.append(civ)
            
            print(f"Game loaded successfully from '{filename}'")
            print(f"Year: {self.year}, Civilizations: {len(self.world.civilizations)}")
            
            return True, "Game loaded successfully"
            
        except FileNotFoundError:
            error_msg = f"Save file '{filename}' not found"
            print(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Error loading game: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    def trigger_god_event(self, event_type, target_civ=None, position=None, magnitude=1.0):
        """Trigger a god mode event"""
        if event_type == "disaster":
            disaster_types = ["earthquake", "flood", "drought", "volcanic_eruption", "disease"]
            specific_disaster = random.choice(disaster_types)
            
            # Get a position if not specified
            if position is None:
                if target_civ:
                    # Use civ's territory center
                    territory_positions = list(target_civ.territory)
                    if territory_positions:
                        position = random.choice(territory_positions)
                    else:
                        position = target_civ.position
                else:
                    # Random position
                    position = (random.randint(0, self.world.width-1), 
                               random.randint(0, self.world.height-1))
            
            # Apply disaster at position
            radius = int(max(1,3 * magnitude)) # Ensure radius is at least 1
            x, y = position
            disaster_name_formatted = specific_disaster.replace('_', ' ').title()
            
            self.event_logger.add_event(
                self.year, 
                f"GOD EVENT: {disaster_name_formatted} at ({x}, {y}) by divine intervention!"
            )

            affected_civs_for_notification = []
            total_pop_loss_for_notification = 0

            # Apply effects to civilizations in the radius
            for civ in list(self.world.civilizations): # Iterate over a copy in case a civ collapses
                # Calculate distance from civ's core to disaster center
                # Or check overlap with territory for more accuracy
                affected_territory_count = 0
                if not civ.territory: # Skip if civ has no territory (e.g. just created)
                    continue
                
                for tile_pos in civ.territory:
                    dist_sq = (tile_pos[0] - x)**2 + (tile_pos[1] - y)**2
                    if dist_sq <= radius**2:
                        affected_territory_count += 1
                
                if affected_territory_count > 0:
                    # This civ is affected
                    if civ not in affected_civs_for_notification:
                        affected_civs_for_notification.append(civ)

                    damage_rate = random.uniform(0.1, 0.3) * magnitude * (affected_territory_count / max(1,len(civ.territory)))
                    damage_rate = min(damage_rate, 0.9) # Cap damage at 90%
                    
                    population_loss = int(civ.population * damage_rate)
                    civ.population = max(1, civ.population - population_loss)
                    total_pop_loss_for_notification += population_loss
                    
                    resource_damage = damage_rate * random.uniform(0.3, 0.7)
                    for resource in civ.resources:
                        civ.resources[resource] *= (1 - resource_damage)
                        civ.resources[resource] = max(0, civ.resources[resource])
                    
                    self.event_logger.add_event(
                        self.year, 
                        f"{civ.name} lost {population_loss} people and resources to divine {specific_disaster.replace('_', ' ')}."
                    )
            
            # Always add to major events for God Mode triggered disasters
            affected_civ_names = ", ".join([c.name for c in affected_civs_for_notification]) if affected_civs_for_notification else "No civilizations"
            self.major_events.append({
                "title": f"Divine Disaster: {disaster_name_formatted}",
                "message": f"A divinely invoked {specific_disaster.lower()} struck near ({x},{y}). {affected_civ_names} affected. Total population lost: {total_pop_loss_for_notification}.",
                "civ": affected_civs_for_notification[0] if affected_civs_for_notification else None # Primary civ for highlight
            })
        
        elif event_type == "blessing":
            if target_civ:
                # Increase resources and population
                boost = magnitude * random.uniform(0.2, 0.5)
                
                # Population boost
                population_increase = int(target_civ.population * boost)
                target_civ.population += population_increase
                
                # Resource boost
                for resource in target_civ.resources:
                    target_civ.resources[resource] *= (1 + boost)
                
                self.event_logger.add_event(
                    self.year, 
                    f"GOD EVENT: Blessing upon {target_civ.name}, population increased by {population_increase}"
                )
        
        elif event_type == "tech_boost":
            if target_civ:
                current_tech = target_civ.technology
                # Boost is 20% of current tech + 10, scaled by magnitude
                percentage_boost = current_tech * 0.20 * magnitude
                flat_boost = 10 * magnitude
                
                new_tech = current_tech + percentage_boost + flat_boost
                target_civ.technology = min(50000, new_tech)  # Cap at 50k
                
                self.event_logger.add_event(
                    self.year, 
                    f"GOD EVENT: Technology boost for {target_civ.name}, tech level increased from {current_tech:.1f} to {target_civ.technology:.1f}"
                )
        
        elif event_type == "shift_ideology":
            if target_civ:
                from src.civilization import BeliefSystem # Assuming BeliefSystem() is the random generator
                from src.civilization import CivilizationTrait # Import for re-rolling traits
                
                old_belief_name = target_civ.belief_system.name
                old_traits = list(target_civ.traits) # Save for the message

                # 1. Generate a completely new belief system
                target_civ.belief_system = BeliefSystem() 
                
                # 2. Completely re-roll civilization traits
                target_civ.traits = CivilizationTrait.get_random_traits()

                # 3. Reset relations with all other civilizations to neutral or slightly random
                for other_civ_id in list(target_civ.relations.keys()): # Iterate over a copy of keys
                    target_civ.relations[other_civ_id] = random.uniform(-0.1, 0.1) # Reset to near neutral
                    # Also update the other civ's relation towards this civ
                    other_civ_obj = next((c for c in self.world.civilizations if c.id == other_civ_id), None)
                    if other_civ_obj:
                        other_civ_obj.relations[target_civ.id] = target_civ.relations[other_civ_id]
                
                # Log the event
                self.event_logger.add_event(
                    self.year, 
                    f"GOD EVENT: {target_civ.name} underwent a profound ideological and cultural transformation from '{old_belief_name}' (Traits: {', '.join(old_traits)}) to '{target_civ.belief_system.name}' (New Traits: {', '.join(target_civ.traits)}). Relations reset."
                )
                
                # Add a notification for the user
                self.major_events.append({
                    "title": f"Total Metamorphosis in {target_civ.name}",
                    "message": f"{target_civ.name} has been entirely reshaped: New Belief is '{target_civ.belief_system.name}', new traits: {', '.join(target_civ.traits)}. All diplomatic ties reset.",
                    "civ": target_civ
                })
        
        elif event_type == "war_influence":
            if target_civ:
                target_civ.permanently_hostile_to_all = True
                # Also make their current relations very poor to kickstart conflicts
                for other_civ_id in list(target_civ.relations.keys()):
                    target_civ.relations[other_civ_id] = -0.9
                    other_civ_obj = next((c for c in self.world.civilizations if c.id == other_civ_id), None)
                    if other_civ_obj:
                        other_civ_obj.relations[target_civ.id] = -0.9
                
                self.event_logger.add_event(
                    self.year, 
                    f"GOD EVENT: {target_civ.name} has been divinely influenced to be permanently hostile and seek war with all other civilizations!"
                )
                self.major_events.append({
                    "title": f"{target_civ.name} Doomed to Eternal War!",
                    "message": f"{target_civ.name} is now compelled by divine will to wage war on any civilization it encounters.",
                    "civ": target_civ
                })
            else:
                 # If no target_civ, this event might not make sense or could pick a random one.
                 # For now, we'll assume it requires a target.
                 pass # Or log an error/feedback that a target is needed.
    
    def get_event_history(self):
        """Get the complete event history"""
        return self.event_logger.get_all_events()
    
    def get_civilization_history(self):
        """Get historical data for all civilizations"""
        return self.history
    
    def get_active_civilizations(self):
        """Get all active civilizations"""
        return self.world.civilizations
    
    def get_major_events(self):
        """Return the list of major events from the current tick"""
        return self.major_events
    
    def toggle_auto_pause(self):
        """Toggle whether the simulation auto-pauses on major events"""
        self.auto_pause_on_events = not self.auto_pause_on_events
        return self.auto_pause_on_events
    
    def _process_wars_and_battles(self):
        """Process ongoing wars and resolve battles between civilizations"""
        # Track civilizations that should be marked as collapsed after all processing
        civilizations_to_collapse = []
        
        # Process each civilization
        for civ in self.world.civilizations:
            # Skip civilizations that are already marked for collapse
            if hasattr(civ, 'has_collapsed') and civ.has_collapsed:
                continue
                
            # Skip civilizations that aren't at war
            if not hasattr(civ, 'at_war_with') or not civ.at_war_with:
                continue
            
            # Process each war this civilization is involved in
            wars_to_remove = set()
            for enemy_id in civ.at_war_with:
                # Find the enemy civilization
                enemy_civ = None
                for other_civ in self.world.civilizations:
                    if other_civ.id == enemy_id:
                        enemy_civ = other_civ
                        break
                
                if not enemy_civ or hasattr(enemy_civ, 'has_collapsed') and enemy_civ.has_collapsed:
                    # Enemy no longer exists or has collapsed, remove from war list
                    wars_to_remove.add(enemy_id)
                    continue
                
                # Only process the battle from one side to avoid duplicates
                if civ.id < enemy_id:
                    # Check if territories are adjacent (battles only occur at borders)
                    if civ._territories_adjacent(enemy_civ):
                        self._resolve_battle(civ, enemy_civ)
                    
                    # Random chance for peace treaty or continued conflict
                    if random.random() < 0.05:  # 5% chance per tick to end war
                        # End the war from both sides
                        wars_to_remove.add(enemy_id)
                        if hasattr(enemy_civ, 'at_war_with'):
                            enemy_civ.at_war_with.discard(civ.id)
                        
                        # Improve relations slightly when peace is made
                        peace_relation = -0.5 + random.random() * 0.3  # -0.5 to -0.2
                        civ.relations[enemy_id] = peace_relation
                        enemy_civ.relations[civ.id] = peace_relation
                        
                        # Log peace event
                        peace_message = f"Peace treaty signed between {civ.name} and {enemy_civ.name}"
                        civ._add_event(peace_message)
                        enemy_civ._add_event(peace_message)
                        
                        # Add to major events
                        self.major_events.append({
                            "title": "Peace Treaty",
                            "message": peace_message,
                            "civ": civ
                        })
            
            # Remove wars that have ended
            if hasattr(civ, 'at_war_with'):
                civ.at_war_with -= wars_to_remove
        
        # Remove civilizations marked for collapse
        for civ in civilizations_to_collapse:
            civ.has_collapsed = True
    
    def _resolve_battle(self, civ1, civ2):
        """Resolve a battle between two civilizations"""
        # Calculate military strength based on population, technology and traits
        strength1 = civ1.population * (1 + civ1.technology / 500)
        strength2 = civ2.population * (1 + civ2.technology / 500)
        
        # Adjust for traits
        if civ1._has_trait(CivilizationTrait.AGGRESSIVE):
            strength1 *= 1.3  # 30% bonus for aggressive civs (increased from 20%)
        if civ2._has_trait(CivilizationTrait.AGGRESSIVE):
            strength2 *= 1.3
            
        if civ1._has_trait(CivilizationTrait.PEACEFUL):
            strength1 *= 0.7  # 30% penalty for peaceful civs (increased from 20%)
        if civ2._has_trait(CivilizationTrait.PEACEFUL):
            strength2 *= 0.7
        
        # Add some randomness
        strength1 *= random.uniform(0.8, 1.2)
        strength2 *= random.uniform(0.8, 1.2)
        
        # Determine winner
        if strength1 > strength2:
            winner = civ1
            loser = civ2
            strength_ratio = strength1 / strength2
        else:
            winner = civ2
            loser = civ1
            strength_ratio = strength2 / strength1
        
        # Battle casualties - SIGNIFICANTLY INCREASED
        # War is much more devastating now
        winner_casualties = int(winner.population * random.uniform(0.03, 0.07))  # 3-7% casualties (increased)
        loser_casualties = int(loser.population * random.uniform(0.08, 0.15))   # 8-15% casualties (increased)
        
        # Apply casualties
        winner.population = max(50, winner.population - winner_casualties)
        loser.population = max(50, loser.population - loser_casualties)
        
        # Territory changes - more territory changes hands in decisive victories
        territory_gain_count = int(min(10, len(loser.territory) * 0.1 * (strength_ratio - 1)))
        
        if territory_gain_count > 0:
            # Find territories near the border that can be conquered
            border_territories = []
            for pos in loser.territory:
                x, y = pos
                # Check if this territory is on the border with the winner
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                    neighbor_pos = (x + dx, y + dy)
                    if neighbor_pos in winner.territory:
                        border_territories.append(pos)
                        break
            
            # Take border territories
            territories_taken = []
            for _ in range(min(territory_gain_count, len(border_territories))):
                if border_territories:
                    pos = random.choice(border_territories)
                    border_territories.remove(pos)
                    
                    if pos in loser.territory:
                        loser.territory.remove(pos)
                        winner.territory.add(pos)
                        territories_taken.append(pos)
                        
                        # If the position had a city, capture it
                        if pos in loser.cities:
                            city_name = loser.cities[pos]["name"]
                            city_pop = loser.cities[pos]["population"]
                            
                            # Reduce population in captured city
                            reduced_pop = int(city_pop * 0.6)  # 40% population loss in captured city (increased from 30%)
                            winner.cities[pos] = {"name": city_name, "population": reduced_pop}
                            del loser.cities[pos]
            
            # Log battle result
            if territories_taken:
                battle_result = (f"{winner.name} defeated {loser.name} in battle, gaining "
                                f"{len(territories_taken)} territories. "
                                f"{winner.name} lost {winner_casualties} population, "
                                f"{loser.name} lost {loser_casualties} population.")
                
                # Record the event
                winner._add_event(f"Won battle against {loser.name}, gained {len(territories_taken)} territories")
                loser._add_event(f"Lost battle to {winner.name}, lost {len(territories_taken)} territories")
                
                # Add to major events list
                self.major_events.append({
                    "title": "Major Battle",
                    "message": battle_result,
                    "civ": winner
                })
                
                # If the loser lost all their cities, they're conquered
                if not loser.cities:
                    conquest_message = f"{loser.name} has been conquered by {winner.name}"
                    loser._add_event(f"Our civilization has been conquered by {winner.name}")
                    winner._add_event(f"We have conquered {loser.name}")
                    
                    # Mark the loser as collapsed
                    loser.has_collapsed = True
                    
                    # Transfer all remaining territory to the winner
                    winner.territory = winner.territory.union(loser.territory)
                    loser.territory = set()
                    
                    # Transfer some population to winner
                    transferred_pop = max(10, int(loser.population * 0.5))  # Transfer 50% of remaining population
                    winner.population += transferred_pop
                    loser.population = 0
                    
                    # Add to major events
                    self.major_events.append({
                        "title": "Civilization Conquered",
                        "message": conquest_message,
                        "civ": winner
                    })
    
    def _remove_collapsed_civilizations(self):
        """Remove collapsed civilizations from the active list"""
        active_civs = []
        
        for civ in self.world.civilizations:
            if not hasattr(civ, 'has_collapsed') or not civ.has_collapsed:
                active_civs.append(civ)
            else:
                # Log the collapse if it's new
                if not hasattr(civ, 'collapse_logged') or not civ.collapse_logged:
                    self.event_logger.add_event(
                        self.year, 
                        f"Civilization {civ.name} has collapsed"
                    )
                    civ.collapse_logged = True
        
        # Update world's civilization list
        self.world.civilizations = active_civs 

    def _check_civilization_interactions(self):
        """Check for interactions between civilizations, including wars and potential unifications"""
        # Check every pair of civilizations
        for i, civ1 in enumerate(self.world.civilizations):
            for j, civ2 in enumerate(self.world.civilizations[i+1:]):
                # Skip if either civilization has collapsed
                if hasattr(civ1, 'has_collapsed') and civ1.has_collapsed:
                    continue
                if hasattr(civ2, 'has_collapsed') and civ2.has_collapsed:
                    continue
                
                # Skip if they're already at war
                if hasattr(civ1, 'at_war_with') and civ2.id in civ1.at_war_with:
                    continue
                
                # Check if territories are adjacent, indicating potential first contact
                if civ1._territories_adjacent(civ2):
                    # First contact - initialize relations if they don't exist
                    if civ2.id not in civ1.relations:
                        # Determine initial relations based on belief systems and traits
                        belief_compatibility = self._calculate_belief_compatibility(civ1, civ2)
                        trait_compatibility = self._calculate_trait_compatibility(civ1, civ2)
                        
                        # Calculate base initial relation
                        base_relation = (belief_compatibility * 0.7) + (trait_compatibility * 0.3)
                        
                        # Add randomness
                        initial_relation = base_relation + random.uniform(-0.2, 0.2)
                        
                        # Clamp to valid range
                        initial_relation = max(-1.0, min(1.0, initial_relation))
                        
                        # Set mutual relations
                        civ1.relations[civ2.id] = initial_relation
                        civ2.relations[civ1.id] = initial_relation
                        
                        # Track first contact
                        first_contact_message = f"{civ1.name} made first contact with {civ2.name}"
                        civ1._add_event(f"Made first contact with {civ2.name}")
                        civ2._add_event(f"Made first contact with {civ1.name}")
                        
                        # Add to major events
                        self.major_events.append({
                            "title": "First Contact",
                            "message": first_contact_message,
                            "civ": civ1
                        })
                        
                        # Determine war likelihood on first contact
                        # Hostile stance and opposing belief systems greatly increase war chance
                        war_chance = 0.1  # Base war chance on contact
                        
                        # Belief system stance dramatically affects war chance
                        if civ1.belief_system.foreign_stance == "hostile" or civ2.belief_system.foreign_stance == "hostile":
                            war_chance += 0.3  # 30% more likely with hostile stance
                        
                        # Opposing belief values increase war chance
                        if belief_compatibility < -0.5:  # Very incompatible beliefs
                            war_chance += 0.4  # 40% more likely with opposing beliefs
                            
                        # Aggressive trait increases war chance
                        if civ1._has_trait(CivilizationTrait.AGGRESSIVE):
                            war_chance += 0.15
                        if civ2._has_trait(CivilizationTrait.AGGRESSIVE):
                            war_chance += 0.15
                        
                        # Peaceful trait reduces war chance
                        if civ1._has_trait(CivilizationTrait.PEACEFUL):
                            war_chance -= 0.15
                        if civ2._has_trait(CivilizationTrait.PEACEFUL):
                            war_chance -= 0.15
                        
                        # Declare war if the chance threshold is met
                        if random.random() < war_chance:
                            self._start_war(civ1, civ2, "ideological differences")
                    
                    # Otherwise, update relations between existing contacts
                    else:
                        current_relation = civ1.relations[civ2.id]
                        
                        # Check for potential unification of friendly civilizations
                        if current_relation > 0.8:  # Very friendly relations
                            # Unification is more likely with compatible beliefs and traits
                            belief_compatibility = self._calculate_belief_compatibility(civ1, civ2)
                            trait_compatibility = self._calculate_trait_compatibility(civ1, civ2)
                            
                            # Calculate unification chance
                            unification_chance = (belief_compatibility + trait_compatibility) / 4  # Base chance
                            
                            # Both civs must have compatible foreign stances for easy unification
                            if (civ1.belief_system.foreign_stance == "open" and 
                                civ2.belief_system.foreign_stance == "open"):
                                unification_chance += 0.2
                                
                            # If both have the same belief system name, even more likely
                            if civ1.belief_system.name == civ2.belief_system.name:
                                unification_chance += 0.3
                            
                            # Execute unification if chance threshold is met
                            if random.random() < unification_chance:
                                self._unify_civilizations(civ1, civ2)
                                return  # End processing as one civ no longer exists
                        
                        # Check for war declaration between existing contacts
                        elif current_relation < -0.7:  # Very negative relations
                            war_chance = 0.15  # Base war chance for hostile relations
                            
                            # Increase war chance for opposing belief systems
                            belief_compatibility = self._calculate_belief_compatibility(civ1, civ2)
                            if belief_compatibility < -0.5:  # Very incompatible beliefs
                                war_chance += 0.2
                                
                            # Aggressive trait increases war chance
                            if civ1._has_trait(CivilizationTrait.AGGRESSIVE):
                                war_chance += 0.1
                            if civ2._has_trait(CivilizationTrait.AGGRESSIVE):
                                war_chance += 0.1
                            
                            # Declare war if the chance threshold is met
                            if random.random() < war_chance:
                                self._start_war(civ1, civ2, "long-standing hostility")

    def _unify_civilizations(self, civ1, civ2):
        """Unify two compatible civilizations into one stronger civilization"""
        # Determine which civ is larger (by population)
        if civ1.population > civ2.population:
            primary_civ = civ1
            secondary_civ = civ2
        else:
            primary_civ = civ2
            secondary_civ = civ1
        
        # Unification message
        unification_message = f"{primary_civ.name} and {secondary_civ.name} have unified under the banner of {primary_civ.name}"
        
        # Record the event
        primary_civ._add_event(f"Unified with {secondary_civ.name}, absorbing their people and territory")
        secondary_civ._add_event(f"Unified with {primary_civ.name}, becoming part of their civilization")
        
        # Transfer territory and cities
        primary_civ.territory = primary_civ.territory.union(secondary_civ.territory)
        for pos, city in secondary_civ.cities.items():
            primary_civ.cities[pos] = city
        
        # Transfer population (80% survival rate during integration)
        transferred_population = int(secondary_civ.population * 0.8)
        primary_civ.population += transferred_population
        
        # Transfer some resources (80% efficiency)
        for resource in secondary_civ.resources:
            primary_civ.resources[resource] += secondary_civ.resources[resource] * 0.8
        
        # Blend traits and belief systems
        # Each trait from the secondary civ has a chance to be added if not already present
        for trait in secondary_civ.traits:
            if trait not in primary_civ.traits and random.random() < 0.5:
                primary_civ.traits.append(trait)
                # Keep max 5 traits
                if len(primary_civ.traits) > 5:
                    primary_civ.traits.pop(0)
        
        # Add the event to the secondary civ's history
        self.event_logger.add_event(
            self.year, 
            f"{secondary_civ.name} unified with {primary_civ.name}"
        )
        
        # Mark the secondary civ as collapsed
        secondary_civ.has_collapsed = True
        
        # Add to major events
        self.major_events.append({
            "title": "Civilizations United",
            "message": unification_message,
            "civ": primary_civ
        })

    def _calculate_belief_compatibility(self, civ1, civ2):
        """Calculate compatibility between two civilizations' belief systems
        Returns a value between -1 (completely opposed) and 1 (perfectly compatible)"""
        # Start with neutral compatibility
        compatibility = 0.0
        
        # Foreign stance heavily impacts compatibility
        stance1 = civ1.belief_system.foreign_stance
        stance2 = civ2.belief_system.foreign_stance
        
        # Hostile stance dramatically reduces compatibility
        if stance1 == "hostile" and stance2 == "hostile":
            compatibility -= 0.6  # Both hostile to others
        elif stance1 == "hostile" or stance2 == "hostile":
            compatibility -= 0.4  # One hostile stance
        
        # Open stance improves compatibility
        if stance1 == "open" and stance2 == "open":
            compatibility += 0.6  # Both open to others
        elif stance1 == "open" or stance2 == "open":
            compatibility += 0.3  # One open stance
        
        # Compare belief values - opposing values reduce compatibility
        for value in civ1.belief_system.values:
            if value in civ2.belief_system.values:
                # Calculate how similar the values are (0 to 1)
                value_difference = abs(civ1.belief_system.values[value] - civ2.belief_system.values[value])
                
                # For core opposing values, increase the importance of differences
                if value in ["peace", "war"]:
                    # Opposing views on peace/war are critical
                    if civ1.belief_system.values[value] > 0.7 and civ2.belief_system.values[value] < 0.3:
                        compatibility -= 0.4  # Major difference in core value
                    elif civ1.belief_system.values[value] < 0.3 and civ2.belief_system.values[value] > 0.7:
                        compatibility -= 0.4  # Major difference in core value
                    else:
                        # Smaller differences have less impact
                        compatibility -= value_difference * 0.2
                else:
                    # Other values have less impact
                    compatibility -= value_difference * 0.1
        
        # Ensure final value is in range [-1, 1]
        return max(-1.0, min(1.0, compatibility))

    def _calculate_trait_compatibility(self, civ1, civ2):
        """Calculate compatibility between two civilizations' traits
        Returns a value between -1 (completely opposed) and 1 (perfectly compatible)"""
        # Start with neutral compatibility
        compatibility = 0.0
        
        # Some traits are directly opposed
        opposed_pairs = [
            (CivilizationTrait.AGGRESSIVE, CivilizationTrait.PEACEFUL),
            (CivilizationTrait.EXPANSIONIST, CivilizationTrait.ISOLATIONIST),
            # Add more opposed traits if needed
        ]
        
        # Check for direct conflicts in traits
        for trait1, trait2 in opposed_pairs:
            if civ1._has_trait(trait1) and civ2._has_trait(trait2):
                compatibility -= 0.4  # Major conflict in traits