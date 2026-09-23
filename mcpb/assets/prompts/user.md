# Vienna Transit User Guide

## Getting Started

1. **Configure Settings**: Adjust timeout and cache settings as needed
2. **Find Stations**: Use station_search to locate stops by name
3. **Check Departures**: Get real-time departure information
4. **Plan Journeys**: Use journey_planner for route optimization

## Core Features

### Finding Stations
```
Search by name: station_search("Karlsplatz")
Search with context: station_search("Central Station")
Fuzzy matching: station_search("stephansdom")
```

### Departure Information
```
Next departures: next_departures("Westbahnhof", limit=5)
Specific lines: next_departures("Karlsplatz", lines=["U1", "U2", "U4"])
Time window: next_departures("Schottentor", minutes=30)
```

### Journey Planning
```
Simple route: journey_planner("from: Westbahnhof", "to: Karlsplatz")
With preferences: journey_planner("from: Airport", "to: City Center", mode="fastest")
Avoid transfers: journey_planner("from: A", "to: B", max_transfers=0)
```

### Service Status
```
Check disruptions: line_status("U1")
All services: line_status()
Elevator status: line_status("elevator")
```

## Vienna Transit Lines

### U-Bahn (Metro)
- **U1**: Red line - Oberlaa ↔ Leopoldau
- **U2**: Purple line - Karlsplatz ↔ Seestadt
- **U3**: Orange line - Ottakring ↔ Simmering
- **U4**: Green line - Hütteldorf ↔ Heiligenstadt
- **U6**: Brown line - Floridsdorf ↔ Siebenhirten

### Key Tram Lines
- **1**: Schottentor ↔ Stefan Fadinger Platz
- **2**: Dornbach ↔ Friedrich-Engels-Platz
- **D**: Nußdorfer Straße ↔ Oper
- **O**: Raxstraße ↔ Ring

### Major Stations
- **Westbahnhof**: Main western train station
- **Südbahnhof**: Southern train connections
- **Franz-Josefs-Bahnhof**: City center station
- **Karlsplatz**: Major interchange
- **Schottentor**: University district
- **Stephansdom**: City center cathedral

## Best Practices

### Accurate Station Names
- Use official station names when possible
- Include district numbers for clarity (e.g., "Karlsplatz U1/U2/U4")
- Check spelling for international users

### Time Management
- Allow buffer time for transfers (5-10 minutes)
- Check service frequency during off-peak hours
- Plan for weekend service changes

### Accessibility
- Many stations have elevators (check line_status)
- Wheelchair-accessible routes available
- Audio announcements at major stations

## Troubleshooting

### No Departures Found
- Verify station name spelling
- Check if station is in service
- Try nearby alternative stations

### Journey Planning Issues
- Ensure both origin and destination are valid
- Check for service disruptions
- Try different routing preferences

### Service Status Problems
- Check for planned maintenance
- Verify internet connectivity
- Contact Wiener Linien directly for urgent issues

## Service Hours

- **Regular Service**: 5:00 AM - 12:30 AM
- **Night Service**: 12:30 AM - 5:00 AM (limited routes)
- **Weekend Adjustments**: Reduced frequency on Sundays
- **Holiday Changes**: Special schedules for holidays

## Emergency Contacts

- **Wiener Linien**: +43 1 7909 100 (24/7)
- **Emergency**: 112 (police, fire, ambulance)
- **Traffic Information**: ÖAMTC or ARBÖ for road conditions




