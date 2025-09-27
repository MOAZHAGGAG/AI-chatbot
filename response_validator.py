"""
Response Validator for College Chatbot
This module ensures responses only use information from the provided college data
"""

import re
from typing import List, Dict, Any

# Keywords that should ONLY appear if they're in the college info
RESTRICTED_KEYWORDS = [
    "جامعة القاهرة", "جامعة عين شمس", "الأزهر", "الإسكندرية",
    "Cairo University", "Ain Shams", "Alexandria University",
    "معلومات عامة", "general information", "usually", "typically",
    "في الجامعات المصرية", "Egyptian universities", "most colleges"
]

# Required topics that should be mentioned (these are in the college info)
ALLOWED_TOPICS = [
    "bis", "fmi", "sbs", "تجارة", "commerce", "حلوان", "helwan",
    "انجليش", "عربي", "english", "arabic", "مصاريف", "fees",
    "تقديم", "application", "انترفيو", "interview", "محاسبة", "accounting",
    "ادارة", "management", "اقتصاد", "economics", "احصاء", "statistics"
]

def validate_response(response: str, college_info: str) -> Dict[str, Any]:
    """
    Validate that the response only uses information from college_info
    
    Args:
        response: The AI's response
        college_info: The provided college information
    
    Returns:
        Dict with validation results
    """
    
    issues = []
    
    # Check for restricted keywords
    for keyword in RESTRICTED_KEYWORDS:
        if keyword.lower() in response.lower():
            if keyword.lower() not in college_info.lower():
                issues.append(f"Using external knowledge: '{keyword}'")
    
    # Check for vague language that suggests external knowledge
    vague_patterns = [
        r"عادة|usually|typically|generally|في معظم",
        r"بشكل عام|in general|commonly|often",
        r"في الجامعات|in universities|most colleges"
    ]
    
    for pattern in vague_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            issues.append(f"Using vague/general language: {pattern}")
    
    # Check if mentioning specific numbers not in college info
    numbers_in_response = re.findall(r'\d+', response)
    numbers_in_info = re.findall(r'\d+', college_info)
    
    for num in numbers_in_response:
        if num not in numbers_in_info and len(num) > 2:  # Ignore small numbers
            issues.append(f"Using number not in college info: {num}")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "score": max(0, 100 - len(issues) * 20)  # Score out of 100
    }

def get_fallback_response(question: str, is_arabic: bool = True) -> str:
    """
    Get a fallback response when information is not available
    
    Args:
        question: The user's question
        is_arabic: Whether to respond in Arabic
    
    Returns:
        Appropriate fallback response
    """
    
    if is_arabic:
        return "آسف، المعلومة دي مش متوفرة عندي دلوقتي، بس هتكون متاحة قريب إن شاء الله. ممكن تسأل عن حاجة تانية متعلقة بكلية التجارة جامعة حلوان؟"
    else:
        return "Sorry, I don't have this information right now, but it will be available soon. Can you ask about something else related to the Faculty of Commerce at Helwan University?"

def is_college_related_question(question: str) -> bool:
    """
    Check if the question is related to the college
    
    Args:
        question: The user's question
    
    Returns:
        True if college-related, False otherwise
    """
    
    college_keywords = [
        "كلية", "تجارة", "حلوان", "bis", "fmi", "sbs", "انجليش", "عربي",
        "college", "commerce", "helwan", "english", "arabic", "business",
        "مصاريف", "fees", "تقديم", "admission", "قبول", "acceptance",
        "انتظام", "انتساب", "دراسة", "طلاب", "students", "study",
        "محاسبة", "ادارة", "اقتصاد", "احصاء", "قسم", "department",
        "شهادة", "certificate", "تخرج", "graduation", "سنة", "year",
        "فصل", "semester", "مواد", "subjects", "انترفيو", "interview"
    ]
    
    question_lower = question.lower()
    
    # If contains college keywords, it's college-related
    if any(keyword.lower() in question_lower for keyword in college_keywords):
        return True
    
    # Basic greetings and conversational starters - ALLOW these (will redirect to college)
    greeting_patterns = [
        r'^hello?$', r'^hi$', r'^hey$', r'thanks?', r'thank you',
        r'good (morning|afternoon|evening)', r'how are you',
        r'what.*my name', r'who am i', r'i am \w+', r'my name is'
    ]    
    
    for pattern in greeting_patterns:
        if re.search(pattern, question_lower):
            return True  # Allow greetings - they'll be redirected
    
    # For very short questions without greeting patterns, be restrictive
    if len(question.strip()) <= 2:
        return False
    
    # Only reject clearly inappropriate or harmful content
    inappropriate_patterns = [
        r'how to (hack|steal|cheat)', r'illegal', r'drugs', r'violence',
        r'explicit.*content', r'adult.*content'
    ]
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, question_lower):
            return False
    
    # Allow most questions - let the AI handle them intelligently
    return True

def clean_response(response: str, college_info: str) -> str:
    """
    Clean response to remove any external information
    
    Args:
        response: Original response
        college_info: Provided college information
    
    Returns:
        Cleaned response
    """
    
    validation = validate_response(response, college_info)
    
    if not validation["is_valid"]:
        # If response has issues, return fallback
        is_arabic = any(ord(char) > 127 for char in response)  # Simple Arabic detection
        return get_fallback_response("", is_arabic)
    
    return response