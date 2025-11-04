"""
Admin analytics endpoints for StoryWeave AI.

Provides analytics dashboards and metrics via Mixpanel API.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os
import requests
from .settings import settings
from .logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])

MIXPANEL_API_SECRET = os.getenv("MIXPANEL_API_SECRET")
MIXPANEL_PROJECT_ID = os.getenv("MIXPANEL_PROJECT_ID", "").split(":")[0] if os.getenv("MIXPANEL_PROJECT_ID") else None


def get_mixpanel_data(
    endpoint: str,
    params: Dict[str, Any],
    method: str = "GET"
) -> Dict[str, Any]:
    """
    Make request to Mixpanel JQL API.
    
    Args:
        endpoint: API endpoint
        params: Request parameters
        method: HTTP method
    
    Returns:
        Response data
    """
    if not MIXPANEL_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mixpanel API secret not configured"
        )
    
    base_url = "https://mixpanel.com/api/2.0"
    url = f"{base_url}/{endpoint}"
    
    params["api_secret"] = MIXPANEL_API_SECRET
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        else:
            response = requests.post(url, json=params, timeout=10)
        
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Mixpanel API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch analytics data: {str(e)}"
        )


@router.get("/analytics/overview")
async def get_analytics_overview(days: int = 7):
    """
    Get overview analytics for the last N days.
    
    Returns:
        - Daily Active Users (DAU)
        - Stories created per day
        - Average generation time
        - Most popular genres
        - Feature usage funnel
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Get daily active users
        dau_data = get_mixpanel_data("events/properties/top", {
            "event": "page_viewed",
            "name": "$city",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "general",
            "unit": "day",
            "interval": 1,
        })
        
        # Get stories created
        stories_data = get_mixpanel_data("events/properties/top", {
            "event": "story_created",
            "name": "genre",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "general",
            "unit": "day",
            "interval": 1,
        })
        
        # Get outline generation times
        outline_data = get_mixpanel_data("events/properties/top", {
            "event": "outline_generated",
            "name": "generation_time",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "average",
            "unit": "day",
            "interval": 1,
        })
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "dau": {
                "total": dau_data.get("data", {}).get("values", {}).get("$city", 0),
                "daily": dau_data.get("data", {}).get("series", [])
            },
            "stories": {
                "total": stories_data.get("data", {}).get("values", {}).get("genre", {}),
                "daily": stories_data.get("data", {}).get("series", [])
            },
            "generation_time": {
                "average": outline_data.get("data", {}).get("values", {}).get("generation_time", 0),
                "trend": outline_data.get("data", {}).get("series", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analytics overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate analytics: {str(e)}"
        )


@router.get("/analytics/genres")
async def get_genre_analytics(days: int = 30):
    """
    Get genre popularity analytics.
    
    Returns:
        Most popular genres and their statistics
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        data = get_mixpanel_data("events/properties/top", {
            "event": "story_created",
            "name": "genre",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "general",
            "unit": "day",
            "interval": 1,
        })
        
        genres = data.get("data", {}).get("values", {}).get("genre", {})
        
        # Sort by count
        sorted_genres = sorted(
            genres.items(),
            key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
            reverse=True
        )[:10]
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "genres": [
                {"genre": genre, "count": count}
                for genre, count in sorted_genres
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting genre analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get genre analytics: {str(e)}"
        )


@router.get("/analytics/funnel")
async def get_feature_funnel():
    """
    Get feature usage funnel.
    
    Returns:
        Conversion funnel from story creation to export
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    try:
        # Get counts for each step
        events = [
            "story_created",
            "outline_generated",
            "scene_expanded",
            "story_exported"
        ]
        
        funnel_data = {}
        for event in events:
            data = get_mixpanel_data("events/properties/top", {
                "event": event,
                "name": "$city",  # Just to get total count
                "values": [f"{start_date}", f"{end_date}"],
                "type": "general",
            })
            count = sum(data.get("data", {}).get("values", {}).get("$city", {}).values())
            funnel_data[event] = count
        
        # Calculate conversion rates
        conversions = []
        previous_count = None
        for event, count in funnel_data.items():
            conversion_rate = None
            if previous_count and previous_count > 0:
                conversion_rate = (count / previous_count) * 100
            conversions.append({
                "step": event,
                "count": count,
                "conversion_rate": round(conversion_rate, 2) if conversion_rate else None
            })
            previous_count = count
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "funnel": conversions,
            "total": funnel_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting funnel analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get funnel analytics: {str(e)}"
        )


@router.get("/analytics/users")
async def get_user_analytics(days: int = 7):
    """
    Get user analytics.
    
    Returns:
        User engagement metrics
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Get new users
        new_users_data = get_mixpanel_data("events/properties/top", {
            "event": "user_registered",
            "name": "$city",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "general",
            "unit": "day",
            "interval": 1,
        })
        
        # Get active users
        active_users_data = get_mixpanel_data("events/properties/top", {
            "event": "page_viewed",
            "name": "$city",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "unique",
            "unit": "day",
            "interval": 1,
        })
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "new_users": {
                "total": new_users_data.get("data", {}).get("values", {}).get("$city", 0),
                "daily": new_users_data.get("data", {}).get("series", [])
            },
            "active_users": {
                "total": active_users_data.get("data", {}).get("values", {}).get("$city", 0),
                "daily": active_users_data.get("data", {}).get("series", [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user analytics: {str(e)}"
        )


@router.get("/analytics/errors")
async def get_error_analytics(days: int = 7):
    """
    Get error analytics.
    
    Returns:
        Error frequency and types
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    try:
        data = get_mixpanel_data("events/properties/top", {
            "event": "error_occurred",
            "name": "error_type",
            "values": [f"{start_date}", f"{end_date}"],
            "type": "general",
            "unit": "day",
            "interval": 1,
        })
        
        errors = data.get("data", {}).get("values", {}).get("error_type", {})
        
        sorted_errors = sorted(
            errors.items(),
            key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
            reverse=True
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "errors": [
                {"error_type": error_type, "count": count}
                for error_type, count in sorted_errors
            ],
            "total": sum(count for _, count in sorted_errors)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting error analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error analytics: {str(e)}"
        )
