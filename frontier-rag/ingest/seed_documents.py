"""
ingest/seed_documents.py — Comprehensive frontier AI corpus

Covers all major LLM developers:
- Western: Anthropic, OpenAI, Google DeepMind, Meta, Microsoft, Amazon, Mistral, xAI, Cohere
- Chinese: DeepSeek, Alibaba Qwen, Baidu, 01.AI, Zhipu AI
- Safety orgs: METR, Apollo Research, UK AISI, NIST

Run: python3 ingest/seed_documents.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.pipeline import ingest_batch

SEED_DOCUMENTS = [

    # ═══════════════════════════════════════════════════
    # ANTHROPIC
    # ═══════════════════════════════════════════════════
    {
        "url": "https://www.anthropic.com/research/claude-character",
        "source_type": "model_card",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"model": "Claude", "topic": "character and values"},
    },
    {
        "url": "https://www.anthropic.com/news/core-views-on-ai-safety",
        "source_type": "safety_eval",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"topic": "AI safety philosophy"},
    },
    {
        "url": "https://www.anthropic.com/research/building-effective-agents",
        "source_type": "blog",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"topic": "agentic AI architecture"},
    },
    {
        "url": "https://www.anthropic.com/research/alignment-faking",
        "source_type": "safety_eval",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"topic": "alignment faking research"},
    },
    {
        "url": "https://www.anthropic.com/responsible-scaling-policy",
        "source_type": "safety_eval",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"topic": "responsible scaling policy"},
    },
    {
        "url": "https://claude.com/blog/zero-trust-for-ai-agents",
        "source_type": "zt_framework",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"topic": "zero trust for AI agents"},
    },
    {
        "url": "https://www.anthropic.com/news/model-card-claude-3",
        "source_type": "model_card",
        "entity_name": "Anthropic",
        "entity_type": "company",
        "metadata": {"model": "Claude 3", "topic": "model card"},
    },

    # ═══════════════════════════════════════════════════
    # OPENAI
    # ═══════════════════════════════════════════════════
    {
        "url": "https://openai.com/index/openai-safety-update",
        "source_type": "safety_eval",
        "entity_name": "OpenAI",
        "entity_type": "company",
        "metadata": {"topic": "safety update"},
    },
    {
        "url": "https://openai.com/index/practices-for-governing-agentic-ai-systems",
        "source_type": "blog",
        "entity_name": "OpenAI",
        "entity_type": "company",
        "metadata": {"topic": "agentic AI governance"},
    },
    {
        "url": "https://openai.com/index/hello-gpt-4o",
        "source_type": "model_card",
        "entity_name": "OpenAI",
        "entity_type": "company",
        "metadata": {"model": "GPT-4o", "topic": "model announcement"},
    },
    {
        "url": "https://openai.com/safety",
        "source_type": "safety_eval",
        "entity_name": "OpenAI",
        "entity_type": "company",
        "metadata": {"topic": "safety overview"},
    },
    {
        "url": "https://openai.com/index/openai-preparedness-framework-beta",
        "source_type": "safety_eval",
        "entity_name": "OpenAI",
        "entity_type": "company",
        "metadata": {"topic": "preparedness framework"},
    },
    {
        "url": "https://openai.com/index/introducing-o1",
        "source_type": "model_card",
        "entity_name": "OpenAI",
        "entity_type": "company",
        "metadata": {"model": "o1", "topic": "reasoning model"},
    },

    # ═══════════════════════════════════════════════════
    # GOOGLE DEEPMIND
    # ═══════════════════════════════════════════════════
    {
        "url": "https://deepmind.google/technologies/gemini/",
        "source_type": "model_card",
        "entity_name": "Google DeepMind",
        "entity_type": "company",
        "metadata": {"model": "Gemini", "topic": "model overview"},
    },
    {
        "url": "https://deepmind.google/responsibility-safety/",
        "source_type": "safety_eval",
        "entity_name": "Google DeepMind",
        "entity_type": "company",
        "metadata": {"topic": "safety and responsibility"},
    },
    {
        "url": "https://blog.google/technology/ai/google-gemini-ai/",
        "source_type": "model_card",
        "entity_name": "Google DeepMind",
        "entity_type": "company",
        "metadata": {"model": "Gemini", "topic": "announcement"},
    },
    {
        "url": "https://deepmind.google/discover/blog/gemini-a-family-of-highly-capable-multimodal-models/",
        "source_type": "model_card",
        "entity_name": "Google DeepMind",
        "entity_type": "company",
        "metadata": {"model": "Gemini", "topic": "technical overview"},
    },

    # ═══════════════════════════════════════════════════
    # META AI
    # ═══════════════════════════════════════════════════
    {
        "url": "https://ai.meta.com/llama/",
        "source_type": "model_card",
        "entity_name": "Meta AI",
        "entity_type": "company",
        "metadata": {"model": "Llama", "topic": "model overview"},
    },
    {
        "url": "https://ai.meta.com/blog/meta-llama-3/",
        "source_type": "model_card",
        "entity_name": "Meta AI",
        "entity_type": "company",
        "metadata": {"model": "Llama 3", "topic": "model announcement"},
    },
    {
        "url": "https://ai.meta.com/responsibility/",
        "source_type": "safety_eval",
        "entity_name": "Meta AI",
        "entity_type": "company",
        "metadata": {"topic": "responsible AI"},
    },
    {
        "url": "https://llama.meta.com/responsible-use-guide/",
        "source_type": "safety_eval",
        "entity_name": "Meta AI",
        "entity_type": "company",
        "metadata": {"topic": "Llama responsible use guide"},
    },

    # ═══════════════════════════════════════════════════
    # MICROSOFT
    # ═══════════════════════════════════════════════════
    {
        "url": "https://azure.microsoft.com/en-us/products/ai-studio/",
        "source_type": "model_card",
        "entity_name": "Microsoft",
        "entity_type": "company",
        "metadata": {"topic": "Azure AI Studio"},
    },
    {
        "url": "https://www.microsoft.com/en-us/ai/responsible-ai",
        "source_type": "safety_eval",
        "entity_name": "Microsoft",
        "entity_type": "company",
        "metadata": {"topic": "responsible AI framework"},
    },
    {
        "url": "https://blogs.microsoft.com/ai/introducing-phi-4-microsoft-latest-small-language-model/",
        "source_type": "model_card",
        "entity_name": "Microsoft",
        "entity_type": "company",
        "metadata": {"model": "Phi-4", "topic": "small language model"},
    },

    # ═══════════════════════════════════════════════════
    # AMAZON / AWS
    # ═══════════════════════════════════════════════════
    {
        "url": "https://aws.amazon.com/bedrock/",
        "source_type": "model_card",
        "entity_name": "Amazon",
        "entity_type": "company",
        "metadata": {"topic": "AWS Bedrock platform"},
    },
    {
        "url": "https://aws.amazon.com/ai/responsible-ai/",
        "source_type": "safety_eval",
        "entity_name": "Amazon",
        "entity_type": "company",
        "metadata": {"topic": "responsible AI"},
    },
    {
        "url": "https://www.amazon.science/blog/amazon-nova-models",
        "source_type": "model_card",
        "entity_name": "Amazon",
        "entity_type": "company",
        "metadata": {"model": "Amazon Nova", "topic": "model announcement"},
    },

    # ═══════════════════════════════════════════════════
    # MISTRAL AI
    # ═══════════════════════════════════════════════════
    {
        "url": "https://mistral.ai/news/",
        "source_type": "blog",
        "entity_name": "Mistral AI",
        "entity_type": "company",
        "metadata": {"topic": "latest news and releases"},
    },
    {
        "url": "https://mistral.ai/news/mistral-large-2407/",
        "source_type": "model_card",
        "entity_name": "Mistral AI",
        "entity_type": "company",
        "metadata": {"model": "Mistral Large 2", "topic": "model announcement"},
    },
    {
        "url": "https://mistral.ai/technology/",
        "source_type": "model_card",
        "entity_name": "Mistral AI",
        "entity_type": "company",
        "metadata": {"topic": "technology overview"},
    },

    # ═══════════════════════════════════════════════════
    # xAI (GROK)
    # ═══════════════════════════════════════════════════
    {
        "url": "https://x.ai/blog/grok-2",
        "source_type": "model_card",
        "entity_name": "xAI",
        "entity_type": "company",
        "metadata": {"model": "Grok 2", "topic": "model announcement"},
    },
    {
        "url": "https://x.ai/blog",
        "source_type": "blog",
        "entity_name": "xAI",
        "entity_type": "company",
        "metadata": {"topic": "xAI research blog"},
    },

    # ═══════════════════════════════════════════════════
    # COHERE
    # ═══════════════════════════════════════════════════
    {
        "url": "https://cohere.com/blog/command-r",
        "source_type": "model_card",
        "entity_name": "Cohere",
        "entity_type": "company",
        "metadata": {"model": "Command R", "topic": "enterprise model"},
    },
    {
        "url": "https://cohere.com/security",
        "source_type": "safety_eval",
        "entity_name": "Cohere",
        "entity_type": "company",
        "metadata": {"topic": "security and privacy"},
    },

    # ═══════════════════════════════════════════════════
    # DEEPSEEK (China)
    # ═══════════════════════════════════════════════════
    {
        "url": "https://www.deepseek.com/",
        "source_type": "model_card",
        "entity_name": "DeepSeek",
        "entity_type": "company",
        "metadata": {"country": "China", "topic": "model overview"},
    },
    {
        "url": "https://api-docs.deepseek.com/",
        "source_type": "model_card",
        "entity_name": "DeepSeek",
        "entity_type": "company",
        "metadata": {"country": "China", "topic": "API documentation"},
    },

    # ═══════════════════════════════════════════════════
    # ALIBABA QWEN (China)
    # ═══════════════════════════════════════════════════
    {
        "url": "https://qwenlm.github.io/blog/qwen2.5/",
        "source_type": "model_card",
        "entity_name": "Alibaba",
        "entity_type": "company",
        "metadata": {"model": "Qwen 2.5", "country": "China", "topic": "model release"},
    },

    # ═══════════════════════════════════════════════════
    # 01.AI / Yi (China)
    # ═══════════════════════════════════════════════════
    {
        "url": "https://01.ai/",
        "source_type": "model_card",
        "entity_name": "01.AI",
        "entity_type": "company",
        "metadata": {"model": "Yi", "country": "China", "topic": "model overview"},
    },

    # ═══════════════════════════════════════════════════
    # SAFETY ORGANIZATIONS
    # ═══════════════════════════════════════════════════
    {
        "url": "https://metr.org/blog/2023-03-18-update-on-our-work-on-dangerous-capabilities-evaluations/",
        "source_type": "safety_eval",
        "entity_name": "METR",
        "entity_type": "evaluation",
        "metadata": {"topic": "dangerous capabilities evaluation"},
    },
    {
        "url": "https://www.apolloresearch.ai/blog",
        "source_type": "safety_eval",
        "entity_name": "Apollo Research",
        "entity_type": "evaluation",
        "metadata": {"topic": "AI safety research"},
    },
    {
        "url": "https://www.aisi.gov.uk/work",
        "source_type": "regulatory",
        "entity_name": "UK AI Safety Institute",
        "entity_type": "regulation",
        "metadata": {"country": "UK", "topic": "AI safety evaluations"},
    },

    # ═══════════════════════════════════════════════════
    # REGULATORY
    # ═══════════════════════════════════════════════════
    {
        "url": "https://www.nist.gov/artificial-intelligence/ai-risk-management-framework",
        "source_type": "regulatory",
        "entity_name": "NIST",
        "entity_type": "regulation",
        "metadata": {"topic": "AI Risk Management Framework"},
    },
    {
        "url": "https://www.cisa.gov/ai",
        "source_type": "regulatory",
        "entity_name": "CISA",
        "entity_type": "regulation",
        "metadata": {"topic": "AI security guidance"},
    },
]

if __name__ == "__main__":
    print(f"Ingesting {len(SEED_DOCUMENTS)} documents across all major AI labs...\n")
    results = ingest_batch(SEED_DOCUMENTS)

    print("\n── Summary ──")
    by_entity = {}
    for r in results:
        # Find matching doc
        doc = next((d for d in SEED_DOCUMENTS if d["url"] == r["url"]), {})
        entity = doc.get("entity_name", "Unknown")
        if entity not in by_entity:
            by_entity[entity] = {"success": 0, "skipped": 0, "error": 0}
        by_entity[entity][r["status"]] += 1

    for entity, counts in sorted(by_entity.items()):
        parts = []
        if counts["success"]: parts.append(f"✅ {counts['success']}")
        if counts["skipped"]: parts.append(f"⏭️  {counts['skipped']}")
        if counts["error"]:   parts.append(f"❌ {counts['error']}")
        print(f"  {entity:<25} {' '.join(parts)}")
