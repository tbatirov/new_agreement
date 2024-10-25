import os
from openai import OpenAI
from templates import AGREEMENT_TEMPLATES
import json

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_template_suggestions(user_input: str) -> list:
    """Get template suggestions based on user input."""
    prompt = f"""Analyze the following user input and suggest the most appropriate legal agreement template from our available templates. Consider the context and key terms mentioned.
    Available templates: {[template['name'] for template in AGREEMENT_TEMPLATES.values()]}
    
    User input: {user_input}
    
    Return a JSON object with:
    1. best_match: The name of the best matching template
    2. confidence: A number between 0 and 1 indicating match confidence
    3. explanation: A brief explanation of why this template was chosen
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
