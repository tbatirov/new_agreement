import os
from openai import OpenAI
from templates import AGREEMENT_TEMPLATES
import json
import re

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_industry_context(text: str) -> dict:
    """Analyze the industry context and specific terminology."""
    prompt = f"""Analyze the following text and identify industry-specific context. Return a JSON object with:
    1. industry: The primary industry this agreement relates to
    2. terminology: List of industry-specific terms with explanations
    3. compliance_requirements: List of relevant compliance considerations
    4. jurisdiction_hints: Any mentioned or implied jurisdictions
    5. risk_factors: List of potential legal or business risks
    
    Text to analyze: {text}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content) if content else {}
        return result
    except Exception as e:
        print(f"Error analyzing industry context: {str(e)}")
        return {}

def get_template_suggestions(user_input: str) -> dict:
    """Get enhanced template suggestions with semantic analysis."""
    # First, get industry context
    context = analyze_industry_context(user_input)
    
    prompt = f"""Analyze the following user input and provide detailed suggestions. Return a JSON object with:
    1. template_matches: Array of objects containing:
        - template_name: Name of the template
        - confidence_score: Number between 0-1
        - matching_factors: List of reasons why this template matches
        - customization_needed: List of suggested customizations
        - template_id: Template identifier
    2. industry_context: {json.dumps(context)}
    3. key_elements: List of important elements detected in the input
    4. semantic_analysis: {{
        "key_concepts": List of main legal concepts,
        "relationship_type": Type of relationship being established,
        "obligation_analysis": Key obligations for each party
    }}
    5. compliance_suggestions: List of relevant compliance requirements
    6. risk_assessment: {{
        "risk_level": "low", "medium", or "high",
        "risk_factors": List of potential risks,
        "mitigation_suggestions": List of suggested mitigations
    }}
    
    Available templates: {[template['name'] for template in AGREEMENT_TEMPLATES.values()]}
    User input: {user_input}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty response.")
            
        result = json.loads(content)
        
        # Find best matching template and add template_id
        if result.get('template_matches'):
            best_match = max(result['template_matches'], 
                           key=lambda x: x['confidence_score'])
            result['best_match'] = best_match['template_name']
            result['confidence'] = best_match['confidence_score']
            
            for template_id, template_data in AGREEMENT_TEMPLATES.items():
                if template_data['name'] == best_match['template_name']:
                    best_match['template_id'] = template_id
                    break
        
        return result
    except Exception as e:
        print(f"Error getting template suggestions: {str(e)}")
        return {}

def analyze_and_format_text(text: str) -> dict:
    """Enhanced analysis and formatting of agreement text."""
    prompt = f"""Analyze and improve the following legal agreement text. Return a JSON object with:
    1. formatted_text: The text formatted in clear, simple language
    2. key_terms: Array of objects containing:
        - term: The legal term
        - definition: Plain language explanation
        - risk_level: "low", "medium", or "high"
        - context: Additional context or usage notes
    3. missing_details: Array of objects containing:
        - field: The missing field
        - importance: "required" or "recommended"
        - context: Why this field is important
        - suggestions: Example values or guidance
    4. improvements: Array of objects containing:
        - type: "clarity", "completeness", "compliance", or "risk"
        - suggestion: The improvement suggestion
        - priority: "high", "medium", or "low"
    5. compliance_analysis: {{
        "jurisdiction": Detected or recommended jurisdiction,
        "requirements": List of relevant compliance requirements,
        "gaps": List of potential compliance gaps,
        "recommendations": List of compliance-related suggestions
    }}
    6. risk_highlights: Array of objects containing:
        - text: The highlighted text
        - risk_type: Type of risk
        - severity: "high", "medium", or "low"
        - mitigation: Suggested mitigation
    
    Text to analyze: {text}
    """
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("OpenAI returned an empty response.")
            
        result = json.loads(content)
        result['highlights'] = highlight_key_elements(text)
        return result
    except Exception as e:
        print(f"Error analyzing text: {str(e)}")
        return {}

def highlight_key_elements(text: str) -> dict:
    """Identify and highlight key elements with enhanced patterns."""
    patterns = {
        'amounts': r'\$\s*[\d,]+(?:\.\d{2})?|\d+(?:\.\d{2})?\s*dollars',
        'dates': r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},\s+\d{4}\b',
        'names': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b(?:\s+(?:LLC|Inc\.|Corporation|Corp\.|Ltd\.|Limited|Company|Co\.|LP|LLP|PC|DBA|S\.A\.|N\.A\.|AG|SE|GmbH|Pty\.|PLC))?\b',
        'legal_terms': r'\b(?:hereby|whereas|shall|pursuant to|notwithstanding|herein|thereof|thereto|hereunder)\b',
        'obligations': r'\b(?:must|shall|will|agrees to|is required to|undertakes to)\b',
        'conditions': r'\b(?:provided that|subject to|contingent upon|in the event that|if and only if)\b'
    }
    
    highlights = {}
    for key, pattern in patterns.items():
        highlights[key] = [match.group() for match in re.finditer(pattern, text)]
    
    return highlights
