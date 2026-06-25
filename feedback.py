"""End-of-interview structured feedback."""

import json
import os
from functools import lru_cache
from groq import Groq

_LANG = {"en": "English", "hi": "Hindi", "de": "German"}


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


def generate(records, role, cfg) -> dict:
    payload = json.dumps(records, ensure_ascii=False)
    resp = _client().chat.completions.create(
        model=cfg["llm"]["model"],
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content":
                f"You are an interview coach for the role: {role}. "
                f"Write the feedback in {_LANG[cfg['language']]}. "
                "Be specific, constructive, and kind. "
                'Return ONLY valid JSON: {"overall_score":0-100,"summary":"...",'
                '"strengths":[...],"improvements":[...],'
                '"per_question":[{"question":"...","note":"..."}],'
                '"recommendation":"strong hire|lean hire|borderline|not yet"}'},
            {"role": "user", "content": f"Per-question results:\n{payload}"},
        ],
    )
    return json.loads(resp.choices[0].message.content)
