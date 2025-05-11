"""
config settings for civ simulator
"""

# openai api key for lore generation
# replace this with your actual api key or set it as an environment variable
# named OPENAI_API_KEY
OPENAI_API_KEY =""  # empty string will use fallback templates

# game settings
GAME_TITLE = "Civilization Simulator"
DEFAULT_WORLD_SIZE = (100, 100)
DEFAULT_WINDOW_SIZE = (1400, 900)

# display settings
TILE_SIZE = 8  # size of each tile in pixels
SHOW_FPS = True  # show fps counter

# simulation settings
DEFAULT_NUM_CIVS = 5  # default number of civs to start with
DEFAULT_SIMULATION_SPEED = 3  # default simulation speed (3x)
AUTO_PAUSE_ON_EVENTS = True  # auto-pause on major events

# lore generation settings
USE_AI_LORE = True  # whether to use ai for lore generation
LORE_MODEL = "gpt-4"  # openai model to use for lore generation

# can add more config options here if needed 