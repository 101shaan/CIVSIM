"""
visualization module for civ simulator
"""
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class Visualizer:
    def __init__(self, simulation):
        self.simulation = simulation
        
        # make sure the folders exist
        os.makedirs("data/reports", exist_ok=True)
        os.makedirs("data/charts", exist_ok=True)
        
        # set up plot style
        plt.style.use('dark_background')
        sns.set_style("darkgrid")
    
    def generate_population_chart(self, save_path=None):
        """generate a chart of population over time for all civilizations"""
        # get historical data
        history = self.simulation.get_civilization_history()
        if not history:
            return None
        
        # extract data for plotting
        years = [snapshot["year"] for snapshot in history]
        
        # track all civs that have existed
        all_civ_ids = set()
        for snapshot in history:
            for civ in snapshot["civilizations"]:
                all_civ_ids.add(civ["id"])
        
        # get population data for each civ
        civ_data = {civ_id: [] for civ_id in all_civ_ids}
        civ_names = {civ_id: "Unknown" for civ_id in all_civ_ids}
        
        for snapshot in history:
            existing_civ_ids = {civ["id"] for civ in snapshot["civilizations"]}
            
            # for each known civ
            for civ_id in all_civ_ids:
                # find this civ in the current snapshot
                civ_data_point = next((civ for civ in snapshot["civilizations"] if civ["id"] == civ_id), None)
                
                if civ_data_point:
                    # record its population
                    civ_data[civ_id].append(civ_data_point["population"])
                    civ_names[civ_id] = civ_data_point["name"]
                else:
                    # civ doesn't exist in this snapshot
                    civ_data[civ_id].append(0)
        
        # create the plot
        plt.figure(figsize=(12, 6))
        
        for civ_id, population_values in civ_data.items():
            # make sure the data array is the same length as years
            data = population_values[:len(years)]
            while len(data) < len(years):
                data.append(0)
                
            plt.plot(years, data, label=civ_names[civ_id], linewidth=2)
        
        plt.title("Civilization Population Over Time")
        plt.xlabel("Year")
        plt.ylabel("Population")
        plt.legend()
        plt.grid(True)
        
        # save the chart if requested
        if save_path:
            plt.savefig(save_path)
            return save_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/charts/{sim_name}_population_{timestamp}.png"
            plt.savefig(save_path)
            plt.close()
            return save_path
    
    def generate_territory_chart(self, save_path=None):
        """generate a chart of territory size over time for all civilizations"""
        # get historical data
        history = self.simulation.get_civilization_history()
        if not history:
            return None
        
        # extract data for plotting
        years = [snapshot["year"] for snapshot in history]
        
        # track all civs that have existed
        all_civ_ids = set()
        for snapshot in history:
            for civ in snapshot["civilizations"]:
                all_civ_ids.add(civ["id"])
        
        # get territory data for each civ
        civ_data = {civ_id: [] for civ_id in all_civ_ids}
        civ_names = {civ_id: "Unknown" for civ_id in all_civ_ids}
        
        for snapshot in history:
            existing_civ_ids = {civ["id"] for civ in snapshot["civilizations"]}
            
            # for each known civ
            for civ_id in all_civ_ids:
                # find this civ in the current snapshot
                civ_data_point = next((civ for civ in snapshot["civilizations"] if civ["id"] == civ_id), None)
                
                if civ_data_point:
                    # record its territory size
                    civ_data[civ_id].append(civ_data_point["territory_size"])
                    civ_names[civ_id] = civ_data_point["name"]
                else:
                    # civ doesn't exist in this snapshot
                    civ_data[civ_id].append(0)
        
        # create the plot
        plt.figure(figsize=(12, 6))
        
        for civ_id, territory_values in civ_data.items():
            # make sure the data array is the same length as years
            data = territory_values[:len(years)]
            while len(data) < len(years):
                data.append(0)
                
            plt.plot(years, data, label=civ_names[civ_id], linewidth=2)
        
        plt.title("Civilization Territory Size Over Time")
        plt.xlabel("Year")
        plt.ylabel("Territory Size (tiles)")
        plt.legend()
        plt.grid(True)
        
        # save the chart if requested
        if save_path:
            plt.savefig(save_path)
            return save_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/charts/{sim_name}_territory_{timestamp}.png"
            plt.savefig(save_path)
            plt.close()
            return save_path
    
    def generate_technology_chart(self, save_path=None):
        """generate a chart of technology level over time for all civilizations"""
        # get historical data
        history = self.simulation.get_civilization_history()
        if not history:
            return None
        
        # extract data for plotting
        years = [snapshot["year"] for snapshot in history]
        
        # track all civs that have existed
        all_civ_ids = set()
        for snapshot in history:
            for civ in snapshot["civilizations"]:
                all_civ_ids.add(civ["id"])
        
        # get technology data for each civ
        civ_data = {civ_id: [] for civ_id in all_civ_ids}
        civ_names = {civ_id: "Unknown" for civ_id in all_civ_ids}
        
        for snapshot in history:
            existing_civ_ids = {civ["id"] for civ in snapshot["civilizations"]}
            
            # for each known civ
            for civ_id in all_civ_ids:
                # find this civ in the current snapshot
                civ_data_point = next((civ for civ in snapshot["civilizations"] if civ["id"] == civ_id), None)
                
                if civ_data_point:
                    # record its technology level
                    civ_data[civ_id].append(civ_data_point["technology"])
                    civ_names[civ_id] = civ_data_point["name"]
                else:
                    # civ doesn't exist in this snapshot
                    civ_data[civ_id].append(0)
        
        # create the plot
        plt.figure(figsize=(12, 6))
        
        for civ_id, tech_values in civ_data.items():
            # ensure the data array is the same length as years
            data = tech_values[:len(years)]
            while len(data) < len(years):
                data.append(0)
                
            plt.plot(years, data, label=civ_names[civ_id], linewidth=2)
        
        plt.title("Civilization Technology Level Over Time")
        plt.xlabel("Year")
        plt.ylabel("Technology Level")
        plt.legend()
        plt.grid(True)
        
        # save the chart if requested
        if save_path:
            plt.savefig(save_path)
            return save_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/charts/{sim_name}_technology_{timestamp}.png"
            plt.savefig(save_path)
            plt.close()
            return save_path
    
    def generate_belief_distribution_chart(self, save_path=None):
        """Generate a chart showing the distribution of belief systems"""
        # Get current civilizations
        civilizations = self.simulation.get_active_civilizations()
        if not civilizations:
            return None
        
        # Extract belief system data
        belief_counts = {}
        for civ in civilizations:
            stance = civ.belief_system.foreign_stance
            if stance not in belief_counts:
                belief_counts[stance] = 0
            belief_counts[stance] += 1
        
        # Create the plot
        plt.figure(figsize=(10, 6))
        
        # Bar chart for belief system stances
        plt.subplot(1, 2, 1)
        stances = list(belief_counts.keys())
        counts = [belief_counts[stance] for stance in stances]
        
        bar_colors = {
            "open": "green",
            "neutral": "blue",
            "hostile": "red",
            "convert": "purple"
        }
        colors = [bar_colors.get(stance, "gray") for stance in stances]
        
        plt.bar(stances, counts, color=colors)
        plt.title("Belief System Foreign Stances")
        plt.xlabel("Stance")
        plt.ylabel("Number of Civilizations")
        
        # Radar chart for belief values
        plt.subplot(1, 2, 2)
        all_values = {}
        for civ in civilizations:
            for value, strength in civ.belief_system.values.items():
                if value not in all_values:
                    all_values[value] = 0
                all_values[value] += strength
        
        # Normalize values
        total = sum(all_values.values())
        if total > 0:
            all_values = {k: v/total for k, v in all_values.items()}
        
        # Create a bar chart for values
        plt.bar(all_values.keys(), all_values.values())
        plt.title("Dominant Belief Values")
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # Save the chart if requested
        if save_path:
            plt.savefig(save_path)
            return save_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/charts/{sim_name}_beliefs_{timestamp}.png"
            plt.savefig(save_path)
            plt.close()
            return save_path
    
    def generate_historical_report(self, save_path=None):
        """Generate a text report of historical events"""
        # Get event history
        events = self.simulation.get_event_history()
        if not events:
            return "No historical events recorded."
        
        # Generate summary using EventLogger
        history_summary = self.simulation.event_logger.generate_history_summary()
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(history_summary)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/reports/{sim_name}_history_{timestamp}.txt"
            with open(save_path, 'w') as f:
                f.write(history_summary)
        
        return save_path
    
    def generate_civilization_report(self, save_path=None):
        """Generate a detailed report about all active civilizations"""
        civilizations = self.simulation.get_active_civilizations()
        if not civilizations:
            return "No active civilizations."
        
        report = "# Civilization Report\n\n"
        
        for civ in civilizations:
            report += f"## {civ.name}\n\n"
            report += f"- **Age:** {civ.age} years\n"
            report += f"- **Population:** {civ.population:,}\n"
            report += f"- **Territory:** {len(civ.territory)} tiles\n"
            report += f"- **Cities:** {len(civ.cities)}\n"
            report += f"- **Technology:** {civ.technology:.1f}\n\n"
            
            report += "### Traits\n"
            for trait in civ.traits:
                report += f"- {trait}\n"
            report += "\n"
            
            report += f"### Belief System: {civ.belief_system.name}\n"
            report += f"- Foreign stance: {civ.belief_system.foreign_stance}\n"
            report += "- Values:\n"
            for value, strength in civ.belief_system.values.items():
                report += f"  - {value}: {int(strength*100)}%\n"
            report += "\n"
            
            report += "### Resources\n"
            for resource, amount in civ.resources.items():
                report += f"- {resource}: {amount:.1f}\n"
            report += "\n"
            
            report += "### Cities\n"
            for pos, city in civ.cities.items():
                report += f"- {city['name']}: Population {city['population']:,} at {pos}\n"
            report += "\n"
            
            report += "### Recent Events\n"
            for event in civ.event_log[-10:]:
                report += f"- Year {event['tick']}: {event['description']}\n"
            report += "\n\n"
        
        if save_path:
            with open(save_path, 'w') as f:
                f.write(report)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/reports/{sim_name}_civs_{timestamp}.txt"
            with open(save_path, 'w') as f:
                f.write(report)
        
        return save_path
    
    def export_simulation_data(self, save_path=None):
        """Export complete simulation data as JSON"""
        # Collect all relevant data
        data = {
            "year": self.simulation.year,
            "tick_count": self.simulation.tick_count,
            "world_size": (self.simulation.world.width, self.simulation.world.height),
            "active_civilizations": [],
            "event_history": self.simulation.get_event_history(),
            "civilization_history": self.simulation.get_civilization_history()
        }
        
        # Add detailed civilization data
        for civ in self.simulation.get_active_civilizations():
            civ_data = {
                "id": civ.id,
                "name": civ.name,
                "age": civ.age,
                "population": civ.population,
                "territory_size": len(civ.territory),
                "technology": civ.technology,
                "traits": civ.traits,
                "belief_system": {
                    "name": civ.belief_system.name,
                    "values": civ.belief_system.values,
                    "foreign_stance": civ.belief_system.foreign_stance
                },
                "resources": civ.resources,
                "relations": civ.relations
            }
            data["active_civilizations"].append(civ_data)
        
        # Save to file
        if save_path:
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            sim_name = getattr(self.simulation, 'current_name', 'sim')
            save_path = f"data/{sim_name}_simulation_{timestamp}.json"
            with open(save_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        return save_path 