import os
from openai import OpenAI
from templates import AGREEMENT_TEMPLATES
import json
import re

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_and_format_text(text: str) -> dict:
    """Analyze and format the agreement text in real-time."""
    prompt = f"""Analyze and improve the following legal agreement text. Return a JSON object with:
    1. formatted_text: The text formatted in clear, simple language
    2. key_terms: List of important terms with their definitions
    3. missing_details: List of important details that should be added
    4. suggestions: List of improvements for clarity and completeness
    
    Text to analyze: {text}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty response.")
            
        return json.loads(content)
    except Exception as e:
        print(f"Error analyzing text: {str(e)}")
        return None

def get_template_suggestions(user_input: str) -> dict:
    """Get template suggestions based on user input."""
    prompt = f"""Analyze the following user input and provide detailed suggestions. Return a JSON object with:
    1. best_match: The name of the best matching template
    2. confidence: A number between 0 and 1 indicating match confidence
    3. explanation: A brief explanation of why this template was chosen
    4. key_points: List of key points detected in the input
    5. suggested_additions: List of important clauses or details to consider adding
    6. formatting_suggestions: List of suggestions to improve clarity
    
    Available templates: {[template['name'] for template in AGREEMENT_TEMPLATES.values()]}
    User input: {user_input}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty response.")
            
        result = json.loads(content)
        # Match the template ID based on the name
        for template_id, template_data in AGREEMENT_TEMPLATES.items():
            if template_data['name'] == result['best_match']:
                result['template_id'] = template_id
                break
                
        return result
    except Exception as e:
        print(f"Error getting template suggestions: {str(e)}")
        return None

def highlight_key_elements(text: str) -> dict:
    """Identify and highlight amounts, dates, names, and other key elements."""
    patterns = {
        'amounts': r'\$\s*[\d,]+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*dollars',
        'dates': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b',
        'names': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b(?:\s+(?:LLC|Inc\.|Corporation|Corp\.|Ltd\.|Limited|Company|Co\.|LP|LLP|PC|DBA|S\.A\.|N\.A\.|AG|SE|GmbH|Pty\.|PLC))?\b'
    }
    
    highlights = {}
    for key, pattern in patterns.items():
        highlights[key] = [match.group() for match in re.finditer(pattern, text)]
    
    return highlights
