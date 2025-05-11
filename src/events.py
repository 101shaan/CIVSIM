"""
event logging module for civ simulator
"""
import json
import time

class EventLogger:
    def __init__(self):
        self.events = []
    
    def add_event(self, year, description, event_type="general"):
        """add a new event to the log"""
        event = {
            "year": year,
            "description": description,
            "type": event_type,
            "timestamp": time.time()
        }
        self.events.append(event)
    
    def get_events_by_year(self, year):
        """get all events for a specific year"""
        return [event for event in self.events if event["year"] == year]
    
    def get_events_by_type(self, event_type):
        """get all events of a specific type"""
        return [event for event in self.events if event["type"] == event_type]
    
    def get_events_range(self, start_year, end_year):
        """get events within a year range"""
        return [event for event in self.events if start_year <= event["year"] <= end_year]
    
    def get_all_events(self):
        """get all logged events"""
        return self.events
    
    def set_events(self, events):
        """set the events (used when loading saved games)"""
        self.events = events
    
    def export_to_json(self, filename):
        """export events to a json file"""
        with open(filename, "w") as file:
            json.dump(self.events, file, indent=2)
    
    def generate_history_summary(self):
        """generate a readable summary of important historical events"""
        if not self.events:
            return "No historical events recorded."
        
        # sort events by year
        sorted_events = sorted(self.events, key=lambda e: e["year"])
        
        # group events by era (blocks of 100 years)
        eras = {}
        for event in sorted_events:
            era = event["year"] // 100
            era_name = f"Era {era}"
            
            if era_name not in eras:
                eras[era_name] = []
            
            eras[era_name].append(event)
        
        # build the summary
        summary = []
        for era_name, era_events in eras.items():
            summary.append(f"\n== {era_name} (Years {era_events[0]['year']} to {era_events[-1]['year']}) ==\n")
            
            for event in era_events:
                summary.append(f"Year {event['year']}: {event['description']}")
        
        return "\n".join(summary)
    
    def clear(self):
        """clear all events"""
        self.events = [] 