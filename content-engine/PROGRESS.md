# Content Engine — Progress Log

Project 2 of the AI Mastery roadmap. Intelligence synthesis + content creation engine.
Live: https://usman-content-engine.streamlit.app

---

## Session 2 — 2026-05-27

### Shipped
Four production bugs fixed plus architectural hardening.

1. **Action-required persistence.** The "links needing manual paste" list lived only in
   `st.session_state`, so it vanished on every page refresh. Moved it to a Firestore
   `pending_paste` collection. The UI now reads the queue fresh on every render — survives
   refresh, restart, and redeploy.

2. **Duplicate UI removed.** Two action-required sections existed in the same tab — one
   backed by session state, one by Firestore. They masked each other and made the
   persistence bug look unfixed. Deleted the session-state copy. Single source of truth.

3. **Sheet status tracking.** Column G in the source Google Sheet was only marked on
   success. Skipped platforms (Instagram/TikTok) and failed scrapes were left blank, so
   they reappeared as "ready to synthesize" forever, inflating the count. Added a status
   taxonomy: `Done`, `Duplicate`, `Skipped`, `Pending Paste`, `Dismissed`, `Error`. Each
   batch outcome now writes the correct status.

4. **Tier classification bug.** Every record was being classified Tier 1 (100% error rate).
   Root cause: the synthesis prompt's JSON template used a literal example value
   (`"tier": 1`), which the model anchored on and copied regardless of content. Fixed by
   (a) moving tier criteria *before* the JSON template so the model evaluates first,
   (b) replacing literal example values with `<placeholder>` syntax, and
   (c) anchoring the default toward Tier 2/3 ("Tier 1 should be rare").

### Added
- **URL normalization for dedup.** New `normalize_url()` strips tracking params
  (`utm_*`, `fbclid`, `linkId`, `e`, `igshid`, etc.), fragments, and trailing slashes
  before comparison. Catches duplicates that differ only by tracking junk. Backfilled
  `normalized_url` on all existing records.
- **Skip button** on action items — dismiss a URL (e.g. paywalled) without forcing fake
  content. Removes from queue + marks `Dismissed` in the sheet.
- **Theme hallucination fixed** — synthesis prompt now enforces an allowed-themes list
  rather than treating it as a suggestion.
- **Defensive logging** in `get_pending_paste()` so Firestore errors surface visibly
  instead of silently returning an empty list.

### Open items
- Re-classify the ~49 legacy records still tiered T1 under the old prompt.
- Add `.nojekyll` for GitHub Pages.
- Link Content Engine from the personal site.
- Upgrade Python 3.9 → 3.11+ (3.9 is EOL).
- Migrate Firestore `.where("field", "==", v)` to the `filter=FieldFilter(...)` API
  (positional form is deprecated).

---

## Architecture Decision: Firestore over local JSON

### Context
The Content Engine originally stored its intelligence library in a local JSON file
(`intelligence_library.json`). This worked locally but broke on Streamlit Cloud.

### Problem
Streamlit Cloud runs each app in an ephemeral container. On sleep, redeploy, or restart,
the container is rebuilt from the git repo and any runtime-written files are lost. A local
JSON library therefore could not persist records, drafts, or the manual-paste queue across
sessions.

### Decision
Move all persistent state to **Google Cloud Firestore** (NoSQL document store):
- `intelligence_records` — the synthesized library
- `pending_paste` — the manual-paste action queue

Credentials load from a gitignored service-account JSON locally, and from
`st.secrets["FIREBASE_KEY"]` on Streamlit Cloud. The service-account key is never committed.

### Consequences (forward impact)
- **Pattern established:** external persistent state, queried fresh on every render. This
  is now the default for every project in the roadmap — no more relying on local files or
  session state for anything that must survive a restart.
- **Secrets pattern established:** gitignored key locally, `st.secrets` on cloud. Reused
  across all future deployments.
- **Limits to watch:** running on the Firestore free (Spark) tier — 1GB storage, daily
  read/write quotas. Fine for current scale; revisit if the library grows large or batch
  volume increases.
- **Not a vector database.** Firestore stores documents and supports equality/range
  queries, but it does not do semantic/vector search. The upcoming RAG + embeddings work
  will need a dedicated vector store (e.g. pgvector, Pinecone, or Weaviate) alongside or
  instead of Firestore. Decision deferred to that project.
- **Migration tooling:** `migrate_from_json()` and `backfill_normalized_urls()` exist in
  `firebase_library.py` for one-time data moves; safe to re-run (idempotent).

---

## Lessons (for the cumulative test)
- **Prompt anchoring:** literal example values in a JSON template become the model's
  default output. Use placeholders; place evaluation criteria before the template.
- **Session state vs persistent state:** `st.session_state` dies on refresh; only external
  stores (Firestore here) persist. Never use session state as a source of truth.
- **Cross-store invariants:** a single logical action ("this URL is handled") may require
  writes to multiple stores (library + sheet + queue). Each enforces a different invariant;
  skip one and they drift.
