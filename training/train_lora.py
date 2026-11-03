"""Offline LoRA trainer. Needs original Qwen weights and a CUDA GPU, not GGUF."""
import argparse
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-model',type=Path)
    p.add_argument('--check',action='store_true')
    args=p.parse_args()
    import torch
    import importlib.util
    gpu=torch.cuda.is_available()
    packages=all(importlib.util.find_spec(x) for x in ('transformers','peft','datasets'))
    print('CUDA_GPU: '+('OK' if gpu else 'MISSING'))
    print('TRAINING_PACKAGES: '+('OK' if packages else 'MISSING'))
    if args.check:return 0
    if not gpu or not packages:
        print('WEIGHT_TRAINING: NOT STARTED; use a suitable CUDA training machine.')
        return 1
    if not args.base_model or not (args.base_model/'config.json').is_file():
        print('BASE_WEIGHTS: MISSING; provide a local Hugging Face Qwen model directory, not Ollama GGUF.')
        return 1
    from transformers import AutoTokenizer,AutoModelForCausalLM,Trainer,TrainingArguments,DataCollatorForSeq2Seq
    from peft import LoraConfig,get_peft_model
    from datasets import load_dataset
    tokenizer=AutoTokenizer.from_pretrained(str(args.base_model),local_files_only=True)
    tokenizer.pad_token=tokenizer.eos_token
    model=AutoModelForCausalLM.from_pretrained(str(args.base_model),local_files_only=True,torch_dtype=torch.float16)
    model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.05,target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM'))
    files={s:str(Path(__file__).parent/'data'/f'{s}.jsonl') for s in ('train','validation')}
    dataset=load_dataset('json',data_files=files)
    def tokenize(row):
        full=tokenizer.apply_chat_template(row['messages'],tokenize=False)
        prefix=tokenizer.apply_chat_template(row['messages'][:-1],tokenize=False,add_generation_prompt=True)
        tokens=tokenizer(full,truncation=True,max_length=512,add_special_tokens=False)
        size=len(tokenizer(prefix,add_special_tokens=False)['input_ids'])
        tokens['labels']=[-100]*min(size,len(tokens['input_ids']))+tokens['input_ids'][size:]
        return tokens
    encoded=dataset.map(tokenize,remove_columns=dataset['train'].column_names)
    output=Path(__file__).parent/'output'/'avvai-lora'
    trainer=Trainer(model=model,args=TrainingArguments(output_dir=str(output),num_train_epochs=2,
        per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=8,
        learning_rate=1e-4,fp16=True,logging_steps=10,save_strategy='epoch',eval_strategy='epoch',
        report_to='none',seed=23),train_dataset=encoded['train'],eval_dataset=encoded['validation'],
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer,padding=True,label_pad_token_id=-100))
    trainer.train();trainer.save_model(str(output));tokenizer.save_pretrained(str(output))
    print('LORA_ADAPTER: SAVED (not automatically deployed)')
    return 0

if __name__=='__main__':raise SystemExit(main())
