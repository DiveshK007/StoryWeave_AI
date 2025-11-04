"""
Mixpanel analytics integration for StoryWeave AI backend.

Provides event tracking, user property management, and analytics utilities.
"""
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
import mixpanel
from .settings import settings
from .logger import logger

# Initialize Mixpanel client
_mixpanel_client: Optional[mixpanel.Mixpanel] = None


def init_mixpanel(token: Optional[str] = None):
    """
    Initialize Mixpanel client.
    
    Args:
        token: Mixpanel project token (defaults to MIXPANEL_TOKEN env var)
    """
    global _mixpanel_client
    
    token = token or os.getenv("MIXPANEL_TOKEN")
    
    if not token:
        logger.warning("Mixpanel token not provided. Analytics disabled.")
        return None
    
    try:
        _mixpanel_client = mixpanel.Mixpanel(token)
        logger.info("Mixpanel initialized successfully")
        return _mixpanel_client
    except Exception as e:
        logger.error(f"Failed to initialize Mixpanel: {e}")
        return None


def get_client() -> Optional[mixpanel.Mixpanel]:
    """Get Mixpanel client instance."""
    global _mixpanel_client
    
    if _mixpanel_client is None:
        init_mixpanel()
    
    return _mixpanel_client


def _track_event(
    distinct_id: str,
    event_name: str,
    properties: Optional[Dict[str, Any]] = None
):
    """
    Track an event in Mixpanel.
    
    Args:
        distinct_id: User identifier
        event_name: Name of the event
        properties: Event properties
    """
    client = get_client()
    if not client:
        return
    
    # Add default properties
    default_properties = {
        "timestamp": int(time.time()),
        "app_version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": settings.ENVIRONMENT,
    }
    
    if properties:
        default_properties.update(properties)
    
    try:
        client.track(distinct_id, event_name, default_properties)
    except Exception as e:
        logger.error(f"Failed to track event {event_name}: {e}")


def _set_user_property(distinct_id: str, properties: Dict[str, Any]):
    """
    Set user properties in Mixpanel.
    
    Args:
        distinct_id: User identifier
        properties: User properties to set
    """
    client = get_client()
    if not client:
        return
    
    try:
        client.people_set(distinct_id, properties)
    except Exception as e:
        logger.error(f"Failed to set user properties: {e}")


def _increment_user_property(distinct_id: str, property_name: str, value: int = 1):
    """
    Increment a user property.
    
    Args:
        distinct_id: User identifier
        property_name: Property name to increment
        value: Amount to increment by
    """
    client = get_client()
    if not client:
        return
    
    try:
        client.people_increment(distinct_id, {property_name: value})
    except Exception as e:
        logger.error(f"Failed to increment property {property_name}: {e}")


# Event Tracking Functions

def track_user_registered(user_id: int, email: Optional[str] = None, source: Optional[str] = None):
    """
    Track user registration event.
    
    Args:
        user_id: User ID
        email: User email
        source: Registration source (optional)
    """
    distinct_id = str(user_id)
    
    properties = {
        "source": source or "unknown",
    }
    
    if email:
        properties["email_domain"] = email.split("@")[-1] if "@" in email else None
    
    _track_event(distinct_id, "user_registered", properties)
    
    # Set user properties
    user_properties = {
        "signup_date": datetime.now().isoformat(),
        "total_stories_created": 0,
        "last_active": datetime.now().isoformat(),
    }
    
    if email:
        user_properties["email"] = email
    
    _set_user_property(distinct_id, user_properties)


def track_story_created(
    user_id: int,
    story_id: int,
    genre: Optional[str] = None,
    length: Optional[str] = None,
    has_corpus: bool = False
):
    """
    Track story creation event.
    
    Args:
        user_id: User ID
        story_id: Story ID
        genre: Story genre
        length: Story length
        has_corpus: Whether corpus was used
    """
    distinct_id = str(user_id)
    
    properties = {
        "story_id": story_id,
        "genre": genre or "unknown",
        "length": length or "unknown",
        "has_corpus": has_corpus,
    }
    
    _track_event(distinct_id, "story_created", properties)
    
    # Increment total stories count
    _increment_user_property(distinct_id, "total_stories_created")
    
    # Update favorite genre (increment genre counter)
    if genre:
        _increment_user_property(distinct_id, f"genre_{genre.lower().replace(' ', '_')}_count")


