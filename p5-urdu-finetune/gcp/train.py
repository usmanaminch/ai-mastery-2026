import os
import json
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    BitsAndBytesConfig,
)
from peft import LoraConfig, get_peft_model, TaskType
from trl import SFTTrainer
import torch
from google.cloud import storage

# ── Config ──────────────────────────────────────────────────────────────────
MODEL_ID     = os.environ.get("MODEL_ID", "mistralai/Mistral-7B-Instruct-v0.3")
GCS_BUCKET   = os.environ.get("GCS_BUCKET", "frontier-rag-p5-training")
OUTPUT_DIR   = os.environ.get("AIP_MODEL_DIR", "/tmp/output")
MAX_STEPS    = int(os.environ.get("MAX_STEPS", "3000"))
LORA_LAYERS  = int(os.environ.get("LORA_LAYERS", "16"))
BATCH_SIZE   = int(os.environ.get("BATCH_SIZE", "4"))
LR           = float(os.environ.get("LEARNING_RATE", "1e-4"))

# ── Pull data from GCS ───────────────────────────────────────────────────────
def download_data():
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    os.makedirs("/tmp/data", exist_ok=True)
    for split in ["train", "valid"]:
        blob = bucket.blob(f"data/{split}.jsonl")
        blob.download_to_filename(f"/tmp/data/{split}.jsonl")
        print(f"Downloaded {split}.jsonl")

def load_jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]

def format_prompt(example):
    return {"text": f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['output']}"}

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    download_data()

    train_data = Dataset.from_list([format_prompt(x) for x in load_jsonl("/tmp/data/train.jsonl")])
    eval_data  = Dataset.from_list([format_prompt(x) for x in load_jsonl("/tmp/data/valid.jsonl")])

    print(f"Train: {len(train_data)} | Eval: {len(eval_data)}")

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        quantization_config=bnb_config,
        device_map="auto",
    )

    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "v_proj"],
        layers_to_transform=list(range(LORA_LAYERS)),
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        max_steps=MAX_STEPS,
        per_device_train_batch_size=BATCH_SIZE,
        learning_rate=LR,
        bf16=True,
        logging_steps=50,
        eval_steps=500,
        save_steps=500,
        eval_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=train_data,
        eval_dataset=eval_data,
        dataset_text_field="text",
        max_seq_length=512,
    )

    trainer.train()
    trainer.save_model(OUTPUT_DIR)
    print(f"Model saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
