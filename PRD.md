# Product Requirements Document: Wiener Linien Live Map

## Executive Summary

The Wiener Linien Live Map is an interactive web application that displays real-time public transport information for Vienna, Austria. The application provides a dynamic map interface showing the current positions of U-Bahn (metro), tram, and bus vehicles, along with their routes and schedules. The goal is to create an intuitive, user-friendly interface that helps commuters and visitors navigate Vienna's public transport system with ease.

## System Overview

### Core Components

1. **Frontend**
   - Interactive map interface using Leaflet.js
   - Real-time vehicle tracking
   - Route visualization
   - Stop information display
   - Responsive design for all devices

2. **Backend**
   - Flask-based web server
   - API integration with Wiener Linien Open Data
   - Data caching and processing
   - Static file serving

3. **Data Processing**
   - GTFS data parsing and storage
   - Real-time vehicle position updates
   - Route and schedule processing

### Technical Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Leaflet.js
- **Backend**: Python 3.8+, Flask
- **Data Storage**: SQLite for GTFS data
- **APIs**: Wiener Linien Open Data API
- **Deployment**: Containerized with Docker (optional)

## Features

### 1. Interactive Map
- Real-time display of vehicle positions
- Zoom and pan functionality
- Base map layers (OpenStreetMap, Satellite, etc.)

### 2. Vehicle Tracking
- Live updates of vehicle positions (every 15 seconds)
- Color-coded by transport type
- Direction indicators and route visualization

### 3. Stop Information
- Clickable stops with departure times
- Line information and next departures
- Accessibility information

### 4. User Interface
- Intuitive controls
- Responsive design for all screen sizes
- Dark/light mode support
- Language selection

## Technical Requirements

### Performance
- Map updates within 500ms of data receipt
- Initial page load under 2 seconds
- Support for at least 1000 concurrent users

### Reliability
- 99.9% uptime
- Graceful degradation during API outages
- Data caching for offline functionality

### Security
- HTTPS encryption
- Input validation
- Rate limiting
- CORS policy enforcement

## Product Requirements

### 1. Core Functionality

#### 1.1 GTFS Data Processing
- **Requirement**: Process GTFS data into structured markdown documentation
- **Requirement**: Display real-time positions of U-Bahn, tram, and bus vehicles on an interactive map
- **Acceptance Criteria**:
  - Vehicles appear as colored markers on the map
  - Vehicle positions update every 15 seconds (respecting API fair use policy)
  - Each vehicle type has distinct visual representation
  - Vehicle markers show line number and direction

#### 1.2 Interactive Map Interface
- **Requirement**: Provide an interactive map centered on Vienna with zoom and pan capabilities
- **Acceptance Criteria**:
  - Map loads with Vienna city center as default view
  - Users can zoom in/out and pan around the map
  - Map uses OpenStreetMap tiles for base layer
  - Responsive design works on desktop and mobile devices

#### 1.3 Vehicle Filtering
- **Requirement**: Allow users to filter vehicles by type and specific lines
- **Acceptance Criteria**:
  - Filter by vehicle type (U-Bahn, tram, bus, all)
  - Filter by specific line numbers
  - Multiple filters can be applied simultaneously
  - Filter state persists during the session

### 2. Technical Requirements

#### 2.1 API Integration
- **Requirement**: Properly integrate with Wiener Linien Open Data API
- **Acceptance Criteria**:
  - Correct API endpoint usage (`/monitor` with proper parameters)
  - Proper data parsing from API responses
  - Respect API fair use policy (15-second minimum intervals)
  - Graceful handling of API errors and timeouts

#### 2.2 Performance
- **Requirement**: Ensure responsive and efficient application performance
- **Acceptance Criteria**:
  - Page load time under 3 seconds
  - Vehicle updates complete within 2 seconds
  - Smooth map interactions without lag
  - Efficient memory usage for vehicle markers

#### 2.3 Reliability
- **Requirement**: Provide stable and reliable service
- **Acceptance Criteria**:
  - Application handles API failures gracefully
  - Fallback to cached data when API is unavailable
  - Clear error messages for users
  - Automatic recovery from temporary failures

### 3. User Experience Requirements

