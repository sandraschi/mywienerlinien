"""
Disruption Alert System for Wiener Linien Live Map

This module provides functionality to monitor, track, and alert users
about service disruptions in Vienna's public transport system.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import threading
import time

logger = logging.getLogger(__name__)

class DisruptionSeverity(Enum):
    """Disruption severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DisruptionType(Enum):
    """Types of disruptions."""
    DELAY = "delay"
    CANCELLATION = "cancellation"
    DETOUR = "detour"
    CLOSURE = "closure"
    TECHNICAL = "technical"
    MAINTENANCE = "maintenance"
    WEATHER = "weather"
    ACCIDENT = "accident"
    OTHER = "other"

class DisruptionStatus(Enum):
    """Disruption status."""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"

@dataclass
class DisruptionAlert:
    """Represents a disruption alert."""
    id: str
    line: str
    type: DisruptionType
    severity: DisruptionSeverity
    status: DisruptionStatus
    title: str
    description: str
    affected_stations: List[str]
    affected_lines: List[str]
    start_time: datetime
    end_time: Optional[datetime]
    estimated_duration: Optional[timedelta]
    created_at: datetime
    updated_at: datetime
    source: str
    external_id: Optional[str] = None
    url: Optional[str] = None
    contact_info: Optional[str] = None

