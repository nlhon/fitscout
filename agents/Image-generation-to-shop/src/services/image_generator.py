"""
Image Generation Service using Replicate API
Generates outfit images based on user prompts using flux-schnell model
"""

import replicate
from config.settings import settings


async def generate_outfit_image(user_prompt: str) -> str:
    """
    Step 1: Generates an outfit look based on the user prompt.
    Uses 'flux-schnell' for fast generation times.
    
    Args:
        user_prompt: Description of the outfit (e.g., "casual summer dress")
        
    Returns:
        str: Direct URL string of the generated image
        
    Raises:
        ValueError: If API key is not configured
        Exception: If Replicate API fails
    """
    if not settings.REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN not configured")
    
    # Set API token
    replicate.api_token = settings.REPLICATE_API_TOKEN
    
    # Enhance the user input for high-quality fashion studio results
    enhanced_prompt = f"Studio editorial fashion photography of {user_prompt}, full body shot, clean background, professional lighting"
    
    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": enhanced_prompt,
                "num_outputs": 1,
                "guidance_scale": 3.5,
                "num_inference_steps": 4
            }
        )
        
        # Returns the direct URL string of the generated image
        if isinstance(output, list) and len(output) > 0:
            return output[0]
        else:
            raise ValueError("No image generated from Replicate API")
            
    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")


async def generate_multiple_outfits(user_prompt: str, count: int = 3) -> list:
    """
    Generate multiple outfit variations based on a single prompt.
    
    Args:
        user_prompt: Description of the outfit
        count: Number of variations to generate (1-10)
        
    Returns:
        list: List of image URLs
    """
    count = min(max(count, 1), 10)  # Clamp between 1-10
    
    if not settings.REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN not configured")
    
    replicate.api_token = settings.REPLICATE_API_TOKEN
    
    enhanced_prompt = f"Studio editorial fashion photography of {user_prompt}, full body shot, clean background, professional lighting"
    
    try:
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": enhanced_prompt,
                "num_outputs": count,
                "guidance_scale": 3.5,
                "num_inference_steps": 4
            }
        )
        
        if isinstance(output, list):
            return output
        else:
            return [output]
            
    except Exception as e:
        raise Exception(f"Multiple outfit generation failed: {str(e)}")
