"""Bounded T4 QLoRA experiment, synthetic data only. Run inside Colab notebook."""
import os
os.environ['WANDB_DISABLED']='true'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import json
import random
from pathlib import Path
import torch
from datasets import load_dataset
from transformers import (AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig,
                          Trainer, TrainingArguments, DataCollatorForSeq2Seq, set_seed, EarlyStoppingCallback)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

assert torch.cuda.is_available(), 'No GPU. Stop and select the free T4 runtime.'
print('GPU:',torch.cuda.get_device_name(0))
set_seed(23)
BASE='Qwen/Qwen2.5-3B-Instruct'
DATA=Path(os.environ.get('AVVAI_TRAIN_DATA','/content/avvai/data'))
OUT=Path(os.environ.get('AVVAI_TRAIN_OUTPUT','/content/avvai/output'))
OUT.mkdir(exist_ok=True)
raw=load_dataset('json',data_files={s:str(DATA/f'{s}.jsonl') for s in ('train','validation','test')})
groups={s:set(raw[s]['family']) for s in raw}
assert all(not groups[a] & groups[b] for a,b in [('train','validation'),('train','test'),('validation','test')])
assert all(row['source']=='synthetic' for split in raw for row in raw[split])
print('Rows:',{s:len(raw[s]) for s in raw})
tokenizer=AutoTokenizer.from_pretrained(BASE)
tokenizer.pad_token=tokenizer.eos_token
def encode(row):
    full=tokenizer.apply_chat_template(row['messages'],tokenize=False)
    prefix=tokenizer.apply_chat_template(row['messages'][:-1],tokenize=False,add_generation_prompt=True)
    tokens=tokenizer(full,max_length=512,truncation=True,add_special_tokens=False)
    start=len(tokenizer(prefix,add_special_tokens=False)['input_ids'])
    assert start<len(tokens['input_ids']), 'Answer truncated; increase token budget.'
    tokens['labels']=[-100]*start+tokens['input_ids'][start:]
    return tokens
encoded=raw.map(encode,remove_columns=raw['train'].column_names)
model=AutoModelForCausalLM.from_pretrained(BASE,device_map={'':0},torch_dtype=torch.float16,
    quantization_config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',
                                          bnb_4bit_compute_dtype=torch.float16,bnb_4bit_use_double_quant=True))
model=prepare_model_for_kbit_training(model)
model.config.use_cache=False
model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.05,
    target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM'))
model.print_trainable_parameters()
args=TrainingArguments(output_dir=str(OUT/'checkpoints'),num_train_epochs=2,
    per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=8,
    gradient_checkpointing=True,learning_rate=5e-5,warmup_ratio=0.1,fp16=True,optim='adamw_torch',
    logging_steps=10,save_strategy='steps',eval_strategy='steps',eval_steps=20,save_steps=20,save_total_limit=2,
    load_best_model_at_end=True,metric_for_best_model='eval_loss',greater_is_better=False,
    report_to='none',seed=23,dataloader_num_workers=0)
trainer=Trainer(model=model,args=args,train_dataset=encoded['train'],eval_dataset=encoded['validation'],
    callbacks=[EarlyStoppingCallback(early_stopping_patience=2, early_stopping_threshold=0.01)],
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer,padding=True,label_pad_token_id=-100))
print('BASELINE_EVALUATION_START')
with model.disable_adapter():
    baseline=trainer.evaluate(encoded['test'],metric_key_prefix='base_test')
(OUT/'baseline.json').write_text(json.dumps(baseline,indent=2))
print('TRAINING_START: 2 epochs, no app deployment')
train=trainer.train()
adapter=OUT/'adapter';trainer.save_model(str(adapter));tokenizer.save_pretrained(str(adapter))
print('CANDIDATE_EVALUATION_START')
candidate=trainer.evaluate(encoded['test'],metric_key_prefix='candidate_test')
metrics={'base_model':BASE,'training_rows':len(raw['train']),'validation_rows':len(raw['validation']),'test_rows':len(raw['test']),
         'selected_checkpoint':trainer.state.best_model_checkpoint,
         'selected_validation_loss':trainer.state.best_metric,
         'release':'pending_independent_review_not_deployed',
         'clinically_validated':False,'base':baseline,'candidate':candidate,'train':train.metrics,
         'note':'English synthetic policy-family holdout loss, not a clinical safety score or proof of improvement.'}
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2))
# Select up to four distinct families; split sizes can vary between experiments.
prompts=[]
seen_families=set()
for row in raw['test']:
    if row['family'] not in seen_families:
        prompts.append(row['messages'][:-1]); seen_families.add(row['family'])
    if len(prompts)==4: break
examples=[];model.eval();model.config.use_cache=True
for messages in prompts:
    inputs=tokenizer.apply_chat_template(messages,add_generation_prompt=True,return_tensors='pt').to(model.device)
    outputs={}
    for label in ('base','adapter'):
        def generate():
            with torch.inference_mode():
                result=model.generate(inputs,attention_mask=torch.ones_like(inputs),max_new_tokens=120,do_sample=False,pad_token_id=tokenizer.eos_token_id)
            return tokenizer.decode(result[0,inputs.shape[1]:],skip_special_tokens=True)
        if label=='base':
            with model.disable_adapter(): outputs[label]=generate()
        else:outputs[label]=generate()
    examples.append({'prompt':messages[-1]['content'],**outputs})
(OUT/'comparison.json').write_text(json.dumps(examples,indent=2))
import shutil
archive=shutil.make_archive('/content/avvai-lora-results','zip',OUT)
print('TRAINING_COMPLETE:',archive)
print(json.dumps(metrics,indent=2))
print('No automatic replacement of the app model. Review comparison.json before deployment.')
