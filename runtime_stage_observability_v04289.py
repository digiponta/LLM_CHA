"""LLM_CHA v0.4.28.9: read-only extraction of observed stage evidence."""
import argparse, hashlib, json, math, re
from pathlib import Path

METRICS=('confidence','min_tok_conf','mean_margin','agreement','sem_agreement','qa_sim','prev_sim','agr_th','slot_cov')
TEXT_FIELDS=('gate','resolution','intent','route','reason','action')

def gate_fields(line):
    if not isinstance(line,str) or not line.startswith('[gate='):
        return {'observed':False,'metrics':{},'fields':{}}
    fields={};metrics={}
    for key in TEXT_FIELDS:
        m=re.search(r'(?<![a-zA-Z_])'+re.escape(key)+r'=([^,\]\n]*)',line)
        if m:fields[key]=m.group(1).strip()
    for key in METRICS:
        m=re.search(r'(?<![a-zA-Z_])'+re.escape(key)+r'=([^,\]\s]+)',line)
        if m:
            try:v=float(m.group(1))
            except ValueError:continue
            if math.isfinite(v):metrics[key]=v
    return {'observed':True,'metrics':metrics,'fields':fields,'source':'captured_gate_line'}

def observe(capture):
    groups=capture.get('groups') if isinstance(capture,dict) else None
    if not isinstance(groups,list) or len(groups)!=56:raise ValueError('requires 56 groups')
    rows=[];keys=set()
    for g in groups:
        ident=g.get('id');turns=g.get('turns')
        if not isinstance(ident,str) or not isinstance(turns,list):raise ValueError('invalid group')
        for i,t in enumerate(turns,1):
            key=(ident,i)
            if key in keys:raise ValueError('duplicate turn')
            keys.add(key)
            if not isinstance(t,dict) or not isinstance(t.get('question'),str):raise ValueError('invalid turn')
            answer=t.get('response')
            if answer is not None and not isinstance(answer,str):raise ValueError('invalid answer')
            rows.append({'id':ident,'turn':i,'question':t['question'],
              'final_response':answer,'process_status':g.get('status'),
              'retrieval':{'status':'NOT_OBSERVED','candidates':None},
              'generation':{'status':'NOT_OBSERVED','pre_gate_text':None},
              'truth_gate':gate_fields(t.get('gate')),
              'final_response_observed':answer is not None,
              'causal_attribution':'UNDETERMINED'})
    if len(rows)!=64:raise ValueError('requires 64 turns')
    return {'version':'v0.4.28.9','evaluation':'DEVELOPMENT_ONLY_OBSERVATIONAL',
      'runtime_instrumented':False,'causal_attribution_established':False,
      'total_turns':len(rows),
      'gate_observed':sum(r['truth_gate']['observed'] for r in rows),
      'gate_metrics_observed':sum(bool(r['truth_gate']['metrics']) for r in rows),
      'retrieval_observed':0,'pre_gate_generation_observed':0,'records':rows,
      'next_step':'Opt-in runtime instrumentation required for missing stages'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    try:
        src,dst=Path(a.capture),Path(a.output)
        if not src.is_file() or src.is_symlink():raise ValueError('invalid input')
        if dst.exists() or dst.is_symlink():raise ValueError('output exists')
        report=observe(json.loads(src.read_text(encoding='utf-8')))
        report['capture_sha256']=hashlib.sha256(src.read_bytes()).hexdigest()
        dst.parent.mkdir(parents=True,exist_ok=True)
        with dst.open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps({k:report[k] for k in ('total_turns','gate_observed','gate_metrics_observed','retrieval_observed','pre_gate_generation_observed')}))
    except (OSError,ValueError,json.JSONDecodeError) as e:p.exit(1,f'observability failed: {e}\n')
if __name__=='__main__':main()
