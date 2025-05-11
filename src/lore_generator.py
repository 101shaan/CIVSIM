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
                "The {name} believes in harmony with nature and the worship of ancestral spirits. Rituals are performed at sacred groves and near bodies of water to honor the cycle of life.",
                "The {name} follows a strict hierarchical religion with complex rituals. Priests hold significant political power and serve as intermediaries between the people and the divine.",
                "The {name} practices a philosophy of self-improvement and technological advancement. They believe the path to enlightenment lies in understanding the material world through scientific inquiry.",
                "The {name} worships celestial bodies and believes in astronomical prophecies. Their temples are built to align with solar and lunar events, and their calendar is highly accurate.",
                "The {name} follows a monotheistic faith with emphasis on personal salvation. They believe in an afterlife where one's actions in life determine eternal reward or punishment.",
                "The {name} practices ancestor worship, believing the deceased continue to influence the living. Family shrines are maintained in every household, and elaborate funerals ensure proper passage to the next world.",
                "The {name} follows an animistic belief system, seeing spirits in all natural elements. Shamans communicate with these spirits through trance rituals, often using sacred plants as intermediaries.",
                "The {name} adheres to a dualistic cosmology where forces of light and darkness are in constant struggle. They see moral choices as participating in this cosmic battle.",
                "The {name} practices a mystery religion with secret initiations and revealed wisdom. Devotees progress through levels of understanding, gaining deeper insights with each ritual passage.",
                "The {name} follows a philosophical tradition emphasizing logic, ethics, and the pursuit of knowledge. Their schools of thought have produced many renowned scholars and debaters.",
                "The {name} embraces polytheism with a vast pantheon representing natural forces and human virtues. Their mythology contains elaborate stories explaining the world's origin and natural phenomena.",
                "The {name} practices a syncretic faith, incorporating elements from multiple traditions they've encountered through trade and conquest. This adaptability has allowed their beliefs to spread widely.",
            ],
            "city_description": [
                "A bustling hub of commerce nestled between {terrain_feature}, with markets filled with exotic goods and street performers entertaining the crowds. {city_name} is known for its intricate canal system that both aids transportation and provides defense.",
                "A fortified settlement known for its {specialty} and strategic location. The massive walls of {city_name} have withstood numerous sieges, and its central fortress is considered impregnable by many.",
                "A sprawling city with grand architecture and vibrant markets. The skyline of {city_name} is dominated by towering spires and massive domes that reflect the prosperity of its merchant class.",
                "A modest town where traditions are preserved through generations. In {city_name}, ancient crafts are still practiced exactly as they were centuries ago, and yearly festivals maintain cultural continuity.",
                "A center of learning and culture surrounded by {terrain_feature}. The libraries and academies of {city_name} attract scholars from far and wide, and its theaters showcase the finest artistic expressions.",
                "A coastal port city with a magnificent harbor filled with ships from distant lands. {city_name}'s lighthouse guides vessels safely to shore, and its shipyards produce the finest vessels in the region.",
                "A mountain citadel carved directly into the rockface, with buildings rising in terraced levels. {city_name} controls important mountain passes and is renowned for its defensive capabilities.",
                "A garden city where buildings and nature exist in harmony. The hanging gardens of {city_name} are considered one of the great wonders of the world, sustained by an ingenious irrigation system.",
                "A desert oasis city that thrives against all odds, with ingenious water management systems. {city_name} is known for its underground aqueducts that bring fresh water from distant mountains.",
                "A holy city built around sacred sites, drawing pilgrims from across the lands. The temples of {city_name} are architectural marvels, and religious ceremonies occur daily in its sacred plazas.",
                "A cosmopolitan trading hub where different cultures blend together. In {city_name}, you can hear dozens of languages spoken in its markets, and its cuisine reflects influences from many traditions.",
                "A frontier settlement that represents the edge of civilization, protecting against wilderness threats. The watchtowers of {city_name} are always manned, and its militia is exceptionally well-trained.",
            ],
            "historical_event": [
                "A devastating plague that reshaped the society's approach to medicine. As the population dwindled, survivors developed new hygienic practices and hospitals were established for the first time.",
                "A golden age of art and science that produced remarkable achievements. Great libraries were built, and scholars made discoveries that would influence thought for centuries to come.",
                "A period of political reform that established new governing institutions. The old order was peacefully transformed, creating a more representative system that has endured to this day.",
                "A series of natural disasters that tested the civilization's resilience. After earthquakes, floods, and fires, they rebuilt stronger than before, with new architectural techniques designed to withstand future calamities.",
                "A cultural revolution that transformed social structures and beliefs. Old traditions were questioned and sometimes abandoned, leading to a more dynamic and progressive society.",
                "A great migration that brought new peoples and ideas into the civilization. This diversity eventually strengthened the culture, though initial conflicts had to be overcome through compromise.",
                "A technological breakthrough that revolutionized everyday life. The innovation spread rapidly and created new industries, dramatically improving living standards for many citizens.",
                "A succession crisis that threatened to tear the civilization apart. Different factions supported rival claimants to leadership, and only after years of tension was stability restored.",
                "An economic transformation that changed the basis of wealth and power. New resources were discovered or new methods of production developed, shifting the balance between social classes.",
                "A religious reformation that challenged established spiritual authorities. New interpretations of sacred texts led to the formation of splinter groups, some of which gained significant followings.",
                "A period of exploration that expanded knowledge of the world. Brave adventurers ventured into unknown territories, returning with maps, specimens, and stories that captivated public imagination.",
                "A legendary leader's rule that became the standard by which all subsequent governance was judged. Their wisdom and vision established principles that would guide the civilization for generations.",
            ],
            "war_description": [
                "A bitter conflict over resources that left both sides weakened.",
                "A swift conquest that demonstrated military superiority.",
                "A long series of border skirmishes that eventually erupted into full war.",
                "A defensive struggle against an aggressive neighbor.",
                "A war of succession after disputed leadership claims.",
            ],
            "civilization_lore": [
                "The {name} civilization is known for their sophisticated agricultural techniques, having developed irrigation systems that transform arid lands into fertile fields. Their architectural style features stepped pyramids that serve both religious and administrative functions.",
                "The {name} people are renowned seafarers whose ships have charted distant coastlines and established trading networks across vast waters. Their society is organized around a council of captains who make decisions collectively.",
                "The {name} civilization has mastered metallurgy to an extraordinary degree, creating alloys unknown to their neighbors. Their cities are protected by concentric walls, and their weapons are sought after by allies and feared by enemies.",
                "The {name} are known for their mathematical and astronomical knowledge, having developed a calendar of remarkable accuracy and complex systems of notation. Their cities are planned in alignment with celestial bodies.",
                "The {name} civilization has developed a complex system of writing used to record history, laws, and poetry. Their literature is rich with epics detailing the exploits of heroes and the intervention of divine beings in mortal affairs.",
                "The {name} have perfected the art of defensive warfare, building sophisticated fortifications and training disciplined infantry. They rarely expand through conquest, preferring to establish tributary relationships with neighboring peoples.",
                "The {name} civilization is organized around a caste system, with each person's role determined by birth. Despite this rigid social structure, they have produced remarkable achievements in art, particularly sculpture and music.",
                "The {name} are master horticulturists who have domesticated numerous plant species for food, medicine, and beauty. Their cities feature extensive botanical gardens, and their healers are sought after for their knowledge of herbal remedies.",
                "The {name} civilization has developed a complex bureaucracy governed by meritocratic principles. Officials must pass rigorous examinations testing their knowledge of history, ethics, and administration before taking office.",
                "The {name} people have a nomadic heritage that influences their culture even as they build permanent settlements. Their architecture uses lightweight materials and incorporates elements reminiscent of traditional portable dwellings.",
                "The {name} civilization has a highly developed legal system with courts and codified laws dating back centuries. Their concept of justice emphasizes restoration and rehabilitation rather than punishment.",
                "The {name} are known for their diplomatic skill, maintaining peace through a network of alliances and marriages between ruling families. Their emissaries are respected for their ability to resolve conflicts without resorting to violence.",
            ],
            "leader_templates": [
                "{name}, the Visionary, who led the civilization through a period of unprecedented expansion, establishing new settlements and forging crucial alliances with neighboring peoples.",
                "{name}, the Reformer, whose sweeping changes to governance created more equitable institutions that have stood the test of time and become central to the civilization's identity.",
                "{name}, the Defender, who successfully repelled multiple invasions and strengthened the civilization's defenses, ensuring decades of security and peaceful development.",
                "{name}, the Scholar-Ruler, whose patronage of learning established great centers of knowledge and attracted brilliant minds from far and wide to contribute to cultural advancement.",
                "{name}, the Unifier, who brought together previously warring factions under a single banner, creating a sense of shared identity that transcended old tribal loyalties.",
                "{name}, the Navigator, whose expeditions discovered new lands and resources, greatly expanding the civilization's understanding of the world and access to valuable trade goods.",
                "{name}, the Lawgiver, whose legal code established clear rights and responsibilities for all citizens, creating a framework for justice that outlived their reign by centuries.",
                "{name}, the Builder, under whose direction monumental architecture transformed the urban landscape and created enduring symbols of the civilization's greatness.",
                "{name}, the Benevolent, whose concern for the common people led to policies that improved living conditions and provided support during times of hardship.",
                "{name}, the Conqueror, whose military campaigns expanded territorial control and brought new peoples and resources under the civilization's influence.",
                "{name}, the Diplomat, whose skill at negotiation prevented numerous conflicts and established beneficial relationships with potential rivals and allies alike.",
                "{name}, the Innovator, whose encouragement of new techniques and technologies gave the civilization advantages in agriculture, craftsmanship, and warfare.",
            ],
            "cultural_facts": [
                "The people of {name} practice a unique form of martial arts that combines combat techniques with dance-like movements, performed during festivals and used for self-defense. Their distinctive weaponry includes a curved blade that can be used both as a tool and for fighting.",
                "In {name} society, coming-of-age rituals involve a period of solitary survival in the wilderness, during which young people must demonstrate self-reliance and return with an item symbolizing their personal strength.",
                "The {name} have developed a sophisticated written language using pictographs that evolved into an elegant script. Their poets are highly respected, and literary competitions are major social events attended by people of all classes.",
                "Architecture in {name} settlements follows strict geometric principles believed to channel cosmic energy. Buildings are oriented according to astronomical alignments, and proportions follow mathematical ratios thought to be divinely inspired.",
                "The {name} practice elaborate funeral rituals where the deceased are accompanied by symbolic objects representing their achievements in life. Ancestors are regularly honored through ceremonies that include offerings of food and symbolic items.",
                "Music plays a central role in {name} culture, with different melodic modes prescribed for various occasions and seasons. Their unique instruments include resonant stone chimes and multi-chambered wind instruments capable of playing chords.",
                "{name} governance includes a unique practice where leaders must periodically undergo public rituals of renewal, during which their fitness to rule is assessed based on physical challenges and tests of wisdom.",
                "Cuisine in {name} society is characterized by elaborate preparation techniques and specific combinations of flavors believed to balance bodily energies. Communal meals are important social occasions that strengthen community bonds.",
                "The {name} have perfected techniques for working with a local material in ways unknown to other peoples. Their artisans create objects of remarkable beauty and utility, which have become valuable trade goods.",
                "Gender roles in {name} society differ from many neighboring cultures, with responsibilities divided based on aptitude rather than strict gender lines. Their historical records mention notable leaders of all genders who made significant contributions.",
                "The calendar system developed by the {name} tracks multiple astronomical cycles and influences when important activities are undertaken. Certain days are considered auspicious for specific actions, from planting crops to beginning journeys.",
                "The {name} have a tradition of oral history where specialized memorizers can recount centuries of events with remarkable accuracy. These knowledge-keepers undergo years of training to develop their mnemonic abilities.",
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
            specialty=specialty,
            city_name=city_name
        )
        
        # We don't need to add the city name again since it's now included in the template
        if "{city_name}" not in template:
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
        cache_key = f"civ_{civ_name}_{'-'.join(sorted(civ_traits))}"
        
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
        
        # fallback to improved templates
        template = random.choice(self.templates["civilization_lore"])
        lore = template.format(name=civ_name)
        
        # Add some traits information
        if civ_traits:
            lore += f" Their society particularly values {', '.join(civ_traits[:-1])}" 
            if len(civ_traits) > 1:
                lore += f" and {civ_traits[-1]}"
            lore += "."
        
        # Add belief system info
        lore += f" They follow the {belief_system.name} belief system and are {belief_system.foreign_stance} toward outsiders."
        
        self.lore_cache[cache_key] = lore
        return lore

    def generate_notable_leaders(self, civ_name, civ_traits, belief_system, tech_level, years_of_history):
        """Generate rich descriptions of notable leaders from the civilization's history"""
        # Check cache
        cache_key = f"leaders_{civ_name}_{'-'.join(sorted(civ_traits))}_{belief_system.name}"
        
        if cache_key in self.lore_cache:
            return self.lore_cache[cache_key]
        
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
        
        # Fallback to template based generation with our new leader templates
        # Choose number of leaders based on civilization age
        num_leaders = min(3, max(1, years_of_history // 100))
        
        # Get templates and generate leader names
        leader_templates = random.sample(self.templates["leader_templates"], num_leaders)
        leader_prefix = random.choice(["Emperor", "Queen", "King", "Chief", "Lord", "Lady", "Chancellor", "High Priest", "Warlord", "Matriarch", "Patriarch", "Sovereign"])
        leader_names = []
        
        # Create phonetically consistent names for the civilization
        vowels = "aeiou"
        consonants = "bcdfghjklmnpqrstvwxyz"
        
        # Extract first letter of civ name to influence leader names
        first_letter = civ_name[0].lower() if civ_name else random.choice(consonants)
        
        for i in range(num_leaders):
            # Generate a name with similar phonetic patterns to the civilization name
            name_length = random.randint(4, 8)
            if first_letter in vowels:
                pattern = [0, 1, 0, 1, 0, 1, 0, 1]  # vowel-consonant pattern
            else:
                pattern = [1, 0, 1, 0, 1, 0, 1, 0]  # consonant-vowel pattern
                
            name = first_letter
            for j in range(1, name_length):
                if pattern[j % len(pattern)] == 0:
                    name += random.choice(vowels)
                else:
                    name += random.choice(consonants)
            
            name = name.capitalize()
            leader_names.append(f"{leader_prefix} {name}")
        
        # Format the leader descriptions
        descriptions = []
        for i in range(num_leaders):
            description = leader_templates[i].format(name=leader_names[i])
            descriptions.append(description)
        
        # Combine descriptions
        lore = "Throughout their history, several notable leaders have shaped the destiny of this civilization:\n\n"
        lore += "\n\n".join(descriptions)
        
        self.lore_cache[cache_key] = lore
        return lore

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
        
        # Fallback to template based generation with our new cultural templates
        template = random.choice(self.templates["cultural_facts"])
        cultural_lore = template.format(name=civ_name)
        
        # Add some additional info based on civilization traits
        if civ_traits:
            trait = random.choice(civ_traits)
            if trait == "aggressive":
                cultural_lore += f" The {civ_name} are known for their intimidating war dances and elaborate armor design that strikes fear into their enemies."
            elif trait == "diplomatic":
                cultural_lore += f" The {civ_name} have a tradition of resolving conflicts through formal debates where both sides present their case before neutral mediators."
            elif trait == "innovative":
                cultural_lore += f" The {civ_name} hold regular competitions where inventors showcase new tools and devices, with the best being awarded special status in society."
            elif trait == "traditional":
                cultural_lore += f" The {civ_name} maintain ancient ceremonies unchanged for generations, believing their precise performance ensures cosmic harmony."
            elif trait == "expansionist":
                cultural_lore += f" The {civ_name} conduct elaborate rituals when claiming new territory, with monuments erected to mark the boundaries of their expanding realm."
        
        # Add belief system influence
        cultural_lore += f" Their {belief_system.name} belief system influences daily life through {random.choice(['prayer rituals', 'dietary restrictions', 'special garments', 'regular festivals', 'symbolic decorations'])}."
        
        self.lore_cache[cache_key] = cultural_lore
        return cultural_lore

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