"""The interviewer brain: grounded but adaptive.

One LLM call per turn returns BOTH the grade and the next spoken line, so each
turn is a single round-trip (lower latency). The system prompt enforces that the
ideal answer is never leaked before the candidate attempts.
"""

import json
import os
from functools import lru_cache
from groq import Groq

_LANG = {"en": "English", "hi": "Hindi", "de": "German"}


@lru_cache(maxsize=1)
def _client() -> Groq:
    return Groq(api_key=os.environ["GROQ_API_KEY"])


SYSTEM = """You are a warm, natural-sounding interviewer for the role: {role}.
You conduct a spoken mock interview entirely in {language}.

Talk the way a real person speaks out loud: use contractions, short sentences,
and easy connectors like "Alright,", "Got it,", "Okay,", "Makes sense.". Sound
relaxed and human, never stiff or formal. This is voice, not an essay.

You are privately given the current question, its ideal answer, and its key
points. Always:
- NEVER read the ideal answer or key points aloud before the candidate has
  attempted. Never say "the ideal answer is...". Do not list the key points.
- Grade the candidate's latest answer against the key points.
- One question at a time. Stay in character. Never break the fourth wall.

{policy}

Return ONLY valid JSON with these keys:
{{"verdict":"strong|partial|weak","covered":[...],"missing":[...],
  "score":0-10,"action":"advance|follow_up|coach_advance",
  "say":"<the spoken line, in {language}>"}}"""

FOLLOWUP_POLICY = """Follow-up policy:
- If STRONG: brief acknowledgement, then move on (action="advance").
- If PARTIAL: ask ONE focused follow-up that probes a MISSING point without
  revealing it (action="follow_up").
- If WEAK and attempts remain: one encouraging hint or reframed follow-up
  (action="follow_up").
- If attempts are exhausted: briefly COACH the candidate in 1-2 sentences on
  what a strong answer covers (now you MAY teach), then move on
  (action="coach_advance")."""

NOFOLLOWUP_POLICY = """Follow-up policy: FOLLOW-UPS ARE DISABLED.
- Regardless of answer quality, give ONE short, warm acknowledgement
  (e.g. "Got it, thanks." / "Makes sense.") and set action="advance".
- Never ask a follow-up question. Never coach. Never reveal the ideal answer.
- Keep the acknowledgement to a single short sentence."""


class InterviewSession:
    def __init__(self, retriever, cfg):
        self.r = retriever
        self.cfg = cfg
        self.lang = cfg["language"]
        self.max_attempts = cfg.get("max_attempts", 2)
        self.follow_ups = cfg.get("follow_ups", True)
        # cap how many questions get asked this session (0/None = all)
        self.total = min(cfg.get("num_questions") or len(retriever),
                         len(retriever))
        self.idx = 0
        self.attempts = 0
        self.history = []   # list of (role, text)
        self.records = []   # per-question evaluations for final feedback

    @property
    def finished(self) -> bool:
        return self.idx >= self.total

    def opening_line(self) -> str:
        q = self.r.get(0)["question"]
        intros = {
            "en": f"Hi! Thanks for joining. Let's begin. {q}",
            "hi": f"नमस्ते! जुड़ने के लिए धन्यवाद। चलिए शुरू करते हैं। {q}",
            "de": f"Hallo! Danke, dass Sie dabei sind. Fangen wir an. {q}",
        }
        line = intros.get(self.lang, intros["en"])
        self.history.append(("interviewer", line))
        return line

    def handle_turn(self, candidate_text: str) -> str:
        self.history.append(("candidate", candidate_text))
        q = self.r.get(self.idx)

        ctx = "\n".join(f"{r.upper()}: {t}" for r, t in self.history[-6:])
        user = (
            f"CURRENT QUESTION: {q['question']}\n"
            f"IDEAL ANSWER (private): {q['ideal_answer']}\n"
            f"KEY POINTS (private): {q['key_points']}\n"
            f"ATTEMPTS USED ON THIS QUESTION: {self.attempts} "
            f"(max {self.max_attempts})\n\n"
            f"RECENT TRANSCRIPT:\n{ctx}\n\n"
            f"CANDIDATE'S LATEST ANSWER: {candidate_text}\n"
            "Grade it and produce the next spoken line per the rules."
        )

        resp = _client().chat.completions.create(
            model=self.cfg["llm"]["model"],
            temperature=self.cfg["llm"].get("temperature", 0.4),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM.format(
                    role=self.r.role, language=_LANG[self.lang],
                    policy=(FOLLOWUP_POLICY if self.follow_ups
                            else NOFOLLOWUP_POLICY))},
                {"role": "user", "content": user},
            ],
        )
        d = json.loads(resp.choices[0].message.content)

        self.attempts += 1
        # force-advance if follow-ups are off, or attempts are exhausted
        advancing = (not self.follow_ups
                     or d.get("action") in ("advance", "coach_advance")
                     or self.attempts >= self.max_attempts)

        if advancing:
            self.records.append({
                "question": q["question"],
                "verdict": d.get("verdict"),
                "score": d.get("score"),
                "covered": d.get("covered", []),
                "missing": d.get("missing", []),
            })
            self.idx += 1
            self.attempts = 0
            if not self.finished:
                nxt = self.r.get(self.idx)["question"]
                d["say"] = f"{d['say']} {nxt}"

        self.history.append(("interviewer", d["say"]))
        return d["say"]
