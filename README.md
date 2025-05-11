# The CIVSIM

A Python/Pygame civilization simulation that models the growth and interaction of civilizations.

## Features

- Realistic population growth with demographic transitions
- Territory expansion and visualization
- War and diplomatic interactions between civilizations
- OpenAI GPT integration for dynamic lore generation
- Detailed civilization information with rich UI

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the simulator:
   ```
   python main.py
   ```

## OpenAI API Key Setup

The simulator can generate rich lore for civilizations using OpenAI's GPT models. To use this feature:

1. **Option 1: Environment Variable**
   - Set the `OPENAI_API_KEY` environment variable with your API key
   
2. **Option 2: Config File**
   - Edit the `config.py` file and add your API key:
     ```python
     OPENAI_API_KEY = "your-api-key-here"
     ```

If no API key is provided, the simulator will fall back to using pre-defined templates for lore generation.

## Controls

- **Click** on civilizations to select them and view details
- **Space** to pause/resume the simulation
- **Up/Down arrows** to change simulation speed
- **C** to toggle the civilization list
- **G** to toggle God Mode
- **V** to toggle city visibility
- **L** to toggle labels
- **H** to toggle help overlay 
