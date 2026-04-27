import json
from openai import OpenAI


def _client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def calculate_ats_score(resume_text: str, job_desc: str, mode: str,
                         model: str, api_key: str) -> dict:
    if mode == 'with_jd':
        system = "You are an expert ATS evaluator. Analyse the resume against the job description. Return ONLY valid JSON."
        user_msg = f"""Evaluate this resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_desc}

Return ONLY this JSON (no markdown, no backticks):
{{
  "score": <integer 0-100>,
  "breakdown": {{
    "keyword_match": <0-100>,
    "formatting": <0-100>,
    "experience_relevance": <0-100>,
    "skills_match": <0-100>,
    "education": <0-100>
  }},
  "missing_keywords": ["keyword1", "keyword2"],
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2",
    "Suggestion 3",
    "Suggestion 4",
    "Suggestion 5"
  ]
}}"""
    else:
        system = "You are an expert ATS evaluator. Analyse the resume on general ATS standards. Return ONLY valid JSON."
        user_msg = f"""Evaluate this resume on general ATS best practices.

RESUME:
{resume_text}

Return ONLY this JSON (no markdown, no backticks):
{{
  "score": <integer 0-100>,
  "breakdown": {{
    "formatting": <0-100>,
    "keyword_density": <0-100>,
    "action_verbs": <0-100>,
    "quantified_achievements": <0-100>,
    "section_structure": <0-100>
  }},
  "missing_keywords": [],
  "suggestions": [
    "Suggestion 1",
    "Suggestion 2",
    "Suggestion 3",
    "Suggestion 4",
    "Suggestion 5"
  ]
}}"""

    client   = _client(api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {'role': 'system', 'content': system},
            {'role': 'user',   'content': user_msg}
        ],
        temperature=0.3, max_tokens=800
    )
    raw  = response.choices[0].message.content.strip()
    raw  = raw.replace('```json', '').replace('```', '').strip()
    data = json.loads(raw)
    data['score']            = max(0, min(100, int(data.get('score', 50))))
    data['breakdown']        = data.get('breakdown', {})
    data['suggestions']      = data.get('suggestions', [])
    data['missing_keywords'] = data.get('missing_keywords', [])
    return data


def improve_resume(resume_text: str, job_desc: str, mode: str,
                   model: str, api_key: str) -> dict:
    if mode == 'with_jd' and job_desc:
        prompt = f"""You are an expert resume writer and ATS optimisation specialist.

Rewrite the resume below to score 85+ on ATS for this job description.

RULES:
- Keep all real facts, companies, dates, technologies exactly as given
- Add strong past-tense action verbs (Built, Designed, Optimised, Implemented, Achieved)
- Incorporate relevant keywords from the job description naturally
- Quantify achievements wherever possible
- Use clean single-column ATS-safe formatting
- Keep standard sections: Profile, Skills, Education, Experience, Projects

JOB DESCRIPTION:
{job_desc}

ORIGINAL RESUME:
{resume_text}

Return ONLY this JSON (no markdown):
{{
  "text": "<full improved resume as plain text with newlines>",
  "new_score": <estimated ATS score after improvement, integer>
}}"""
    else:
        prompt = f"""You are an expert resume writer and ATS optimisation specialist.

Rewrite the resume below to score 85+ on general ATS standards.

RULES:
- Keep all real facts exactly as given
- Add strong action verbs, quantify achievements
- Use clean ATS-safe formatting, standard section headings

ORIGINAL RESUME:
{resume_text}

Return ONLY this JSON (no markdown):
{{
  "text": "<full improved resume as plain text with newlines>",
  "new_score": <estimated ATS score after improvement, integer>
}}"""

    client   = _client(api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.4, max_tokens=2000
    )
    raw  = response.choices[0].message.content.strip()
    raw  = raw.replace('```json', '').replace('```', '').strip()
    data = json.loads(raw)
    data['new_score'] = max(0, min(100, int(data.get('new_score', 80))))
    return data
