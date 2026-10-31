#!/usr/bin/env python3
"""Falelo Inworld TTS-2 batch runner. Python standard library only."""
import argparse
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request
import urllib.parse

BASE='https://api.inworld.ai'
ROOT=Path(__file__).resolve().parent

def fetch(url, key=None, payload=None):
    data=None if payload is None else json.dumps(payload).encode('utf-8')
    headers={'Authorization':'Basic '+key} if key else {}
    if data is not None: headers['Content-Type']='application/json'
    request=urllib.request.Request(url,data=data,headers=headers)
    try:
        with urllib.request.urlopen(request,timeout=90) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'HTTP {error.code}: {error.read().decode("utf-8",errors="replace")[:1200]}') from error

def batches(items,limit=8000):
    group=[]; size=0
    for item in items:
        length=len(item['text'].encode('utf-16-le'))//2
        if length>limit: raise ValueError('Item too long: '+item['customId'])
        if size+length>limit and group:
            yield group
            group=[]; size=0
        group.append(item); size+=length
    if group: yield group

def select_voices(key, names, explicit):
    """Choose one stable catalog voice per character, with an explicit override."""
    catalog=[]; token=''
    while True:
        query=urllib.parse.urlencode({'pageSize':200,'pageToken':token,'filter':'source="SYSTEM" AND lang_code="en"'})
        page=json.loads(fetch(BASE+'/voices/v1/voices?'+query,key))
        catalog.extend(v for v in page.get('voices',[]) if v.get('voiceId'))
        token=page.get('nextPageToken','')
        if not token: break
    catalog=sorted({v['voiceId']:v for v in catalog}.values(),key=lambda v:v['voiceId'])
    if not catalog: raise RuntimeError('No English system voices returned by Inworld')
    preferred={
      'Adrian':'male','Alex':'neutral','Aria':'female','Asha':'female','Bea':'female',
      'Ben':'male','Elena':'female','Evan':'male','Grant':'male','Guest':'neutral',
      'Imani':'female','Ivy':'female','Jun':'neutral','Leo':'male','Mara':'female',
      'Miko':'neutral','Mila':'female','Nina':'female','Noor':'female','Omar':'male',
      'Sam':'neutral','Sol':'neutral','Tess':'female','Visitor':'neutral','Zoe':'female'}
    selected={}; used=set()
    for name in sorted(names):
        if explicit.get(name): selected[name]=explicit[name]; used.add(explicit[name]); continue
        gender=preferred.get(name,'neutral')
        candidates=[v for v in catalog if str(v.get('gender','')).lower()==gender]
        if not candidates: candidates=catalog
        choice=next((v for v in candidates if v['voiceId'] not in used),candidates[len(used)%len(candidates)])
        selected[name]=choice['voiceId']; used.add(choice['voiceId'])
    print('Voice assignment:',json.dumps(selected,ensure_ascii=False))
    (ROOT/'vozes-escolhidas.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n')
    return selected

def run():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['validate','submit','collect','generate'])
    parser.add_argument('--operation',help='Operation name returned by submit')
    parser.add_argument('--batch',type=int,help='One-based batch number; required with submit')
    parser.add_argument('--format',choices=['MP3','WAV'],default='MP3')
    args=parser.parse_args()
    items=json.loads((ROOT/'falas.json').read_text())
    voices=json.loads((ROOT/'vozes.json').read_text())
    groups=list(batches(items))
    print(f'{len(items)} lines, {len(groups)} batches; sizes: {[sum(len(i["text"].encode("utf-16-le"))//2 for i in group) for group in groups]}')
    if args.action=='validate': return
    key=os.environ.get('INWORLD_API_KEY','').strip()
    if not key: raise SystemExit('Missing INWORLD_API_KEY environment variable / GitHub Actions secret')
    if args.action in ('submit','generate'):
        voices=select_voices(key,{i['character'] for i in items},voices)
        if args.action=='submit' and (not args.batch or args.batch>len(groups) or args.batch<1): raise SystemExit('Use --batch 1..'+str(len(groups)))
        targets=[args.batch] if args.action=='submit' else list(range(1,len(groups)+1))
        operations=[]
        for index in targets:
            group=groups[index-1]
            body={'items':[{'customId':i['customId'],'request':{'text':i['text'],'voiceId':voices[i['character']], 'modelId':'inworld-tts-2','audioConfig':{'audioEncoding':args.format}, 'deliveryMode':'BALANCED'}} for i in group]}
            response=json.loads(fetch(BASE+'/tts/v1/voice:synthesizeBatch',key,body))
            name=response.get('name')
            if not name: raise RuntimeError('No operation returned: '+str(response))
            operations.append({'batch':index,'operation':name})
            (ROOT/'operacoes.json').write_text(json.dumps(operations,indent=2)+'\n')
            print(json.dumps({'operation':name,'items':len(group),'batch':index,'format':args.format}),flush=True)
            if args.action=='generate':
                deadline=time.monotonic()+4*60*60
                while True:
                    operation=json.loads(fetch(BASE+'/lro/v1alpha/'+name,key))
                    if operation.get('done'): break
                    if time.monotonic()>deadline: raise RuntimeError('Job still running; use collect with the saved operation name')
                    time.sleep(60)
                if 'error' in operation: raise RuntimeError('Batch failed: '+str(operation['error']))
                results=json.loads(fetch(operation['response']['resultsUri']))
                output=ROOT/'audios'; output.mkdir(exist_ok=True)
                failures=[]
                for entry in results['results']:
                    cue=entry['customId']
                    if cue not in {i['customId'] for i in group}: raise RuntimeError('Unknown cue '+cue)
                    if 'error' in entry: failures.append(entry); continue
                    url=entry.get('audioUri')
                    if not url: failures.append(entry); continue
                    (output/(cue+('.wav' if args.format=='WAV' else '.mp3'))).write_bytes(fetch(url))
                (output/('falhas-lote-'+str(index)+'.json')).write_text(json.dumps(failures,indent=2)+'\n')
                print('Batch',index,'finished, failures',len(failures),flush=True)
        return
    if not args.operation or not args.operation.startswith('workspaces/') or '..' in args.operation:
        raise SystemExit('Provide --operation with the name returned by submit')
    operation=json.loads(fetch(BASE+'/lro/v1alpha/'+args.operation,key))
    print('Progress:',operation.get('metadata',{}))
    if not operation.get('done'):
        print('Still running. Run collect again later using the same operation name.')
        return
    if 'error' in operation: raise RuntimeError('Batch failed: '+str(operation['error']))
    results=json.loads(fetch(operation['response']['resultsUri']))
    output=ROOT/'audios'; output.mkdir(exist_ok=True)
    by_id={i['customId']:i for i in items}
    failures=[]
    for entry in results['results']:
        cue=entry['customId']
        if cue not in by_id: raise RuntimeError('Unknown customId: '+cue)
        if 'error' in entry: failures.append({'customId':cue,'error':entry['error']}); continue
        url=entry.get('audioUri')
        if not url: failures.append({'customId':cue,'error':'Missing audioUri'}); continue
        ext='.wav' if url.lower().split('?')[0].endswith('.wav') else '.mp3'
        dest=output/(cue+ext)
        if not dest.exists(): dest.write_bytes(fetch(url))
        print('Saved',dest.name)
    (output/'falhas.json').write_text(json.dumps(failures,indent=2)+'\n')
    print('Failed items:',len(failures))

if __name__=='__main__': run()