class DisruptionMonitor:
    """Monitors and tracks service disruptions."""
    
    def __init__(self):
        """Initialize the disruption monitor."""
        self.disruptions: Dict[str, DisruptionAlert] = {}
        self.subscribers: List[callable] = []
        self.running = False
        self.monitor_thread = None
        self.last_check = None
        self.check_interval = 60  # Check every 60 seconds
        
        # API configuration
        self.api_base_url = "https://www.wienerlinien.at/ogd_realtime"
        self.api_timeout = 10
        
        # Alert thresholds
        self.severity_thresholds = {
            DisruptionSeverity.LOW: 5,      # 5 minutes delay
            DisruptionSeverity.MEDIUM: 15,  # 15 minutes delay
            DisruptionSeverity.HIGH: 30,    # 30 minutes delay
            DisruptionSeverity.CRITICAL: 60 # 60+ minutes delay
        }
    
    def start_monitoring(self):
        """Start monitoring for disruptions."""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("Disruption monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring for disruptions."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Disruption monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self._check_disruptions()
                self._cleanup_old_disruptions()
                self._update_disruption_status()
                
                # Sleep for check interval
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in disruption monitor loop: {e}")
                time.sleep(10)
    
    def _check_disruptions(self):
        """Check for new disruptions from the API."""
        try:
            # Fetch traffic information from Wiener Linien API
            traffic_info = self._fetch_traffic_info()
            if traffic_info:
                self._process_traffic_info(traffic_info)
            
            # Fetch news and announcements
            news_info = self._fetch_news()
            if news_info:
                self._process_news_info(news_info)
            
            self.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Error checking disruptions: {e}")
    
    def _fetch_traffic_info(self) -> Optional[Dict[str, Any]]:
        """Fetch traffic information from the API."""
        try:
            url = f"{self.api_base_url}/trafficInfo"
            response = requests.get(url, timeout=self.api_timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching traffic info: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing traffic info: {e}")
            return None
    
    def _fetch_news(self) -> Optional[Dict[str, Any]]:
        """Fetch news and announcements from the API."""
        try:
            url = f"{self.api_base_url}/news"
            response = requests.get(url, timeout=self.api_timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching news: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing news: {e}")
            return None
    
    def _process_traffic_info(self, traffic_info: Dict[str, Any]):
        """Process traffic information and extract disruptions."""
        try:
            if 'data' in traffic_info and 'trafficInfos' in traffic_info['data']:
                for info in traffic_info['data']['trafficInfos']:
                    self._create_disruption_from_traffic_info(info)
        except Exception as e:
            logger.error(f"Error processing traffic info: {e}")
    
    def _process_news_info(self, news_info: Dict[str, Any]):
        """Process news information and extract disruptions."""
        try:
            if 'data' in news_info and 'news' in news_info['data']:
                for news in news_info['data']['news']:
                    self._create_disruption_from_news(news)
        except Exception as e:
            logger.error(f"Error processing news info: {e}")
    
    def _create_disruption_from_traffic_info(self, info: Dict[str, Any]):
        """Create a disruption alert from traffic information."""
        try:
            disruption_id = info.get('id', str(datetime.now().timestamp()))
            
            # Check if this disruption already exists
            if disruption_id in self.disruptions:
                self._update_existing_disruption(disruption_id, info)
                return
            
            # Create new disruption
            alert = DisruptionAlert(
                id=disruption_id,
                line=info.get('line', ''),
                type=self._determine_disruption_type(info),
                severity=self._determine_severity(info),
                status=DisruptionStatus.ACTIVE,
                title=info.get('title', 'Service Disruption'),
                description=info.get('description', ''),
                affected_stations=info.get('affectedStations', []),
                affected_lines=info.get('affectedLines', []),
                start_time=datetime.fromisoformat(info.get('startTime', datetime.now().isoformat())),
                end_time=datetime.fromisoformat(info.get('endTime', '')) if info.get('endTime') else None,
                estimated_duration=self._parse_duration(info.get('estimatedDuration')),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source='traffic_info',
                external_id=info.get('externalId'),
                url=info.get('url'),
                contact_info=info.get('contactInfo')
            )
            
            self.disruptions[disruption_id] = alert
            self._notify_subscribers(alert, 'new')
            logger.info(f"Created new disruption alert: {disruption_id}")
            
        except Exception as e:
            logger.error(f"Error creating disruption from traffic info: {e}")
    
    def _create_disruption_from_news(self, news: Dict[str, Any]):
        """Create a disruption alert from news information."""
        try:
            # Check if news is related to disruptions
            if not self._is_disruption_news(news):
                return
            
            disruption_id = f"news_{news.get('id', str(datetime.now().timestamp()))}"
            
            # Check if this disruption already exists
            if disruption_id in self.disruptions:
                return
            
            # Create new disruption
            alert = DisruptionAlert(
                id=disruption_id,
                line=news.get('line', ''),
                type=DisruptionType.OTHER,
                severity=DisruptionSeverity.MEDIUM,
                status=DisruptionStatus.ACTIVE,
                title=news.get('title', 'Service Announcement'),
                description=news.get('content', ''),
                affected_stations=news.get('affectedStations', []),
                affected_lines=news.get('affectedLines', []),
                start_time=datetime.fromisoformat(news.get('publishedAt', datetime.now().isoformat())),
                end_time=None,
                estimated_duration=None,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                source='news',
                external_id=news.get('id'),
                url=news.get('url'),
                contact_info=None
            )
            
            self.disruptions[disruption_id] = alert
            self._notify_subscribers(alert, 'new')
            logger.info(f"Created new disruption alert from news: {disruption_id}")
            
        except Exception as e:
            logger.error(f"Error creating disruption from news: {e}")
    
    def _update_existing_disruption(self, disruption_id: str, info: Dict[str, Any]):
        """Update an existing disruption with new information."""
        try:
            if disruption_id in self.disruptions:
                disruption = self.disruptions[disruption_id]
                disruption.updated_at = datetime.now()
                disruption.description = info.get('description', disruption.description)
                disruption.status = self._determine_status(info)
                
                if info.get('endTime'):
                    disruption.end_time = datetime.fromisoformat(info['endTime'])
                
                self._notify_subscribers(disruption, 'updated')
                logger.info(f"Updated disruption: {disruption_id}")
                
        except Exception as e:
            logger.error(f"Error updating existing disruption: {e}")
    
    def _determine_disruption_type(self, info: Dict[str, Any]) -> DisruptionType:
        """Determine the type of disruption from the information."""
        description = info.get('description', '').lower()
        title = info.get('title', '').lower()
        
        if any(word in description or word in title for word in ['delay', 'verspätung']):
            return DisruptionType.DELAY
        elif any(word in description or word in title for word in ['cancellation', 'cancelled', 'storniert']):
            return DisruptionType.CANCELLATION
        elif any(word in description or word in title for word in ['detour', 'umleitung']):
            return DisruptionType.DETOUR
        elif any(word in description or word in title for word in ['closure', 'closed', 'geschlossen']):
            return DisruptionType.CLOSURE
        elif any(word in description or word in title for word in ['technical', 'technisch']):
            return DisruptionType.TECHNICAL
        elif any(word in description or word in title for word in ['maintenance', 'wartung']):
            return DisruptionType.MAINTENANCE
        elif any(word in description or word in title for word in ['weather', 'wetter']):
            return DisruptionType.WEATHER
        elif any(word in description or word in title for word in ['accident', 'unfall']):
            return DisruptionType.ACCIDENT
        else:
            return DisruptionType.OTHER
    
    def _determine_severity(self, info: Dict[str, Any]) -> DisruptionSeverity:
        """Determine the severity of a disruption."""
        description = info.get('description', '').lower()
        title = info.get('title', '').lower()
        
        # Check for severity indicators in text
        if any(word in description or word in title for word in ['critical', 'kritisch', 'severe', 'schwer']):
            return DisruptionSeverity.CRITICAL
        elif any(word in description or word in title for word in ['major', 'groß', 'significant', 'erheblich']):
            return DisruptionSeverity.HIGH
        elif any(word in description or word in title for word in ['minor', 'klein', 'slight', 'leicht']):
            return DisruptionSeverity.LOW
        else:
            return DisruptionSeverity.MEDIUM
    
    def _determine_status(self, info: Dict[str, Any]) -> DisruptionStatus:
        """Determine the status of a disruption."""
        status = info.get('status', '').lower()
        
        if status in ['resolved', 'gelöst', 'ended', 'beendet']:
            return DisruptionStatus.RESOLVED
        elif status in ['scheduled', 'geplant']:
            return DisruptionStatus.SCHEDULED
        elif status in ['cancelled', 'storniert']:
            return DisruptionStatus.CANCELLED
        else:
            return DisruptionStatus.ACTIVE
    
    def _is_disruption_news(self, news: Dict[str, Any]) -> bool:
        """Check if news is related to disruptions."""
        content = news.get('content', '').lower()
        title = news.get('title', '').lower()
        
        disruption_keywords = [
            'delay', 'verspätung', 'cancellation', 'stornierung',
            'detour', 'umleitung', 'closure', 'schließung',
            'disruption', 'störung', 'problem', 'issue'
        ]
        
        return any(keyword in content or keyword in title for keyword in disruption_keywords)
    
    def _parse_duration(self, duration_str: Optional[str]) -> Optional[timedelta]:
        """Parse duration string into timedelta."""
        if not duration_str:
            return None
        
        try:
            # Parse duration in format like "30 minutes", "2 hours", etc.
            import re
            match = re.match(r'(\d+)\s*(minute|hour|day)s?', duration_str.lower())
            if match:
                value = int(match.group(1))
                unit = match.group(2)
                
                if unit == 'minute':
                    return timedelta(minutes=value)
                elif unit == 'hour':
                    return timedelta(hours=value)
                elif unit == 'day':
                    return timedelta(days=value)
        except Exception as e:
            logger.error(f"Error parsing duration: {e}")
        
        return None
    
    def _cleanup_old_disruptions(self):
        """Remove old resolved disruptions."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)  # Keep for 24 hours
            to_remove = []
            
            for disruption_id, disruption in self.disruptions.items():
                if (disruption.status == DisruptionStatus.RESOLVED and 
                    disruption.updated_at < cutoff_time):
                    to_remove.append(disruption_id)
            
            for disruption_id in to_remove:
                del self.disruptions[disruption_id]
                logger.info(f"Removed old disruption: {disruption_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up old disruptions: {e}")
    
    def _update_disruption_status(self):
        """Update status of disruptions based on time."""
        try:
            current_time = datetime.now()
            
            for disruption in self.disruptions.values():
                if (disruption.end_time and 
                    disruption.end_time < current_time and 
                    disruption.status == DisruptionStatus.ACTIVE):
                    disruption.status = DisruptionStatus.RESOLVED
                    disruption.updated_at = current_time
                    self._notify_subscribers(disruption, 'resolved')
                    logger.info(f"Marked disruption as resolved: {disruption.id}")
                    
        except Exception as e:
            logger.error(f"Error updating disruption status: {e}")
    
    def _notify_subscribers(self, disruption: DisruptionAlert, event_type: str):
        """Notify subscribers about disruption events."""
        for subscriber in self.subscribers:
            try:
                subscriber(disruption, event_type)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def subscribe(self, callback: callable):
        """Subscribe to disruption alerts."""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback: callable):
        """Unsubscribe from disruption alerts."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_active_disruptions(self) -> List[DisruptionAlert]:
        """Get all active disruptions."""
        return [d for d in self.disruptions.values() if d.status == DisruptionStatus.ACTIVE]
    
    def get_disruptions_by_line(self, line: str) -> List[DisruptionAlert]:
        """Get disruptions affecting a specific line."""
        return [d for d in self.disruptions.values() if line in d.affected_lines or line == d.line]
    
    def get_disruptions_by_station(self, station: str) -> List[DisruptionAlert]:
        """Get disruptions affecting a specific station."""
        return [d for d in self.disruptions.values() if station in d.affected_stations]
    
    def get_disruptions_by_severity(self, severity: DisruptionSeverity) -> List[DisruptionAlert]:
        """Get disruptions of a specific severity."""
        return [d for d in self.disruptions.values() if d.severity == severity]
    
    def get_disruption_by_id(self, disruption_id: str) -> Optional[DisruptionAlert]:
        """Get a specific disruption by ID."""
        return self.disruptions.get(disruption_id)
    
    def get_disruption_summary(self) -> Dict[str, Any]:
        """Get a summary of current disruptions."""
        active_disruptions = self.get_active_disruptions()
        
        return {
            'total_active': len(active_disruptions),
            'by_severity': {
                severity.value: len([d for d in active_disruptions if d.severity == severity])
                for severity in DisruptionSeverity
            },
            'by_type': {
                dtype.value: len([d for d in active_disruptions if d.type == dtype])
                for dtype in DisruptionType
            },
            'most_affected_lines': self._get_most_affected_lines(active_disruptions),
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_most_affected_lines(self, disruptions: List[DisruptionAlert]) -> List[str]:
        """Get the most affected lines."""
        line_counts = {}
        for disruption in disruptions:
            for line in disruption.affected_lines:
                line_counts[line] = line_counts.get(line, 0) + 1
        
        # Sort by count and return top 5
        sorted_lines = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)
        return [line for line, count in sorted_lines[:5]]

# Global disruption monitor instance
disruption_monitor = DisruptionMonitor() 