def track_outline_generated(
    user_id: int,
    story_id: int,
    generation_time: float,
    beat_count: int,
    genre: Optional[str] = None
):
    """
    Track outline generation event.
    
    Args:
        user_id: User ID
        story_id: Story ID
        generation_time: Time taken to generate (seconds)
        beat_count: Number of beats in outline
        genre: Story genre
    """
    distinct_id = str(user_id)
    
    properties = {
        "story_id": story_id,
        "generation_time": round(generation_time, 2),
        "beat_count": beat_count,
        "genre": genre or "unknown",
    }
    
    _track_event(distinct_id, "outline_generated", properties)


def track_scene_expanded(
    user_id: int,
    story_id: int,
    beat_index: int,
    scene_length: int,
    generation_time: Optional[float] = None
):
    """
    Track scene expansion event.
    
    Args:
        user_id: User ID
        story_id: Story ID
        beat_index: Index of the beat
        scene_length: Length of generated scene (characters)
        generation_time: Time taken to generate (seconds)
    """
    distinct_id = str(user_id)
    
    properties = {
        "story_id": story_id,
        "beat_index": beat_index,
        "scene_length": scene_length,
    }
    
    if generation_time:
        properties["generation_time"] = round(generation_time, 2)
    
    _track_event(distinct_id, "scene_expanded", properties)


def track_story_exported(
    user_id: int,
    story_id: int,
    format: str,
    scene_count: int,
    total_length: Optional[int] = None
):
    """
    Track story export event.
    
    Args:
        user_id: User ID
        story_id: Story ID
        format: Export format (txt, pdf, etc.)
        scene_count: Number of scenes exported
        total_length: Total length of exported story
    """
    distinct_id = str(user_id)
    
    properties = {
        "story_id": story_id,
        "format": format,
        "scene_count": scene_count,
    }
    
    if total_length:
        properties["total_length"] = total_length
    
    _track_event(distinct_id, "story_exported", properties)


def track_error_occurred(
    user_id: Optional[int],
    error_type: str,
    endpoint: Optional[str] = None,
    error_message: Optional[str] = None,
    **kwargs
):
    """
    Track error occurrence.
    
    Args:
        user_id: User ID (optional)
        error_type: Type of error
        endpoint: API endpoint where error occurred
        error_message: Error message
        **kwargs: Additional error properties
    """
    distinct_id = str(user_id) if user_id else "anonymous"
    
    properties = {
        "error_type": error_type,
        "endpoint": endpoint or "unknown",
    }
    
    if error_message:
        properties["error_message"] = error_message[:200]  # Limit length
    
    properties.update(kwargs)
    
    _track_event(distinct_id, "error_occurred", properties)


def track_api_call(
    user_id: Optional[int],
    endpoint: str,
    method: str,
    response_time: float,
    status_code: int
):
    """
    Track API call performance.
    
    Args:
        user_id: User ID (optional)
        endpoint: API endpoint
        method: HTTP method
        response_time: Response time in seconds
        status_code: HTTP status code
    """
    distinct_id = str(user_id) if user_id else "anonymous"
    
    properties = {
        "endpoint": endpoint,
        "method": method,
        "response_time": round(response_time, 3),
        "status_code": status_code,
    }
    
    _track_event(distinct_id, "api_call", properties)


def update_user_last_active(user_id: int):
    """
    Update user's last active timestamp.
    
    Args:
        user_id: User ID
    """
    distinct_id = str(user_id)
    _set_user_property(distinct_id, {
        "last_active": datetime.now().isoformat()
    })


def set_user_subscription_tier(user_id: int, tier: str):
    """
    Set user subscription tier.
    
    Args:
        user_id: User ID
        tier: Subscription tier (free, pro, enterprise)
    """
    distinct_id = str(user_id)
    _set_user_property(distinct_id, {
        "subscription_tier": tier
    })


def set_user_favorite_genre(user_id: int, genre: str):
    """
    Update user's favorite genre.
    
    Args:
        user_id: User ID
        genre: Favorite genre
    """
    distinct_id = str(user_id)
    _set_user_property(distinct_id, {
        "favorite_genre": genre
    })


# Initialize on import
init_mixpanel()
