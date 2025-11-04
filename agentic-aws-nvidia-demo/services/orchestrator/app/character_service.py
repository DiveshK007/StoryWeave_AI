"""
Character generation and consistency checking services.
"""
from typing import Dict, Any, List, Optional
import json
import re
from .nim_client import call_llm
from .logger import logger
from .settings import settings


async def generate_character_profile(
    name: str,
    role: str,
    story_premise: Optional[str] = None,
    genre: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive character profile using LLM.
    
    Args:
        name: Character name
        role: Character role (protagonist/antagonist/supporting)
        story_premise: Story premise for context
        genre: Story genre for context
    
    Returns:
        Dictionary with character profile fields
    """
    prompt = f"""You are a character development expert. Create a comprehensive character profile.

Character Name: {name}
Role: {role}
"""
    
    if story_premise:
        prompt += f"Story Premise: {story_premise}\n"
    if genre:
        prompt += f"Genre: {genre}\n"
    
    prompt += """
Generate a detailed character profile in JSON format with the following structure:
{
  "physical_description": "Detailed physical appearance including age, build, distinctive features, clothing style",
  "personality_traits": ["trait1", "trait2", "trait3", "trait4", "trait5"],
  "backstory": "Character's background, history, and formative experiences",
  "goals": ["primary goal", "secondary goal", "internal goal"],
  "motivations": "What drives this character",
  "fears": ["fear1", "fear2"],
  "flaws": ["flaw1", "flaw2", "flaw3"],
  "strengths": ["strength1", "strength2", "strength3"],
  "speech_patterns": "How they talk - vocabulary, tone, catchphrases, dialect",
  "abilities": ["ability1", "ability2"],
  "knowledge": "Areas of expertise or important knowledge",
  "character_arc": "Suggested character development arc throughout the story"
}

Make the character compelling, three-dimensional, and appropriate for their role. Return ONLY valid JSON.
"""
    
    try:
        response = await call_llm(prompt, settings.LLM_URL, max_tokens=1500)
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            profile = json.loads(json_match.group())
        else:
            # Fallback: try parsing entire response
            profile = json.loads(response)
        
        # Validate required fields
        required_fields = [
            "physical_description", "personality_traits", "backstory",
            "goals", "motivations", "fears", "flaws"
        ]
        for field in required_fields:
            if field not in profile:
                profile[field] = "" if field != "personality_traits" else []
        
        # Ensure lists are actually lists
        if not isinstance(profile.get("personality_traits"), list):
            profile["personality_traits"] = []
        if not isinstance(profile.get("goals"), list):
            profile["goals"] = []
        if not isinstance(profile.get("fears"), list):
            profile["fears"] = []
        if not isinstance(profile.get("flaws"), list):
            profile["flaws"] = []
        if not isinstance(profile.get("strengths"), list):
            profile["strengths"] = []
        if not isinstance(profile.get("abilities"), list):
            profile["abilities"] = []
        
        return profile
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse character profile JSON: {e}")
        # Return default profile structure
        return {
            "physical_description": "Character appearance to be determined",
            "personality_traits": ["Complex", "Multifaceted"],
            "backstory": "Character history to be developed",
            "goals": ["To be determined"],
            "motivations": "Character motivations to be explored",
            "fears": ["Unknown fears"],
            "flaws": ["Human flaws"],
            "strengths": ["Character strengths"],
            "speech_patterns": "Natural speech patterns",
            "abilities": [],
            "knowledge": "Various knowledge areas",
            "character_arc": "Character growth arc to be developed"
        }
    except Exception as e:
        logger.error(f"Error generating character profile: {e}", exc_info=True)
        raise


async def analyze_character_consistency(
    character_name: str,
    character_profile: Dict[str, Any],
    scene_texts: List[str]
) -> Dict[str, Any]:
    """
    Analyze character consistency across scenes.
    
    Args:
        character_name: Name of the character
        character_profile: Character profile dictionary
        scene_texts: List of scene texts to analyze
    
    Returns:
        Dictionary with consistency analysis results
    """
    if not scene_texts:
        return {
            "consistent": True,
            "issues": [],
            "mentions": []
        }
    
    combined_scenes = "\n\n---SCENE BREAK---\n\n".join(scene_texts)
    
    prompt = f"""You are a story editor analyzing character consistency.

Character: {character_name}

Character Profile:
Physical Description: {character_profile.get('physical_description', 'N/A')}
Personality Traits: {', '.join(character_profile.get('personality_traits', []))}
Speech Patterns: {character_profile.get('speech_patterns', 'N/A')}
Abilities: {', '.join(character_profile.get('abilities', []))}
Knowledge: {character_profile.get('knowledge', 'N/A')}

Scenes to Analyze:
{combined_scenes[:5000]}  # Limit to avoid token limits

Analyze the scenes for consistency issues. Check:
1. Physical descriptions match the character profile
2. Speech patterns are consistent
3. Behavior and reactions match personality traits
4. Abilities and knowledge are consistent

Return JSON in this format:
{{
  "consistent": true/false,
  "issues": [
    {{
      "type": "physical|speech|behavior|ability|knowledge",
      "severity": "low|medium|high",
      "description": "Description of the inconsistency",
      "scene_index": 0,
      "evidence": "Quote from scene"
    }}
  ],
  "mentions": [
    {{
      "scene_index": 0,
      "context": "Excerpt where character is mentioned",
      "mention_type": "dialogue|action|description",
      "consistency": "consistent|inconsistent"
    }}
  ]
}}

Return ONLY valid JSON.
"""
    
    try:
        response = await call_llm(prompt, settings.LLM_URL, max_tokens=2000)
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            analysis = json.loads(response)
        
        # Validate structure
        if "consistent" not in analysis:
            analysis["consistent"] = True
        if "issues" not in analysis:
            analysis["issues"] = []
        if "mentions" not in analysis:
            analysis["mentions"] = []
        
        return analysis
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse consistency analysis JSON: {e}")
        return {
            "consistent": True,
            "issues": [],
            "mentions": []
        }
    except Exception as e:
        logger.error(f"Error analyzing character consistency: {e}", exc_info=True)
        return {
            "consistent": True,
            "issues": [],
            "mentions": []
        }


def extract_character_mentions(
    text: str,
    character_names: List[str]
) -> List[Dict[str, Any]]:
    """
    Extract character mentions from text using simple pattern matching.
    
    Args:
        text: Text to search
        character_names: List of character names to find
    
    Returns:
        List of mentions with context
    """
    mentions = []
    sentences = re.split(r'[.!?]+', text)
    
    for char_name in character_names:
        # Case-insensitive search
        pattern = re.compile(r'\b' + re.escape(char_name) + r'\b', re.IGNORECASE)
        
        for i, sentence in enumerate(sentences):
            if pattern.search(sentence):
                # Get context (previous and next sentences)
                start = max(0, i - 1)
                end = min(len(sentences), i + 2)
                context = ' '.join(sentences[start:end]).strip()
                
                # Determine mention type
                mention_type = "description"
                if '"' in sentence or "'" in sentence:
                    mention_type = "dialogue"
                elif any(action_word in sentence.lower() for action_word in ['walked', 'ran', 'looked', 'said', 'did']):
                    mention_type = "action"
                
                mentions.append({
                    "character_name": char_name,
                    "context": context,
                    "mention_type": mention_type
                })
    
    return mentions