#### 3.1 Interface Design
- **Requirement**: Clean, intuitive, and modern user interface
- **Acceptance Criteria**:
  - Clear visual hierarchy
  - Intuitive controls for filtering
  - Responsive design for all screen sizes
  - Accessible color scheme and contrast

#### 3.2 Information Display
- **Requirement**: Provide relevant information about vehicles and system status
- **Acceptance Criteria**:
  - Vehicle popups show line, direction, and timing information
  - Last update timestamp is displayed
  - System status indicators (online/offline)
  - Loading states for data fetching

## Implementation Plan

### Phase 1: Fix Core API Integration (Priority: Critical)
1. **Fix API Parameter Usage**
   - Replace `stopId` with `rbl` parameter
   - Use correct RBL numbers for Vienna stops
   - Implement proper API request structure

2. **Fix Data Parsing**
   - Update vehicle data extraction logic
   - Handle different API response structures
   - Implement proper coordinate extraction

3. **Improve Error Handling**
   - Add comprehensive error handling for API failures
   - Implement retry logic with exponential backoff
   - Add user-friendly error messages

### Phase 2: Complete Frontend Implementation (Priority: High)
1. **Finish JavaScript Implementation**
   - Complete vehicle marker management
   - Implement proper filter functionality
   - Add vehicle popup information

2. **Enhance User Interface**
   - Improve control panel design
   - Add loading indicators
   - Implement responsive design improvements

### Phase 3: Performance and Reliability (Priority: Medium)
1. **Optimize Performance**
   - Implement efficient marker management
   - Add request debouncing
   - Optimize map rendering

2. **Add Advanced Features**
   - Vehicle route visualization
   - Historical data display
   - User preferences storage

## Technical Specifications

### Backend (Flask)
- **Framework**: Flask 2.2.3+
- **Caching**: Flask-Caching with 15-second timeout
- **API Integration**: Requests library with proper error handling
- **Data Processing**: JSON parsing and transformation

### Frontend
- **Map Library**: Leaflet.js 1.9.4+
- **Styling**: CSS3 with responsive design
- **JavaScript**: Vanilla JS for vehicle management
- **Icons**: Custom vehicle type icons

### API Integration
- **Base URL**: `https://www.wienerlinien.at/ogd_realtime`
- **Main Endpoint**: `/monitor`
- **Parameters**: `rbl` (stop identifier), `line` (optional filter)
- **Rate Limiting**: 15-second minimum intervals

## Success Metrics

### Functional Metrics
- **API Success Rate**: >95% successful API requests
- **Data Accuracy**: Vehicle positions within 100m of actual location
- **Update Frequency**: Consistent 15-second update intervals

### Performance Metrics
- **Page Load Time**: <3 seconds
- **Vehicle Update Time**: <2 seconds
- **Memory Usage**: <100MB for typical usage

### User Experience Metrics
- **Interface Responsiveness**: <100ms for user interactions
- **Error Recovery**: <5 seconds for automatic recovery
- **Cross-browser Compatibility**: Works on Chrome, Firefox, Safari, Edge

## Risk Assessment

### High Risk
- **API Changes**: Wiener Linien may change API structure
- **Rate Limiting**: Potential IP blocking for excessive requests
- **Data Availability**: API may be temporarily unavailable

### Medium Risk
- **Performance**: Large number of vehicles may impact performance
- **Browser Compatibility**: Different browser implementations

### Mitigation Strategies
- **API Monitoring**: Implement health checks and fallback mechanisms
- **Request Optimization**: Efficient caching and request batching
- **Graceful Degradation**: Fallback to static data when API fails

## Timeline

### Week 1: Core Fixes
- Fix API integration issues
- Implement proper data parsing
- Add comprehensive error handling

### Week 2: Frontend Completion
- Complete JavaScript implementation
- Implement filtering functionality
- Add user interface improvements

### Week 3: Testing and Optimization
- Performance testing and optimization
- Cross-browser testing
- User acceptance testing

### Week 4: Deployment and Monitoring
- Production deployment
- Monitoring setup
- Documentation updates

## Conclusion

This PRD outlines a comprehensive plan to transform the current non-functional Wiener Linien Live Map into a robust, user-friendly real-time public transport visualization tool. The focus is on fixing critical API integration issues while maintaining the existing architecture and adding necessary improvements for reliability and user experience. 