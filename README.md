# AI Mastery 2026 — Usman Chaudhary

> Field CISO & AI Builder · [usmanc.com](https://usmanc.com)

Working AI systems built end-to-end. Each one starts with a problem enterprises
actually have and a constraint they actually face — enterprise OAuth boundaries,
regulated-data retrieval, sovereign deployment, zero network egress — designed,
built, and shipped, with honest write-ups of what worked and what didn't.

## Projects

| # | Project | What it is | Status | Links |
|---|---------|-----------|--------|-------|
| P1 | **Chief of Staff Agent** | Executive workflow automation under enterprise OAuth constraints — reads Gmail + Calendar, prioritizes the day, triages the inbox | ✅ Live | [Summary](https://usmanc.com/chief-of-staff.html) · [App](https://usman-chief-of-staff-demo.streamlit.app) |
| P2 | **Content Engine** | Editorial intelligence pipeline with human-in-the-loop publishing | ✅ Done | [Summary](https://usmanc.com/content-engine.html) |
| P3 | **Frontier AI Intelligence RAG** | Source-grounded AI assistant for a regulated SOC — hybrid BM25 + vector retrieval, every answer cites its sources | ✅ Live | [Summary](https://usmanc.com/frontier-rag.html) · [App](https://usman-frontier-rag.streamlit.app) |
| P4 | **UrduGPT — LLM from scratch** | Character-level transformer built and inspected by hand; an interpretability case study on a low-resource language | ✅ Done | [Summary](https://usmanc.com/urdu-gpt.html) |
| P5 | **Urdu Fine-tuning Pipeline** | End-to-end fine-tuning infrastructure: local MLX prototype → containerized GCP / Vertex AI production pipeline | ✅ Done | [Summary](https://usmanc.com/urdu-finetune.html) |
| P6 | **EdgePatch — Air-Gapped Patch Evaluation** | Offline, deterministic gate for AI-generated C patches in disconnected environments | ✅ v1 done | [Write-up](https://usmanc.com/edgepatch.html) · [Code](./p6-edgepatch) |
| P7 | **Open Source + Publication** | OSS release, benchmark results against real CVEs, published write-ups | 🔜 Next | |

## P6 — EdgePatch (current)

EdgePatch evaluates LLM-generated C vulnerability patches **offline**, before they go
into production. A model proposes a fix — from a local model, a secure enclave, or a
signed upstream pack — and deterministic tooling decides whether to trust it:
structural scoring, behavioral evidence, and a verdict packaged for a human to
approve. **The patch is generative; the verification is deterministic.**

Built for ICS, critical infrastructure, and regulated environments the cloud can't
reach. It does **not** ship exploit material or reproduction recipes, rewrite C into
Rust, or patch anything autonomously.

v1 ships a provenance-gated benchmark across four real C libraries (zlib, libpng,
expat, libxml2) and a CLI that reproduces it from a clean clone — no model, no Docker,
no internet, no upstream checkout, no pip install:

```bash
git clone https://github.com/usmanaminch/ai-mastery-2026.git
cd ai-mastery-2026/p6-edgepatch
python3 -m edgepatch bench
```

Full write-up: **[usmanc.com/edgepatch.html](https://usmanc.com/edgepatch.html)**

## Connect

[usmanc.com](https://usmanc.com) · [LinkedIn](https://linkedin.com/in/usmanchaudhary) · [GitHub](https://github.com/usmanaminch)
