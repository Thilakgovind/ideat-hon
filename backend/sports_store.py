"""Public sports reference data. Private tables never fall back to public samples."""
import httpx
from . import config
from .seed.sports_sample import PUBLIC_TABLES, generate

def read(table):
    if table not in PUBLIC_TABLES:
        raise ValueError('Not a public sports table')
    if config.has('supabase'):
        key=config.env('SUPABASE_SERVICE_KEY')
        try:
            r=httpx.get(config.env('SUPABASE_URL').rstrip('/')+'/rest/v1/'+table,
                headers={'apikey':key,'Authorization':f'Bearer {key}'},params={'select':'*','order':'id','limit':1000},timeout=5)
            r.raise_for_status()
            rows=r.json()
            if isinstance(rows,list) and rows:
                return rows,'supabase'
        except (httpx.HTTPError,ValueError):
            pass
    return generate()[table],'sample_fallback'
