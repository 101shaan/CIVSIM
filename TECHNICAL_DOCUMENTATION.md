# CIVSIM: Watch societies evolve, compete and collapse

## Project Overview

Throughout my development of CIVSIM, I aimed to create a sophisticated simulation that captures the intricate dynamics of civilization development. This document outlines the technical implementation details and design decisions I made while building this system. The project represents thousands of hours of research, development, and optimization to create what I believe is one of the most detailed civilization simulations available.

## Technical Foundation

I chose the following technology stack after careful consideration of performance requirements and development flexibility:

- Python 3.13 as the core engine for its powerful data processing capabilities
- Pygame 2.5.2 for rendering, giving me low-level control over graphics
- NumPy 1.26.0 for efficient numerical computations
- Matplotlib 3.8.0 and Seaborn 0.13.0 for data visualization
- OpenAI's GPT-4 API for dynamic narrative generation

## Core Systems Architecture

### World Generation System

The world generation system employs a sophisticated multi-layered approach that I developed through extensive testing:

1. **Terrain Generation Algorithm**
   I implemented a modified cellular automata with the following characteristics:
   ```python
   # Base terrain generation parameters
   INITIAL_LAND_PROBABILITY = 0.45
   MOUNTAIN_PROPAGATION_CHANCE = 0.70
   FOREST_INITIAL_COVERAGE = 0.03
   DESERT_FORMATION_THRESHOLD = 0.65
   ```

   The system uses a multi-pass approach:
   1. Initial landmass generation
   2. Coastline smoothing (3 passes)
   3. Mountain range formation
   4. Forest growth simulation
   5. Desert climate modeling

2. **Resource Distribution System**
   I developed a sophisticated resource placement algorithm that considers:
   - Geological realism (metal/stone concentrations)
   - Historical accuracy (food source distribution)
   - Gameplay balance (resource accessibility)

   Resource abundance follows these carefully tuned ratios:
   ```python
   RESOURCE_ABUNDANCE = {
       'mountains': {
           'metal': (0.5, 1.0),
           'stone': (0.6, 0.9)
       },
       'forest': {
           'food': (0.7, 1.0),
           'wood': (0.8, 1.0)
       },
       'coastal': {
           'food': (0.4, 0.8),
           'fish': (0.6, 0.9)
       }
   }
   ```

### Population Dynamics System

This system represents one of my most significant technical achievements. After studying historical demographic patterns and implementing multiple iterations, I developed a sophisticated growth model:

1. **Core Growth Formula**
   ```python
   growth_rate = (base_rate * size_factor * tech_factor * trait_factor * 
                  protection_factor * expansion_factor * resource_factor)
   ```

   Each factor is carefully calculated:
   ```python
   # Base rate calculation
   if food_per_person >= 1.5:
       base_rate = random.uniform(0.01, 0.02)  # Abundant food
   elif food_per_person >= 1.0:
       base_rate = random.uniform(0.005, 0.015)  # Sufficient food
   elif food_per_person >= 0.75:
       base_rate = random.uniform(0.003, 0.008)  # Adequate food
   elif food_per_person >= 0.5:
       base_rate = random.uniform(-0.001, 0.003)  # Minimal food
   else:
       base_rate = random.uniform(-0.015, -0.005)  # Shortage
   ```

2. **Demographic Transition Model**
   I implemented a sophisticated demographic transition model that mirrors real-world population patterns:

   ```python
   def calculate_size_factor(population):
       if population < 100:
           return 1.3  # Early tribal phase
       elif population < 10000:
           return 1.0  # Early settlement phase
       elif population < 50000:
           return 0.8  # Agricultural phase
       elif population < 100000:
           return 0.6  # Early industrial
       elif population < 500000:
           return 0.4  # Industrial
       else:
           return 0.2  # Post-industrial
   ```

3. **Resource Management**
   The resource system I developed includes sophisticated gathering and consumption mechanics:

   ```python
   # Resource gathering efficiency calculation
   efficiency = (1.0 + math.log(technology + 1) / 20) * 
                (1.0 + young_civilization_bonus) *
                (1.0 + trait_modifiers)
   ```

### Territory Expansion System

I developed an expansion system that balances historical accuracy with engaging gameplay:

1. **Expansion Decision Algorithm**
   ```python
   expansion_threshold = base_threshold * math.sqrt(territory_size) / 2
   
   # Threshold adjustments
   if traits.EXPANSIONIST:
       expansion_threshold *= 0.375  # 30/80 ratio
   elif traits.ISOLATIONIST:
       expansion_threshold *= 1.875  # 150/80 ratio
   ```

2. **Territory Selection Process**
   I implemented a sophisticated selection algorithm that considers:
   - Resource availability (weighted scoring)
   - Defensive potential (terrain analysis)
   - Economic viability (trade route potential)
   - Strategic value (chokepoint analysis)

