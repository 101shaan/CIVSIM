"""
lore generator module for civ simulator using openai api
"""
import os
import json
import time
import random
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI library not found. Install with: pip install openai")

class LoreGenerator:
    def __init__(self):
        """initialize the lore generator"""
        self.client = None
        self.api_key = None
        self.default_model = "gpt-4"
        self.initialized = False
        self.config_path = "config.py"
        
        # cache to avoid repeated api calls for the same content
        self.lore_cache = {}
        
        # try to load the api key
        self._load_api_key()
        
        # fallback cultural templates for offline mode
        self._load_fallback_templates()
    
    def _load_api_key(self):
        """load the openai api key from various sources"""
        # try loading from environment variable
        self.api_key = os.environ.get("OPENAI_API_KEY")
        
        # try loading from config file
        if not self.api_key and os.path.exists(self.config_path):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("config", self.config_path)
                config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config)
                
                self.api_key = getattr(config, "OPENAI_API_KEY", None)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # initialize the client if api key was found
        if self.api_key and OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self.initialized = True
                print("OpenAI API initialized successfully")
            except Exception as e:
                print(f"Error initializing OpenAI API: {e}")
                self.initialized = False
        else:
            if not OPENAI_AVAILABLE:
                print("OpenAI library not available. Lore generation will use fallback templates.")
            else:
                print("OpenAI API key not found. Lore generation will use fallback templates.")
    
    def _load_fallback_templates(self):
        """load fallback templates for when api is unavailable"""
        self.templates = {
            "belief_system": [
                "The {name} believes in harmony with nature and the worship of ancestral spirits.",
                "The {name} follows a strict hierarchical religion with complex rituals.",
                "The {name} practices a philosophy of self-improvement and technological advancement.",
                "The {name} worships celestial bodies and believes in astronomical prophecies.",
                "The {name} follows a monotheistic faith with emphasis on personal salvation.",
            ],
            "city_description": [
                "A bustling hub of commerce nestled between {terrain_feature}.",
                "A fortified settlement known for its {specialty} and strategic location.",
                "A sprawling city with grand architecture and vibrant markets.",
                "A modest town where traditions are preserved through generations.",
                "A center of learning and culture surrounded by {terrain_feature}.",
            ],
            "historical_event": [
                "A devastating plague that reshaped the society's approach to medicine.",
                "A golden age of art and science that produced remarkable achievements.",
                "A period of political reform that established new governing institutions.",
                "A series of natural disasters that tested the civilization's resilience.",
                "A cultural revolution that transformed social structures and beliefs.",
            ],
            "war_description": [
                "A bitter conflict over resources that left both sides weakened.",
                "A swift conquest that demonstrated military superiority.",
                "A long series of border skirmishes that eventually erupted into full war.",
                "A defensive struggle against an aggressive neighbor.",
                "A war of succession after disputed leadership claims.",
            ],
        }
    
    def set_api_key(self, api_key):
        """set the openai api key manually"""
        self.api_key = api_key
        
        if OPENAI_AVAILABLE:
            try:
                self.client = OpenAI(api_key=api_key)
                self.initialized = True
                return True
            except Exception as e:
                print(f"Error initializing OpenAI API: {e}")
                self.initialized = False
                return False
        return False
    
    def generate_belief_system_lore(self, belief_system, civ_traits):
        """generate rich lore for a civilization's belief system"""
        # create a cache key
        cache_key = f"belief_{belief_system.name}_{'-'.join(sorted(civ_traits))}"
        
        # check cache first
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
        
        # if api is available, use it
        if self.initialized and self.client:
            try:
                # create the prompt
                prompt = f"""Create a detailed but concise description of a fictional belief system called "{belief_system.name}" 
                for a civilization with these traits: {', '.join(civ_traits)}. 
                
                Values distribution:
                {json.dumps(belief_system.values, indent=2)}
                
                Foreign stance: {belief_system.foreign_stance}
                
                Include details about:
                - Origin story (1-2 sentences)
                - Core tenets (2-3 key beliefs)
                - Cultural practices (1-2 notable customs)
                - Keep the response under 150 words and focus on what makes this belief system distinctive.
                """
                
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {"role": "system", "content": "You are a creative worldbuilding assistant creating concise lore for a fictional civilization simulation."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250,
                    temperature=0.7
                )
                
                lore = response.choices[0].message.content
                self.lore_cache[cache_key] = lore
                return lore
                
            except Exception as e:
                print(f"OpenAI API error: {e}")
                # fall back to template-based generation
        
        # fallback to template-based generation
        template = random.choice(self.templates["belief_system"])
        values_sorted = sorted(belief_system.values.items(), key=lambda x: x[1], reverse=True)
        top_values = [v[0] for v in values_sorted[:2]]
        
        lore = template.format(name=belief_system.name)
        lore += f" They particularly value {' and '.join(top_values)}."
        lore += f" Their stance toward other beliefs is {belief_system.foreign_stance}."
        
        self.lore_cache[cache_key] = lore
        return lore
    
    def generate_city_lore(self, city_name, terrain, civilization_traits, position):
        """generate lore for a city"""
        cache_key = f"city_{city_name}_{terrain}_{'-'.join(sorted(civilization_traits))}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
            
        if self.initialized and self.client:
            try:
                terrain_types = {0: "water", 1: "plains", 2: "mountains", 3: "forest", 4: "desert"}
                terrain_name = terrain_types.get(terrain, "plains")
                
                prompt = f"""Create a brief, vivid description of a city named "{city_name}" in a {terrain_name} region.
                The city belongs to a civilization with these traits: {', '.join(civilization_traits)}.
                The city is located at coordinates {position}.
                
                Include:
                - Brief physical description (1 sentence)
                - What the city is known for (1 sentence)
                - One distinctive cultural or architectural feature
                - Keep it under 100 words total
                """
                
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {"role": "system", "content": "You are a creative worldbuilding assistant creating concise lore for a fictional city."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                lore = response.choices[0].message.content
                self.lore_cache[cache_key] = lore
                return lore
                
            except Exception as e:
                print(f"OpenAI API error in city lore: {e}")
        
        # fallback
        terrain_features = {
            0: "coastal waters",
            1: "fertile plains",
            2: "rugged mountains",
            3: "dense forests",
            4: "vast deserts"
        }
        
        specialties = ["craftsmanship", "trade", "military training", "scholarly pursuits", "religious ceremonies"]
        specialty = random.choice(specialties)
        
        template = random.choice(self.templates["city_description"])
        lore = template.format(
            terrain_feature=terrain_features.get(terrain, "varied landscapes"),
            specialty=specialty
        )
        
        lore += f" {city_name} is known throughout the region for its {random.choice(['unique architecture', 'cultural festivals', 'defensive walls', 'trading markets', 'religious monuments'])}."
        
        self.lore_cache[cache_key] = lore
        return lore
    
    def generate_war_description(self, civ1_name, civ2_name, civ1_traits, civ2_traits, winner_name):
        """Generate a description of a war between civilizations"""
        cache_key = f"war_{civ1_name}_{civ2_name}_{winner_name}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
            
        if self.initialized and self.client:
            try:
                prompt = f"""Create a brief, dramatic description of a war between {civ1_name} (with traits: {', '.join(civ1_traits)}) 
                and {civ2_name} (with traits: {', '.join(civ2_traits)}).
                {winner_name} was the victor.
                
                Include:
                - The cause of the conflict (1 sentence)
                - A pivotal battle or strategy (1 sentence)
                - The aftermath and consequences (1 sentence)
                - Keep it under 100 words total
                """
                
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {"role": "system", "content": "You are a creative historical chronicler creating concise war descriptions for a fictional civilization simulation."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                lore = response.choices[0].message.content
                self.lore_cache[cache_key] = lore
                return lore
                
            except Exception as e:
                print(f"OpenAI API error in war description: {e}")
        
        # fallback
        template = random.choice(self.templates["war_description"])
        lore = f"The war between {civ1_name} and {civ2_name} was {template.lower()} "
        lore += f"After a series of conflicts, {winner_name} emerged victorious, forever changing the balance of power in the region."
        
        self.lore_cache[cache_key] = lore
        return lore
    
    def generate_historical_period(self, civ_name, start_year, end_year, events):
        """Generate a description of a historical period for a civilization"""
        if not events:
            return "Little is known of this period of history."
            
        cache_key = f"history_{civ_name}_{start_year}_{end_year}_{hash(json.dumps(events))}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
            
        if self.initialized and self.client:
            try:
                # Filter to important events only to avoid token limits
                important_events = []
                for event in events:
                    if any(keyword in event.lower() for keyword in ["war", "city", "collapsed", "unified", "conquered", "founded", "established"]):
                        important_events.append(event)
                
                # If we still have too many events, sample some
                if len(important_events) > 10:
                    important_events = random.sample(important_events, 10)
                
                prompt = f"""Create a brief historical summary for the civilization of {civ_name} from year {start_year} to {end_year}.
                
                Key events during this period:
                {chr(10).join('- ' + event for event in important_events)}
                
                Include:
                - A name for this historical period/age (1 short phrase)
                - Brief summary of the period's significance (2-3 sentences)
                - Keep it under 120 words total
                """
                
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {"role": "system", "content": "You are a creative historical chronicler creating concise historical summaries for a fictional civilization simulation."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                lore = response.choices[0].message.content
                self.lore_cache[cache_key] = lore
                return lore
                
            except Exception as e:
                print(f"OpenAI API error in historical period: {e}")
        
        # fallback
        template = random.choice(self.templates["historical_event"])
        period_names = ["Age of Enlightenment", "Dark Period", "Golden Era", "Time of Troubles", "Renaissance"]
        
        lore = f"**The {random.choice(period_names)} ({start_year}-{end_year})**\n\n"
        lore += f"This period was marked by {template.lower()} "
        lore += f"The civilization of {civ_name} underwent significant changes during this time."
        
        if events:
            lore += f" Notable events included: {'; '.join(random.sample(events, min(3, len(events))))}."
        
        self.lore_cache[cache_key] = lore
        return lore

    def generate_civilization_lore(self, civ_name, civ_traits, belief_system, history_events):
        """Generate rich lore for a civilization"""
        cache_key = f"civ_{civ_name}_{','.join(civ_traits)}_{belief_system.name}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
        
        if self.initialized and self.client:
            try:
                # Select important events only
                selected_events = []
                for event in history_events:
                    if any(keyword in event.lower() for keyword in ["war", "city", "collapsed", "unified", "conquered", "founded", "established"]):
                        selected_events.append(event)
                
                # If we still have too many events, sample some
                if len(selected_events) > 10:
                    selected_events = random.sample(selected_events, 10)
                
                prompt = f"""Create rich and detailed lore for the fictional civilization of {civ_name}.
                
                Their traits are: {', '.join(civ_traits)}
                Their belief system is: {belief_system.name}, with a {belief_system.foreign_stance} stance toward foreigners.
                
                Key historical events:
                {chr(10).join('- ' + event for event in selected_events)}
                
                Include:
                1. Origin story of the civilization (1-2 paragraphs)
                2. Details about 2-3 notable historical leaders with unique personalities and accomplishments
                3. Cultural practices unique to this civilization (1 paragraph)
                4. Architecture and city design unique to them (1 paragraph)
                5. Interesting or unusual facts about their society
                
                Make the content diverse, rich in detail but concise, and unique - not generic fantasy tropes.
                Total length should be around 250-300 words.
                """
                
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {"role": "system", "content": "You are a creative world-building assistant generating unique, detailed lore for fictional civilizations in a simulation. Avoid generic fantasy tropes and focus on creating distinctive cultures with memorable details. Each civilization should feel unique with its own identity."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.8
                )
                
                lore = response.choices[0].message.content
                self.lore_cache[cache_key] = lore
                return lore
                
            except Exception as e:
                print(f"OpenAI API error in civilization lore: {e}")
        
        # fallback
        lore = f"The {civ_name} civilization is known for their {', '.join(civ_traits)} nature. "
        lore += f"They follow the {belief_system.name} belief system and are {belief_system.foreign_stance} toward outsiders. "
        lore += "Their history is filled with " + random.choice(["conquest", "innovation", "cultural achievements", "religious devotions"]) + "."
        
        self.lore_cache[cache_key] = lore
        return lore

    def generate_notable_leaders(self, civ_name, civ_traits, belief_system, tech_level, years_of_history):
        """Generate rich descriptions of notable leaders from the civilization's history"""
        # Check cache
        cache_key = f"leaders_{civ_name}_{'-'.join(sorted(civ_traits))}_{belief_system.name}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
        
        # If API is available, use it
        if self.initialized and self.client:
            try:
                # Create the prompt
                prompt = f"""Create brief descriptions of 2-3 notable historical leaders from a fictional civilization called "{civ_name}" 
                with these traits: {', '.join(civ_traits)}.
                
                Their belief system is: {belief_system.name} (stance: {belief_system.foreign_stance})
                
                Technology level: {tech_level:.1f}/100
                Years of history: {years_of_history}
                
                For each leader provide:
                - Name and title
                - When they lived/ruled (relative to civilization's history)
                - One key achievement or characteristic
                - One interesting quirk or trait
                
                Keep the entire response under 150 words total.
                """
                
                try:
                    response = self.client.chat.completions.create(
                        model=self.default_model,
                        messages=[
                            {"role": "system", "content": "You are a creative worldbuilding assistant creating concise lore for a fictional civilization simulation."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=250,
                        temperature=0.7
                    )
                    
                    lore = response.choices[0].message.content
                    self.lore_cache[cache_key] = lore
                    return lore
                except Exception as e:
                    print(f"OpenAI API error in leader profiles: {e}")
                    # Fall through to template-based generation
            except Exception as e:
                print(f"Error generating leader profiles: {e}")
                # Fall through to template-based generation
        
        # Fall back to template-based generation
        # Generate 2-3 leaders using templates
        num_leaders = random.randint(2, 3)
        leader_descriptions = []
        
        titles = ["Emperor", "Queen", "High Priest", "Warlord", "Chieftain", "Sage", "Prophet", "Chancellor"]
        achievements = ["expanded territory by conquest", "brought an age of peace", "reformed the legal system", 
                      "built great monuments", "advanced technology", "survived a catastrophe"]
        quirks = ["had six fingers on each hand", "never slept more than 4 hours", "adopted 100 children", 
                 "wrote poetry in secret", "was afraid of water", "collected unusual pets"]
        
        for i in range(num_leaders):
            # Generate leader info
            name = self._generate_name()
            title = random.choice(titles)
            
            # When they lived - distribute across civilization history
            period_start = int((i / num_leaders) * years_of_history)
            period_end = int(((i + 1) / num_leaders) * years_of_history)
            period = f"ruled {period_start}-{period_end} years ago"
            
            # Achievements and quirks
            achievement = random.choice(achievements)
            quirk = random.choice(quirks)
            
            leader_desc = f"{name} the {title} ({period}): {achievement}. Notably, {quirk}."
            leader_descriptions.append(leader_desc)
        
        leaders_text = "\n\n".join(leader_descriptions)
        self.lore_cache[cache_key] = leaders_text
        return leaders_text

    def generate_cultural_facts(self, civ_name, civ_traits, belief_system, territory_size):
        """Generate unique cultural facts about a civilization"""
        cache_key = f"culture_{civ_name}_{','.join(civ_traits)}_{territory_size}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
        
        if self.initialized and self.client:
            try:
                # Determine scope of civilization based on territory size
                scope = "small tribal group"
                if territory_size > 20:
                    scope = "small nation-state"
                if territory_size > 50:
                    scope = "established nation"
                if territory_size > 100:
                    scope = "large empire with multiple provinces"
                
                prompt = f"""Create 5 unique and interesting cultural facts about the {civ_name} civilization.
                
                Their traits are: {', '.join(civ_traits)}
                Their belief system is: {belief_system.name}, with a {belief_system.foreign_stance} stance toward foreigners.
                They are a {scope} with distinctive cultural practices.
                
                For each cultural fact, cover one of these aspects:
                1. A unique food, cuisine or dining tradition
                2. An unusual form of art, music, or cultural expression
                3. A distinctive social ritual or ceremony (birth, coming-of-age, marriage, death, etc.)
                4. A unique technology, craft, or innovation they're known for
                5. An unusual law, governance structure, or social organization
                
                Make these facts specific, vivid, and NOT generic fantasy tropes.
                Each fact should be 2-3 sentences and provide vivid details.
                Facts should connect logically to their traits and belief systems.
                Avoid any overlap between the facts - each should cover a completely different aspect.
                """
                
                response = self.client.chat.completions.create(
                    model=self.default_model,
                    messages=[
                        {"role": "system", "content": "You are a creative cultural anthropologist creating unique, detailed cultural practices for fictional civilizations. Focus on specificity, originality, and logical connection to the civilization's traits. Avoid generic fantasy tropes or overlapping content."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.8
                )
                
                lore = response.choices[0].message.content
                self.lore_cache[cache_key] = lore
                return lore
                
            except Exception as e:
                print(f"OpenAI API error in cultural facts: {e}")
        
        # Fallback
        lore = f"## Cultural Facts: {civ_name}\n\n"
        lore += "- They have a unique tradition of " + random.choice(["seasonal festivals", "ancestor worship", "communal meals", "artistic competitions"]) + ".\n"
        lore += "- They are known for their skill in " + random.choice(["metalworking", "pottery", "textile arts", "astronomy", "medicine"]) + ".\n"
        
        self.lore_cache[cache_key] = lore
        return lore

    def _generate_name(self, prefix=""):
        """Generate a random name for belief systems, cities, etc."""
        syllables = ["ra", "ka", "ta", "li", "na", "mo", "so", "lo", "mi", "ti", 
                    "pa", "ko", "to", "po", "ba", "ga", "ma", "sa", "za", "fa"]
        name_parts = []
        
        # Add prefix if provided
        if prefix:
            name_parts.append(prefix)
        
        # Generate 2-3 syllables
        for _ in range(random.randint(2, 3)):
            name_parts.append(random.choice(syllables))
        
        # Capitalize each part
        name = "".join(part.capitalize() for part in name_parts)
        return name

# Global instance for convenience
lore_gen = LoreGenerator() 