# Architecture Note — Voice Interview Agent

## 1. Retrieval design

**Store & format.** The reference Q&A lives in plain YAML files
(`questions/*.yaml`). Each entry has an `id`, the `question` asked aloud, a
private `ideal_answer`, and a list of `key_points`. YAML was chosen over a
database or vector store on disk because the hard requirement is *editability
without code changes* — a non-engineer can add a question by copying a block.

All access is funnelled through one module, `core/qa_store.py`, which is the
single source of truth: it loads, validates, lists, and saves question sets, so
the interview logic never touches files or formats directly. This buys three
properties that make the "easy to update" requirement concrete:
- **Auto-discovery** — every `*.yaml` in `questions/` becomes a selectable set
  in the UI automatically; adding a domain is just dropping a file in.
- **Validation** — a malformed set raises a clear, user-facing error naming the
  offending question and field, rather than crashing mid-interview.
- **Hot-reload + in-app editing** — the retriever is cached on the file's mtime,
  so hand-edits show up without a restart, and an in-app grid editor writes
  changes back to the YAML. Both paths leave the core logic untouched.

**Chunking.** Each Q&A pair is its own atomic chunk. There is no need to split:
an ideal answer is a few sentences, well under any context limit, and splitting
would only fragment the grading signal. The unit of retrieval is therefore "one
reference question," which maps exactly to one interview turn.

**Matching.** The interview is **index-driven**: the agent walks the question
list in order and fetches the current reference directly by index
(`retriever.get(idx)`). This is deliberate — the set of questions is fixed and
the interviewer, not the candidate, decides what is asked, so semantic search to
*select* the question would be the wrong tool. Embeddings
(`all-MiniLM-L6-v2`, normalized) still back a `semantic_search` method, used to
detect off-topic answers and to support open-ended lookup; similarity is a plain
normalized dot product (cosine) over the 8–12 vectors.

**Why brute-force, not FAISS.** With only 8–12 reference vectors, a brute-force
cosine scan is O(12) — microseconds. A FAISS/ANN index adds build time, a
dependency, and approximation error while delivering no recall or latency
benefit at this scale. Choosing the simpler structure that fits the data size is
the right engineering call; the design would switch to an index only if the bank
grew into the thousands.

## 2. Keeping the LLM an interviewer (grounded, not leaky)

The interviewer is a single LLM call per turn (`core/interviewer.py`) whose
system prompt is given the current question, its ideal answer, and its key
points **privately**, alongside the recent transcript. The prompt is engineered
around three behaviours:

- **No answer leaking.** Explicit, repeated instruction: never read the ideal
  answer or key points aloud before the candidate has attempted. The ideal
  answer is used only to *grade*, never to *speak*. Coaching is unlocked only
  after attempts are exhausted, where teaching is the point.
- **Adaptive follow-ups.** The model grades the latest answer against the key
  points and returns a `verdict` (strong/partial/weak). Strong → acknowledge and
  advance. Partial/weak with attempts left → one focused follow-up that probes a
  *missing* point without naming it. This is what makes it feel like a real
  interviewer rather than a quiz.
- **Staying on track.** The agent owns question order via the index, so the
  conversation cannot wander off the reference set. A hard cap (`max_attempts`)
  guarantees forward progress: the code force-advances when attempts run out,
  regardless of what the model proposes, so the LLM can't loop forever.

**Structured I/O.** The call uses JSON mode and returns both the grade *and* the
next spoken line in one object (`verdict`, `covered`, `missing`, `score`,
`action`, `say`). Grades are accumulated and fed to a separate feedback call at
the end for an overall score, strengths, improvements, and a recommendation.
Combining grade + next line in one call is a deliberate latency choice (below).

## 3. Latency

A voice turn is: **record → STT → LLM → TTS → playback.** Measured roughly:

| Stage | Approx. cost | Notes |
|-------|-------------|-------|
| STT (Groq Whisper) | ~0.5–1.0 s | scales with clip length |
| LLM (Groq LLaMA 3.3) | ~0.4–0.8 s | Groq is the fast part; chosen for exactly this |
| TTS (ElevenLabs) | ~0.6–1.5 s | dominant cost; network + synthesis |
| **Total** | **~1.5–3 s** | per turn |

**Where time goes:** STT and TTS dominate; the LLM is comparatively cheap, which
is the entire reason for picking Groq. The current prototype waits for each stage
to finish before starting the next.

**How I'd reduce it:**
1. **Stream TTS from the LLM token stream** — begin synthesizing the first
   sentence as soon as the model emits it, instead of waiting for the full
   reply. This overlaps the two most expensive stages and is the single biggest
   win.
2. **One round-trip per turn** — already done: grade + next line come back in a
   single LLM call rather than two.
3. **Smaller model for grading** — a lighter Groq model (e.g. an 8B) can grade
   and pick the next action with lower latency; reserve the larger model only
   where nuance matters.
4. **Streaming STT with VAD** — replace push-to-record with continuous
   transcription so STT finishes almost as the candidate stops speaking, rather
   than starting only after they click stop.
5. **Cache the embedding model load** (done via `@st.cache_resource`) so the
   ~90 MB MiniLM download/load is a one-time cost, not per session.

## Known limitations (prototype scope)
- Push-to-record rather than continuous streaming with voice-activity detection.
- TTS plays after full synthesis (no token-level streaming yet) — item 1 above is
  the planned fix.
