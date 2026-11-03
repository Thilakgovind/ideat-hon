"""Create credential-free n8n imports for sports guidance and opted-in emails."""
import json
from . import config

def build():
    folder = config.ROOT / 'n8n'
    path = folder / 'veeramangai_avvai.json'
    flow = json.loads(path.read_text(encoding='utf-8'))
    incoming = next(n for n in flow['nodes'] if n['name'] == 'Incoming')
    incoming['parameters']['authentication'] = 'none'
    # Public read-only guide; never accepts identity, private records or actions.
    clean = next(n for n in flow['nodes'] if n['name'] == 'Minimize input')
    clean['parameters']['jsCode'] = """const body = $input.first().json.body || {};
const prompts = {opportunities: 'Find a trial', funding: 'Help with entry fees', travel: 'Plan travel', support: 'Ask for rest'};
if (!Object.hasOwn(prompts, body.topic) || !['ta','en'].includes(body.lang)) throw new Error('Invalid topic or language');
return [{json: {text: prompts[body.topic], lang: body.lang}}];"""
    next(n for n in flow['nodes'] if n['name'] == 'Avvai backend')['parameters']['url'] = config.env('PUBLIC_BACKEND_URL').rstrip('/') + '/api/veeramangai/chat'
    path.write_text(json.dumps(flow,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('AVVAI_WORKFLOW: OK')
    base = config.env('PUBLIC_BACKEND_URL').rstrip('/')
    def node(id, name, kind, version, x, parameters, **extra):
        return dict(id=id,name=name,type='n8n-nodes-base.'+kind,typeVersion=version,position=[x,0],parameters=parameters,**extra)
    worker_auth = {'authentication':'genericCredentialType','genericAuthType':'httpHeaderAuth'}
    nodes = [
        node('manual','Process pending updates','manualTrigger',1,0,{}),
        node('claim','Claim pending deliveries','httpRequest',4.2,240,{
            **worker_auth,'method':'POST','url':base+'/api/veeramangai/automation/claim',
            'sendBody':True,'specifyBody':'json','jsonBody':'{}','options':{'timeout':20000}}),
        node('split','Each delivery','splitOut',1,480,{'fieldToSplitOut':'deliveries','options':{}}),
        node('gmail','Send generic update','gmail',2.1,720,{
            'resource':'message','operation':'send','sendTo':'={{ $json.to }}',
            'subject':'={{ $json.subject }}','emailType':'text','message':'={{ $json.message }}',
            'options':{}},onError='continueRegularOutput',retryOnFail=False),
        node('receipt','Record provider result','httpRequest',4.2,960,{
            **worker_auth,'method':'POST','url':base+'/api/veeramangai/automation/receipt',
            'sendBody':True,'specifyBody':'json',
            'jsonBody':"={{ JSON.stringify({delivery_id: $('Each delivery').item.json.delivery_id, claim_id: $('Each delivery').item.json.claim_id, status: $json.id && !$json.error ? 'sent' : 'uncertain', provider_id: $json.id && !$json.error ? $json.id : null}) }}",
            'options':{'timeout':20000}}),
    ]
    connections = {nodes[i]['name']:{'main':[[{'node':nodes[i+1]['name'],'type':'main','index':0}]]} for i in range(len(nodes)-1)}
    notification = {'name':'Veeramangai — Opted-in Request Updates','active':False,'nodes':nodes,
                    'connections':connections,'settings':{'executionOrder':'v1','saveDataSuccessExecution':'none',
                    'saveDataErrorExecution':'none','saveManualExecutions':False},'pinData':{}}
    (folder/'veeramangai_notifications.json').write_text(json.dumps(notification,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('NOTIFICATION_WORKFLOW: OK (credential bindings required)')

if __name__ == '__main__':
    build()
