# Choosing the model VVAH runs on

VVAH (the scanner) is model-agnostic. vvah-to-sigma itself uses **no LLM at all**: the converter is
deterministic code. So "bring your own model" is a scanner setting, and these profiles make it a
one-file change.

| Profile | Use when | Measured by this project |
|---|---|---|
| *(none, VVAH default)* | Best detection quality on Anthropic | Yes: PyGoat, 63 confirmed findings, $33.72 |
| `anthropic-budget.yaml` | Lower cost on Anthropic. Sonnet for high-volume stages, Opus kept for verification | Not yet |
| `openai-compatible.yaml` | Gemini (via its OpenAI-compatible API), a local model on Ollama or vLLM, or another vendor | Not yet; passes VVAH's readiness check with no Anthropic key |

**Short version: use the best model you have access to.** Security-specialized tiers, available to vetted
defenders through verified-access programs, refuse far less on exploit work (including VVAH's exploit-verification
stage) and should perform better. Any model below works.

Model choice affects how many real vulnerabilities are found and how many false positives get through.
Until a profile has been measured on the same app, treat its results as not comparable.

## How to apply a profile

VVAH deep-merges a `config.local.yaml` that sits next to the active `config.yaml`. From the folder you
run scans in:

```bash
cp "$(python -c 'import vvaharness,os;print(os.path.dirname(vvaharness.__file__))')/config/profiles/default.yaml" config.yaml
cp /path/to/vvah-to-sigma/model-profiles/anthropic-budget.yaml config.local.yaml
chmod go-w config.local.yaml
vvaharness setup
```

`setup` prints `config overlay: ... applied` and lists every stage it changed. VVAH refuses an overlay
that other users can write to, hence the `chmod`.

For `openai-compatible.yaml`, also replace `MODEL_ID` with a model your endpoint serves, and add to
`.env` (never to the YAML):

```bash
OPENAI_API_KEY=<key for that endpoint>
OPENAI_BASE_URL=<the endpoint's OpenAI-compatible base URL>
```

Run `vvaharness setup` until it reports `0 blocking issue(s)`, then scan as usual with `--stop-after s9`.
