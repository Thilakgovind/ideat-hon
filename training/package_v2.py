"""Package the V2 development experiment and automatic post-run regression review."""
import base64
import io
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from .build_v2 import main as build

ROOT = Path(__file__).parent

def main():
    build()
    stream=io.BytesIO()
    with ZipFile(stream,'w',ZIP_DEFLATED) as z:
        z.writestr('colab_run.py',(ROOT/'colab_run.py').read_text(encoding='utf-8-sig'))
        z.writestr('colab_code_red.py',(ROOT/'colab_code_red.py').read_text(encoding='utf-8-sig'))
        for split in ('train','validation','test'):
            z.writestr(f'data/{split}.jsonl',(ROOT/'data_v2'/f'{split}.jsonl').read_bytes())
    payload=base64.b64encode(stream.getvalue()).decode()
    code=("import base64, io, zipfile, subprocess, sys, os\n"
          f"payload='{payload}'\n"
          "with zipfile.ZipFile(io.BytesIO(base64.b64decode(payload))) as z:\n"
          "    assert set(z.namelist()) == {'colab_run.py','colab_code_red.py','data/train.jsonl','data/validation.jsonl','data/test.jsonl'}\n"
          "    z.extractall('/content/avvai_v2_bundle')\n"
          "subprocess.check_call([sys.executable,'-m','pip','install','-q','transformers==4.57.1','peft==0.17.1','datasets==4.3.0','accelerate==1.11.0','bitsandbytes==0.48.1'])\n"
          "os.environ['AVVAI_TRAIN_DATA']='/content/avvai_v2_bundle/data'\n"
          "os.environ['AVVAI_TRAIN_OUTPUT']='/content/avvai_v2_output'\n"
          "%run /content/avvai_v2_bundle/colab_run.py\n"
          "%run -i /content/avvai_v2_bundle/colab_code_red.py\n"
          "from google.colab import files\n"
          "files.download('/content/avvai-lora-results.zip')\n"
          "files.download('/content/avvai-code-red.zip')\n")
    nb={'nbformat':4,'nbformat_minor':5,'metadata':{'accelerator':'GPU','kernelspec':{'name':'python3','display_name':'Python 3'}},'cells':[
        {'cell_type':'markdown','metadata':{},'source':['# Avvai V2 development experiment\nRun on a fresh free T4 runtime. Synthetic, unreviewed data; English answers. Includes automatic Code Red comparison. No automatic deployment.\n']},
        {'cell_type':'code','metadata':{},'source':code.splitlines(keepends=True),'outputs':[],'execution_count':None}]}
    dest=ROOT/'Avvai_V2_Training_And_Review.ipynb'
    dest.write_text(json.dumps(nb,ensure_ascii=False,indent=2),encoding='utf-8')
    print('V2_NOTEBOOK:',dest)

if __name__=='__main__':main()
