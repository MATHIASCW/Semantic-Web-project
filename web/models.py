"""
Data models for Tolkien Knowledge Graph resources.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TimelineEvent:
    """Represents a single timeline period/event."""
    label: str
    start: str
    end: str
    color: str = ""
    era: str = ""


@dataclass
class ResourceProperty:
    """A single property value pair."""
    predicate: str
    values: List[str] = field(default_factory=list)
    
    def is_uri(self) -> bool:
        """Check if all values are URIs."""
        return all(v.startswith('http://') or v.startswith('https://') for v in self.values)


@dataclass
class ResourceData:
    """Complete data for a resource (character, location, etc.)."""
    name: str
    uri: str
    properties: Dict[str, List[str]]
    
    def get_property(self, predicate: str) -> Optional[List[str]]:
        """Get a property by predicate URI."""
        return self.properties.get(predicate)
    
    def get_first_value(self, predicate: str) -> Optional[str]:
        """Get the first value of a property."""
        values = self.properties.get(predicate)
        return values[0] if values else None
    
    def has_property(self, predicate: str) -> bool:
        """Check if resource has a property."""
        return predicate in self.properties


@dataclass
class PageContent:
    """Content structure for HTML page rendering."""
    resource: ResourceData
    image_url: Optional[str] = None
    summary_data: Dict[str, str] = field(default_factory=dict)
    timeline_events: List[TimelineEvent] = field(default_factory=list)
    properties_to_display: Dict[str, List[str]] = field(default_factory=dict)
    
    @property
    def is_found(self) -> bool:
        """Check if resource was found."""
        return self.resource is not None
