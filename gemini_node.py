"""
This module handles Google Gemini API integration with automatic cost tracking.
"""
import os
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st

# Load environment variables from .env file
load_dotenv()


def configure_gemini():
    """Configure Gemini API with the API key"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)


def stream_gemini_response(
    messages: List[Dict[str, Any]], 
    model: str = "gemini-2.0-flash",
    temperature: float = 0.7
):
    """
    Stream Gemini responses chunk by chunk
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Gemini model to use (gemini-2.0-flash-lite, gemini-2.0-flash, gemini-2.5-flash)
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
    
    Yields:
        String chunks of the response
    """
    try:
        configure_gemini()
        
        # Initialize the model
        model_instance = genai.GenerativeModel(model)
        
        # Convert messages to Gemini format
        # Gemini expects a single prompt, so we'll combine the messages
        prompt = convert_messages_to_gemini_prompt(messages)
        
        # Generate streaming response
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
            ),
            stream=True
        )
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"Error: {str(e)}"


def process_gemini_message(
    messages: List[Dict[str, Any]], 
    model: str = "gemini-2.0-flash-lite",  # CHEAPEST stable model
    streaming: bool = False,
    temperature: float = 0.5  # REDUCED for cost savings
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process messages using Google Gemini API
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: Gemini model to use
        streaming: Whether to stream the response
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        Tuple of (response_dict, metadata_dict)
        - response_dict: Contains role and content
        - metadata_dict: Contains tokens, cost, and model info
    """
    
    try:
        configure_gemini()
        
        if streaming:
            raise ValueError("For streaming, use stream_gemini_response() function instead")
        
        # Initialize the model
        model_instance = genai.GenerativeModel(model)
        
        # Convert messages to Gemini format
        prompt = convert_messages_to_gemini_prompt(messages)
        
        # Generate response
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
            )
        )
        
        content = response.text
        
        # Extract metadata
        metadata = {
            "model": model,
            "streaming": False,
            "tokens_input": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
            "tokens_output": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0,
            "total_tokens": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
        }
        
        # Calculate cost (Gemini is currently free, so cost is 0)
        cost = calculate_gemini_cost(
            model=model,
            input_tokens=metadata['tokens_input'],
            output_tokens=metadata['tokens_output']
        )
        metadata['cost'] = cost
        
        # Return response and metadata
        response_dict = {
            "role": "assistant",
            "content": content
        }
        
        return response_dict, metadata
        
    except Exception as e:
        error_response = {
            "role": "assistant",
            "content": f"Sorry, I encountered an error: {str(e)}"
        }
        error_metadata = {
            "model": model,
            "streaming": False,
            "tokens_input": 0,
            "tokens_output": 0,
            "total_tokens": 0,
            "cost": 0,
            "error": str(e)
        }
        return error_response, error_metadata


def convert_messages_to_gemini_prompt(messages: List[Dict[str, Any]]) -> str:
    """
    Convert OpenAI-style messages to a single prompt for Gemini
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
    
    Returns:
        Single prompt string for Gemini
    """
    prompt_parts = []
    
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        
        if role == "system":
            prompt_parts.append(f"Instructions: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
    
    return "\n\n".join(prompt_parts)


def calculate_gemini_cost(model: str = "gemini-2.0-flash", input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = None) -> float:
    """
    Calculate the cost of a Gemini API call based on token usage
    
    Args:
        model: The Gemini model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens  
        total_tokens: Total tokens (used if input/output not available)
    
    Returns:
        Cost in USD (currently $0 as Gemini is free with rate limits)
    """
    
    # Gemini pricing (as of 2025)
    # Note: Gemini has generous free tier limits
    pricing = {
        "gemini-2.0-flash-lite": {"input": 0.0, "output": 0.0},  # CHEAPEST - Free up to rate limits
        "gemini-2.0-flash": {"input": 0.0, "output": 0.0},       # Free up to rate limits
        "gemini-2.5-flash": {"input": 0.0, "output": 0.0},       # Free up to rate limits
        "gemini-1.5-flash": {"input": 0.0, "output": 0.0},       # Free up to rate limits (deprecated)
        "gemini-1.5-pro": {"input": 0.0, "output": 0.0},         # Free up to rate limits
        "gemini-pro": {"input": 0.0, "output": 0.0},             # Free up to rate limits
    }
    
    # Get pricing for the model (all are currently free)
    model_pricing = pricing.get(model, pricing.get("gemini-2.0-flash", {"input": 0.0, "output": 0.0}))
    
    # Calculate cost (currently $0)
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)


def count_tokens_gemini(text: str, model: str = "gemini-2.0-flash") -> int:
    """
    Count tokens in text using Gemini's tokenizer
    
    Args:
        text: Text to count tokens for
        model: Gemini model to use for counting
    
    Returns:
        Number of tokens
    """
    try:
        configure_gemini()
        model_instance = genai.GenerativeModel(model)
        result = model_instance.count_tokens(text)
        return result.total_tokens
    except Exception:
        # Fallback: rough estimation (4 chars per token)
        return len(text) // 4


def check_gemini_api_key() -> bool:
    """
    Check if Google API key is configured
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    return api_key is not None and api_key != "your_google_api_key_here" and len(api_key) > 0


def get_available_gemini_models() -> List[str]:
    """
    Get list of available Gemini models
    """
    return [
        "gemini-2.0-flash",    # Latest fast model
        "gemini-2.5-flash",   # Advanced model
        "gemini-exp-1206",    # Experimental model
    ]