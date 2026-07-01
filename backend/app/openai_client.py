import json
import logging
from typing import Any, Dict, List
from openai import OpenAI, APIError
from .config import settings

logger = logging.getLogger(__name__)
client = OpenAI(api_key=settings.openai_api_key)

def create_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    try:
        texts = [t.strip() for t in texts if t.strip()]
        if not texts:
            return []
        resp = client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in resp.data]
    except APIError as e:
        logger.error(f"OpenAI embedding error: {e}")
        raise

def parse_resume_text(resume_text: str) -> Dict[str, Any]:
    if not resume_text or not resume_text.strip():
        return {"error": "Empty resume text"}
    try:
        system_prompt = "You are a resume parser. Extract resume information and return ONLY valid JSON. No markdown."
        user_prompt = f"Parse this resume into JSON with fields: name, email, phone, location, summary, experiences (array), education (array), skills (array).\n\nResume:\n{resume_text}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.0,
            max_tokens=2000
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "").strip()
        parsed = json.loads(text)
        logger.info(f"Resume parsed: {parsed.get('name', 'Unknown')}")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}")
        return {"error": "Failed to parse resume"}
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        return {"error": str(e)}

def generate_feedback(resume_json: Dict[str, Any], job_json: Dict[str, Any]) -> Dict[str, Any]:
    try:
        system_prompt = "You are a career coach. Return ONLY valid JSON with no markdown."
        user_prompt = f"Compare resume to job. Return JSON with: match_score (0-100), match_explanation, resume_edits (array), cover_letter_hook.\n\nResume: {json.dumps(resume_json)[:1000]}\n\nJob: {json.dumps(job_json)[:1000]}"
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.3,
            max_tokens=800
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except:
        return {"error": "Failed to generate feedback"}
