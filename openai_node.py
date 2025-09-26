"""
OpenAI LLM Node for Phase 2
This module handles OpenAI API integration with automatic cost tracking
"""

from typing import Dict, Any, List, Tuple, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# Load environment variables from .env file
load_dotenv()


def stream_openai_response(
    messages: List[Dict[str, Any]], 
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7
):
    """
    Stream OpenAI responses chunk by chunk
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: OpenAI model to use
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
    
    Yields:
        String chunks of the response
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        error_msg = str(e)
        if "insufficient permissions" in error_msg or "model.request" in error_msg:
            yield "⚠️ **API Key Issue**: Your OpenAI API key doesn't have the required permissions.\n\n"
            yield "**To fix this:**\n"
            yield "1. Go to https://platform.openai.com/api-keys\n"
            yield "2. Create a new API key with 'All' permissions\n"
            yield "3. Update your .env file with the new key\n\n"
            yield "**Current Error**: Missing 'model.request' scope"
        else:
            yield f"Error: {error_msg}"


def process_openai_message(
    messages: List[Dict[str, Any]], 
    model: str = "gpt-3.5-turbo",
    streaming: bool = False,
    temperature: float = 0.7
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Process messages using OpenAI's API
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: OpenAI model to use (gpt-3.5-turbo, gpt-4, etc.)
        streaming: Whether to stream the response
        temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
    
    Returns:
        Tuple of (response_dict, metadata_dict)
        - response_dict: Contains role and content
        - metadata_dict: Contains tokens, cost, and model info
    """
    
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        if streaming:
            raise ValueError("For streaming, use stream_openai_response() function instead")
            
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        content = response.choices[0].message.content
        
        # Extract metadata
        metadata = {
            "model": model,
            "streaming": False,
            "tokens_input": response.usage.prompt_tokens if response.usage else 0,
            "tokens_output": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0,
        }
        
        # Calculate cost
        cost = calculate_openai_cost(
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


def calculate_openai_cost(model: str = "gpt-3.5-turbo", input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = None) -> float:
    """
    Calculate the cost of an OpenAI API call based on token usage
    
    Args:
        model: The OpenAI model used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens  
        total_tokens: Total tokens (used if input/output not available)
    
    Returns:
        Cost in USD
    """
    
    # Define pricing per 1000 tokens (in USD)
    # Prices confirmed from OpenAI pricing page (2025)
    pricing = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},  # $0.15/$0.60 per million tokens
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},  # $0.50/$1.50 per million tokens
        "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},  # Same as gpt-3.5-turbo
        "gpt-3.5-turbo-1106": {"input": 0.0005, "output": 0.0015},  # Same as gpt-3.5-turbo
        # Keeping other models for reference only
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
    }
    
    # Get pricing for the model (default to GPT-3.5-turbo pricing if model not found)
    model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
    
    # If total_tokens provided but not input/output, estimate 75% input, 25% output
    if total_tokens and not (input_tokens and output_tokens):
        input_tokens = int(total_tokens * 0.75)
        output_tokens = int(total_tokens * 0.25)
    
    # Calculate cost
    input_cost = (input_tokens / 1000) * model_pricing["input"]
    output_cost = (output_tokens / 1000) * model_pricing["output"]
    total_cost = input_cost + output_cost
    
    return round(total_cost, 6)  # Round to 6 decimal places for precision


def check_openai_api_key() -> bool:
    """
    Check if OpenAI API key is configured
    """
    api_key = os.getenv("OPENAI_API_KEY")
    return api_key is not None and api_key != "your_openai_api_key_here" and len(api_key) > 0