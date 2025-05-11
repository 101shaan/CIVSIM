"""
lore access module for civ simulator
this module provides a simpler interface to the lore generation functionality.
"""
from src.lore_generator import lore_gen

def get_detailed_civilization_info(civilization, simulation):
    """
    get detailed info about a civ using the lore generator.
    
    args:
        civilization: the civ object to get info for
        simulation: the current simulation instance
        
    returns:
        a dictionary with detailed info about the civilization
    """
    detailed_info = {
        "belief_lore": lore_gen.generate_belief_system_lore(civilization.belief_system, civilization.traits),
        "cities": {},
        "history": lore_gen.generate_historical_period(
            civilization.name,
            max(0, simulation.year - 100),
            simulation.year,
            [event["description"] for event in civilization.event_log[-10:]]
        ),
        "general_lore": lore_gen.generate_civilization_lore(
            civilization.name,
            civilization.traits,
            civilization.belief_system,
            [event["description"] for event in civilization.event_log[-15:]]
        ),
        "leaders": lore_gen.generate_notable_leaders(
            civilization.name,
            civilization.traits,
            civilization.belief_system,
            civilization.technology,
            civilization.age
        ),
        "cultural_facts": lore_gen.generate_cultural_facts(
            civilization.name,
            civilization.traits,
            civilization.belief_system,
            len(civilization.territory)
        )
    }
    
    # get lore for major cities (limit to 3 largest to avoid excessive api calls)
    if civilization.cities:
        largest_cities = sorted(civilization.cities.items(), key=lambda x: x[1]["population"], reverse=True)[:3]
        for pos, city_info in largest_cities:
            terrain = simulation.world.get_terrain_at(pos)
            detailed_info["cities"][city_info["name"]] = lore_gen.generate_city_lore(
                city_info["name"],
                terrain,
                civilization.traits,
                pos
            )
    
    return detailed_info 