"""Build an allowlisted upload archive, excluding all app data and secrets."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import base64
import json
ROOT=Path(__file__).resolve().parent
def main():
    files=[ROOT/'colab_run.py',*(ROOT/'data'/f'{s}.jsonl' for s in ('train','validation','test'))]
    with ZipFile(ROOT/'avvai_colab_bundle.zip','w',ZIP_DEFLATED) as z:
        for f in files:
            z.write(f,arcname=str(f.relative_to(ROOT)))
    print('TRAINING_BUNDLE: OK (one script and three synthetic datasets only)')
    payload=base64.b64encode((ROOT/'avvai_colab_bundle.zip').read_bytes()).decode('ascii')
    code=("import base64, io, zipfile, subprocess, sys\n"
          f"encoded = '{payload}'\n"
          "with zipfile.ZipFile(io.BytesIO(base64.b64decode(encoded))) as z:\n"
          "    assert set(z.namelist()) == {'colab_run.py','data/train.jsonl','data/validation.jsonl','data/test.jsonl'}\n"
          "    z.extractall('/content/avvai')\n"
          "subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'transformers==4.57.1', 'peft==0.17.1', 'datasets==4.3.0', 'accelerate==1.11.0', 'bitsandbytes==0.48.1'])\n"
          "%run /content/avvai/colab_run.py\n"
          "from google.colab import files\nfiles.download('/content/avvai-lora-results.zip')\n")
    notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'accelerator':'GPU','kernelspec':{'name':'python3','display_name':'Python 3'}},
              'cells':[{'cell_type':'markdown','metadata':{},'source':['# Avvai T4 experiment\nSynthetic English data only. No clinical validation. No automatic deployment.\n']},
                       {'cell_type':'code','metadata':{},'source':code.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    (ROOT/'Avvai_T4_Training.ipynb').write_text(json.dumps(notebook,indent=2),encoding='utf-8')
    print('LOCAL_NOTEBOOK_BACKUP: OK')
if __name__=='__main__':main()