### Combat System

The combat system I developed incorporates both historical research and balanced gameplay mechanics:

1. **Battle Resolution Algorithm**
   ```python
   def calculate_military_strength(civilization):
       base_strength = civilization.population * (1 + civilization.technology/500)
       terrain_modifier = get_terrain_modifier(civilization.territory)
       trait_modifier = calculate_trait_modifiers(civilization.traits)
       
       return base_strength * terrain_modifier * trait_modifier * 
              random.uniform(0.8, 1.2)  # Combat uncertainty
   ```

2. **Casualty Calculation**
   I implemented historically-inspired casualty rates with gameplay considerations:
   ```python
   winner_casualties = int(winner.population * random.uniform(0.03, 0.07))
   loser_casualties = int(loser.population * random.uniform(0.08, 0.15))
   ```

### Diplomatic Relations System

My diplomatic system models complex international relations:

1. **Relationship Evolution**
   ```python
   new_relation = (current_relation +
                   random.uniform(-0.05, 0.05) +  # Random drift
                   calculate_territory_pressure() +
                   calculate_tech_factor() +
                   calculate_belief_compatibility())
   ```

2. **War Probability System**
   I developed a nuanced war initiation system:
   ```python
   war_chance = 0.1  # Base chance
   if belief_compatibility < -0.5:
       war_chance += 0.4
   for trait in [AGGRESSIVE, PEACEFUL]:
       war_chance += trait_modifiers[trait]
   ```

### Technology System

The technology system I implemented models scientific and cultural advancement:

1. **Research Progression**
   ```python
   tech_growth = (base_rate * 
                  (1 + knowledge_bonus) * 
                  (1 + population_factor) * 
                  stability_modifier)
   ```

2. **Application Areas**
   I developed technology impacts across multiple domains:
   - Resource gathering efficiency
   - Military capabilities
   - Population capacity
   - Diplomatic influence

### City Management System

My city system implements sophisticated urban development patterns:

1. **City Founding Logic**
   ```python
   def calculate_city_viability(position):
       score = 0
       score += 2 if has_water_access(position) else 0
       score += terrain_values[get_terrain(position)]
       score += calculate_resource_value(position)
       score += strategic_position_value(position)
       return score
   ```

2. **Population Distribution**
   I implemented dynamic population distribution based on:
   - Resource availability
   - Strategic importance
   - Terrain suitability
   - Economic potential

## Performance Optimizations

Through extensive profiling and optimization, I implemented several critical performance improvements:

1. **Territory Processing**
   - Chunk-based updates using spatial hashing
   - Efficient territory border detection
   - Cached neighbor calculations

2. **Resource Calculation**
   - Batch processing for resource updates
   - Optimized pathfinding for resource gathering
   - Smart caching of resource availability

3. **Graphics Rendering**
   - Surface caching for static elements
   - Dirty rectangle tracking
   - Viewport culling for large maps

## Unique Features

Some of the advanced features I'm particularly proud of implementing:

1. **God Mode Interface**
   I developed a comprehensive divine intervention system:
   ```python
   class DivineIntervention:
       def trigger_disaster(self, type, magnitude, area)
       def modify_technology(self, civilization, amount)
       def influence_relations(self, civ1, civ2, change)
       def alter_resources(self, civilization, resources)
   ```

2. **Dynamic Narrative Generation**
   I integrated GPT-4 for procedural story generation:
   ```python
   class LoreGenerator:
       def generate_civilization_history(self, civ)
       def create_event_narrative(self, event)
       def develop_cultural_elements(self, belief_system)
   ```

## Artificial Intelligence Systems

I implemented several AI systems to create realistic civilization behavior:

1. **Decision Making**
   - Utility-based action selection
   - Multi-factor strategic planning
   - Risk-reward analysis for expansion

2. **Behavioral Modeling**
   - Trait-based personality system
   - Historical event memory
   - Adaptive strategy selection

## Future Development

Areas I plan to enhance:

1. **Advanced Systems**
   - Cultural diffusion modeling
   - Religious belief propagation
   - Economic trade networks
   - Climate simulation

2. **Technical Improvements**
   - Multi-threaded processing
   - Enhanced pathfinding
   - Advanced AI decision making
   - Improved race condition handling

## Conclusion

CIVSIM represents my vision of creating a deeply detailed civilization simulation that balances historical accuracy with engaging gameplay. Through careful system design and continuous refinement, I've developed a platform that can model the complex interactions between developing societies while maintaining performance and user engagement.

The project continues to evolve as I discover new ways to enhance the simulation's depth while keeping it accessible and performant. The combination of traditional simulation techniques with modern AI capabilities has opened up exciting possibilities for future development.
