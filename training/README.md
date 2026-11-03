# Avvai support training and evaluation

Status: a QLoRA adapter was trained on a free Colab Tesla T4 on 2026-11-03.
**The candidate failed a manual safety spot-check and is NOT deployed.**
The laptop has 16 GB RAM, Intel
integrated graphics, no CUDA GPU, and lacks peft/datasets. Its existing Ollama
Q4 GGUF is an inference model, not the base-weight directory the trainer needs.

## Completed Colab experiment

Qwen/Qwen2.5-3B-Instruct, NF4 4-bit, LoRA rank 8 on q_proj/v_proj,
1,843,200 trainable parameters. Two epochs completed (170 optimizer steps;
807.8 seconds training time). Checkpoint 85 was selected by minimum validation
loss (2.7788); the second epoch overfit (validation loss 3.2514).
Held-out synthetic reference loss: base 6.0378, selected adapter 4.2746.
This measures reference-answer fit, not clinical safety or overall usefulness.

The archive is saved at `training/output/avvai-best-adapter.zip`, extracted to
`training/output/selected_adapter/`. SHA256:
`885dfc89c0b20ee9240517d69d0bc5d2c5662b6f3a27b60bd26b9ce9cb49410e`.
Raw metrics and four prompt comparisons are inside the extracted folder.

**Release decision: reject this candidate for deployment.** A missed-period
answer misleadingly dismissed its significance; the opportunities answer also
did not use the application's actual database tools. Lower loss did not prevent
these failures. Correct and independently review examples, expand adversarial
and Tamil/Tanglish evaluation, and verify tool use before another release review.
The original Ollama model and existing application guardrails remain in use.

`Avvai_T4_Training.ipynb` is a local self-contained notebook backup; regenerate
with `python -m training.package_colab`. The original shared notebook could not
be copied to Drive because its storage quota was exceeded. Adapter files under
`training/output/` are ignored by git. No private athlete data or credentials
were uploaded.

## Data

Run `python -m training.generate_cases` from the project root.
The outputs contain 1,000 English synthetic contextual variations from **25
policy families**, not 1,000 independently researched medical cases:
680 training, 160 validation, 160 test. Families never cross splits.
All rows have source=synthetic and clinically_reviewed=false. No real athlete
data, health histories, credentials, names or phone numbers are included.
Tamil and Tanglish training/evaluation examples have not been produced yet.

The generated policy answers are starting material for review. They are not
diagnosis, clinical validation, return-to-play clearance or treatment protocols.
Do not use the 1,026 fictional sports rows as facts about real competitions.

## Evidence boundaries

- https://www.ausport.gov.au/clearinghouse/evidence/women-in-sport/factors/menstrual-cycle
- https://www.acog.org/womens-health/faqs/the-healthy-female-athlete
- https://bjsm.bmj.com/content/57/17/1073

Calendar phase does not determine individual hormone levels or justify a fixed
training prescription. Symptoms and preferences differ. Persistent menstrual
changes, fatigue or bone stress concerns warrant qualified assessment. The app
does not diagnose REDs, anaemia, PCOS or endometriosis, prescribe medicines,
recommend restrictive eating, or share health reasons automatically.

## Runtime behavior

`backend/athlete_support.py` contains deterministic responses for supported
phrases. These guard selected health/safety/privacy requests before model
generation and return immediate guidance, a next-step option and a privacy
statement. They do not save health histories or submit requests. They are a
limited phrase-based safety layer, not a complete medical triage system. Unknown
phrasing and multilingual coverage still need evaluation; a passing unit test
does not establish clinical safety or general Qwen quality.

## Fine-tuning on a suitable training machine

Use a CUDA environment with compatible torch, transformers, peft and datasets,
and original locally downloaded Qwen2.5-3B-Instruct Hugging Face weights.
The runner does not download weights or submit a paid GPU job automatically.

```powershell
python -m training.train_lora --check
python -m training.train_lora --base-model C:\models\Qwen2.5-3B-Instruct
```

The runner trains a small LoRA adapter for two epochs with assistant-only loss,
evaluates on held-out families and saves under ignored `training/output/`.
That is a bounded initial experiment, not a proven optimal hyperparameter setup.
Benchmark the base model and candidate on held-out scenarios, prompt injection,
PII leakage, uncertain inputs and Tamil/Tanglish before deployment. Test invalid
tool arguments, unauthorized requests and duplicate submissions separately.
Expert review and real user usability work remain needed. The script does not
automatically deploy an adapter or claim that training improved the model.
