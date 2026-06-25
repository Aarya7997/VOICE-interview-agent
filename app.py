"""Voice Interview Agent — Streamlit front end.

Pipeline per turn:
    mic -> Groq Whisper (STT) -> retriever (current ref Q&A)
        -> Groq LLM turn controller (grade + next line) -> TTS -> autoplay
At the end: structured feedback.
"""

import os
import yaml
import streamlit as st
from dotenv import load_dotenv

load_dotenv()   # must run before any core module touches API keys

from core.retriever import Retriever
from core.stt import transcribe
from core.tts import synthesize
from core.interviewer import InterviewSession
from core import feedback, styles, qa_store

st.set_page_config(page_title="Voice Interview Agent", page_icon="🎙️",
                   layout="centered")
styles.inject(st)


@st.cache_resource
def load_retriever(qa_set: str, _mtime: float) -> Retriever:
    # _mtime is part of the cache key: when the YAML changes, the cached
    # retriever is rebuilt automatically — no restart needed.
    return Retriever(qa_set)


with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

# language switch (overrides config.yaml for this session)
langs = ["en", "hi", "de"]
lang = st.sidebar.selectbox(
    "Language", langs,
    index=langs.index(cfg["language"]) if cfg["language"] in langs else 0,
    format_func=lambda c: {"en": "English", "hi": "हिन्दी", "de": "Deutsch"}[c],
)
cfg["language"] = lang

# question-set picker: auto-discovers every YAML in questions/ (no code change
# needed to add a set — just drop a file in)
sets = qa_store.list_sets()
default_set = cfg["question_set"]
qa_set = st.sidebar.selectbox(
    "Question set", sets,
    index=sets.index(default_set) if default_set in sets else 0,
)
cfg["question_set"] = qa_set
st.sidebar.caption(f"TTS: **{cfg['tts']['provider']}** (falls back to gTTS)")

try:
    r = load_retriever(qa_set, qa_store.mtime(qa_set))
except qa_store.QAValidationError as e:
    st.error(f"Problem in question set '{qa_set}': {e}")
    st.stop()

st.sidebar.caption(f"Role: **{r.role}** · {len(r)} questions")

# how many we'll actually ask this session (config cap)
n_ask = min(cfg.get("num_questions") or len(r), len(r))
lang_name = {"en": "English", "hi": "Hindi", "de": "German"}[lang]
styles.header(st, r.role, n_ask, lang_name, cfg["llm"]["model"])

# ── start screen ──────────────────────────────────────────────────────
if "sess" not in st.session_state:
    st.write("Press **Start** and answer each question out loud. "
             "The agent will follow up, coach you, and score you at the end.")
    if st.button("▶️ Start interview", type="primary"):
        st.session_state.sess = InterviewSession(r, cfg)
        line = st.session_state.sess.opening_line()
        st.session_state.last_audio = synthesize(line, cfg["tts"], lang)
        st.rerun()

    # ── edit the reference Q&A live — no code changes ──────────────────
    with st.expander("✏️ Edit interview questions (no code needed)"):
        data = qa_store.load(qa_set)
        st.caption(f"Editing **{qa_set}** · role: *{data['role']}*. "
                   "Edit any cell, add a row with ➕, or delete with the trash "
                   "icon. Separate key points with `|`.")
        rows = [{
            "question": q["question"],
            "ideal_answer": q["ideal_answer"],
            "key_points": " | ".join(q["key_points"]),
        } for q in data["questions"]]

        edited = st.data_editor(
            rows, num_rows="dynamic", use_container_width=True, key="qedit",
            column_config={
                "question": st.column_config.TextColumn("Question", width="medium"),
                "ideal_answer": st.column_config.TextColumn("Ideal answer", width="large"),
                "key_points": st.column_config.TextColumn("Key points (| separated)", width="medium"),
            },
        )

        if st.button("💾 Save changes"):
            new_questions = []
            for i, row in enumerate(edited, 1):
                if not row.get("question") or not row.get("ideal_answer"):
                    continue
                kp = [k.strip() for k in str(row.get("key_points", "")).split("|")
                      if k.strip()]
                new_questions.append({
                    "id": f"q{i}",
                    "question": row["question"].strip(),
                    "ideal_answer": row["ideal_answer"].strip(),
                    "key_points": kp,
                })
            data["questions"] = new_questions
            try:
                qa_store.save(qa_set, data)
                load_retriever.clear()   # drop stale cache immediately
                st.success(f"Saved {len(new_questions)} questions to "
                           f"{qa_store.path_for(qa_set)}")
                st.rerun()
            except qa_store.QAValidationError as e:
                st.error(str(e))

    st.stop()

sess = st.session_state.sess
sess.lang = lang
sess.cfg["language"] = lang

# ── transcript ────────────────────────────────────────────────────────
for who, text in sess.history:
    st.chat_message("assistant" if who == "interviewer" else "user").write(text)

if "last_audio" in st.session_state:
    audio, mime = st.session_state.last_audio
    st.audio(audio, format=mime, autoplay=True)

# ── interview loop ────────────────────────────────────────────────────
if not sess.finished:
    progress = sess.idx / sess.total
    st.progress(progress, text=f"Question {sess.idx + 1} of {sess.total}")
    clip = st.audio_input("🎤 Record your answer", key=f"mic_{len(sess.history)}")
    if clip is not None:
        with st.spinner("Transcribing and thinking…"):
            text = transcribe(clip.getvalue(), language=lang,
                              model=cfg["stt"]["model"])
            reply = sess.handle_turn(text)
            st.session_state.last_audio = synthesize(reply, cfg["tts"], lang)
        st.rerun()

# ── feedback screen ───────────────────────────────────────────────────
else:
    st.divider()
    st.subheader("📋 Interview Feedback")
    if "fb" not in st.session_state:
        with st.spinner("Generating feedback…"):
            st.session_state.fb = feedback.generate(sess.records, r.role, cfg)
    fb = st.session_state.fb

    st.metric("Overall score", f"{fb['overall_score']}/100")
    st.write(fb["summary"])

    c1, c2 = st.columns(2)
    with c1:
        st.success("**Strengths**\n\n" +
                   "\n".join(f"- {s}" for s in fb["strengths"]))
    with c2:
        st.warning("**Areas to improve**\n\n" +
                   "\n".join(f"- {s}" for s in fb["improvements"]))

    with st.expander("Per-question notes"):
        for p in fb["per_question"]:
            st.markdown(f"**{p['question']}**\n\n{p['note']}")

    st.markdown(
        f'<p style="font-size:1.05rem;margin-top:.6rem">Recommendation: '
        f'<span class="vi-gold">{fb["recommendation"].upper()}</span></p>',
        unsafe_allow_html=True,
    )

    if st.button("🔄 Restart"):
        for k in ("sess", "fb", "last_audio"):
            st.session_state.pop(k, None)
        st.rerun()
