"""LLM summarization service. Supports Gemini (via custom endpoint) or OpenAI as fallback.

Environment variables:
- GEMINI_API_KEY (optional) and GEMINI_ENDPOINT (optional) -- if set, will call that endpoint with Bearer token
- OPENAI_API_KEY (optional) -- fallback to OpenAI Chat Completions
"""
from typing import Any, Dict
import os
import logging
import requests
import json

log = logging.getLogger('service.gemini')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_ENDPOINT = os.getenv('GEMINI_ENDPOINT')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')


def _call_gemini_endpoint(prompt: str) -> str:
    if not GEMINI_API_KEY or not GEMINI_ENDPOINT:
        raise RuntimeError('GEMINI_API_KEY and GEMINI_ENDPOINT must be set to use Gemini provider')
    headers = {'Authorization': f'Bearer {GEMINI_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'prompt': prompt, 'max_output_tokens': 512}
    r = requests.post(GEMINI_ENDPOINT, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    # expect text in data['candidates'][0]['content'] or data['output'] depending on endpoint
    text = None
    if isinstance(data, dict):
        if 'candidates' in data and isinstance(data['candidates'], list) and data['candidates']:
            text = data['candidates'][0].get('content')
        elif 'output' in data and isinstance(data['output'], dict):
            # Google-style
            text = data['output'].get('text') or json.dumps(data['output'])
    return text or json.dumps(data)


def _call_openai_chat(prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError('OPENAI_API_KEY must be set to use OpenAI provider')
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
    body = {
        'model': OPENAI_MODEL,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.0,
        'max_tokens': 512,
    }
    r = requests.post(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    j = r.json()
    # extract assistant content
    try:
        return j['choices'][0]['message']['content']
    except Exception:
        return json.dumps(j)


def summarize_medicine(name: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a structured summary for a medicine as a dict.

    The LLM is instructed to return JSON with keys:
      - purpose
      - approval_status
      - safety_alerts (list)
      - recall_history (list)
      - manufacturer
      - risk_level (low|medium|high)
      - reasoning
    """
    # Build prompt
    prompt_lines = [
        f"You are a medical regulatory assistant. Summarize the following findings about the medicine: {name}.",
        "Return ONLY a JSON object with keys: purpose, approval_status, safety_alerts, recall_history, manufacturer, risk_level, reasoning.",
        "safety_alerts and recall_history should be arrays of short summaries (max 3 items each).",
        "risk_level should be one of: low, medium, high.",
        "Use the context below to derive the answers. If information is missing, be explicit (e.g., null or empty list).",
        "---CONTEXT START---",
    ]
    # attach context sections
    def _attach_section(title: str, obj: Any):
        prompt_lines.append(f"{title}: ")
        try:
            prompt_lines.append(json.dumps(obj, default=str, ensure_ascii=False, indent=2))
        except Exception:
            prompt_lines.append(str(obj))

    _attach_section('Supabase medicine record', context.get('supabase_medicine'))
    _attach_section('Supabase alerts', context.get('alerts'))
    _attach_section('Supabase recalls', context.get('recalls'))
    _attach_section('Supabase reports', context.get('reports'))
    _attach_section('OpenFDA results', context.get('fda'))
    _attach_section('CDSCO notes', context.get('cdsco'))

    prompt_lines.append('---CONTEXT END---')
    prompt = '\n'.join(prompt_lines)

    # Call provider
    try:
        if GEMINI_API_KEY and GEMINI_ENDPOINT:
            text = _call_gemini_endpoint(prompt)
        else:
            text = _call_openai_chat(prompt)
    except Exception as e:
        log.exception('LLM call failed')
        raise

    # Parse JSON from the LLM output
    try:
        # try to find the first JSON object in text
        start = text.find('{')
        if start >= 0:
            candidate = text[start:]
            obj = json.loads(candidate)
            return obj
        else:
            # fallback: return text as reasoning
            return {'purpose': None, 'approval_status': None, 'safety_alerts': [], 'recall_history': [], 'manufacturer': None, 'risk_level': 'unknown', 'reasoning': text}
    except Exception:
        log.exception('Failed to parse LLM JSON response')
        return {'purpose': None, 'approval_status': None, 'safety_alerts': [], 'recall_history': [], 'manufacturer': None, 'risk_level': 'unknown', 'reasoning': text}
