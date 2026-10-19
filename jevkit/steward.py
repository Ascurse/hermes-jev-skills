"""Checked installer/report adapter. Authority and execution callbacks remain caller-owned."""
import json
import os
import subprocess
from pathlib import Path
from . import provenance


def _read(path):
    try:
        return json.loads(path.read_text())
    except (OSError,ValueError):
        return None


def usage_totals(homes, since):
    """Aggregate common-ledger numeric metadata only; never expose custom labels/actions."""
    import math
    from . import ledger
    features={'video_qa','video_qa_trial','video_qa_ab','image_action','blender_advice',
              'gate','memory','search','vision','screen','routing','skills','decide','mail','compact'}
    homes=list(homes)
    rows=[];files=0;unavailable=0
    for home in homes:
        path=Path(home)/'logs/jev-ledger.jsonl'
        if not path.exists():continue
        try:
            if path.stat().st_size>32*1024*1024:
                unavailable+=1;continue
            selected=ledger.read(path,since=since,strict=True);files+=1
        except (OSError,ValueError):
            unavailable+=1;continue
        for record in selected:
            item={'ts':record.get('ts',0),
                  'feature':record.get('feature') if isinstance(record.get('feature'),str) and record.get('feature') in features else 'other',
                  'status':record.get('status') if record.get('status') in ('ok','error','skipped','code','unknown') else 'unknown',
                  'shadow':record.get('shadow') is True}
            for key in ('cost_usd','list_usd','input_tokens','latency_ms','llm_avoided_est'):
                value=record.get(key)
                item[key]=value if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and value>=0 else None
            rows.append(item)
    result=ledger.summarize(rows,by_day=False)
    if unavailable:
        result["totals"].update(estimated_cost_complete=False,estimated_cost_usd=None)
    return {**result,'homes_checked':len(homes),'ledger_files':files,'unavailable_files':unavailable,
            'scope':'Common-ledger numeric metadata only; historical direct calls may be absent'}


def describe_install(state):
    p=state.get('provenance')
    if isinstance(p,dict):
        return provenance.describe(p)
    return 'unverified source/install identity; no main-match claim'


def install_state(sha,ci,tests,*,repo,home,switches,git,run,dry=False):
    """Never downgrade a feature tree or install from unverified/dirty source."""
    repo=Path(repo); home=Path(home); switches=Path(switches)
    def inspect():
        return provenance.check_install(repo,home,sha)
    try:
        p=inspect()
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as exc:
        return dict(in_sync=False,main_match=False,action='not refreshed: provenance unavailable ('+type(exc).__name__+')')
    state=dict(in_sync=p['installed_matches_checkout'],main_match=p['matches_main'],provenance=p)
    state['external_dependencies']={}
    for name in ('vibe-editing','blender-warm-session'):
        try:
            state['external_dependencies'][name]=provenance.external_skill(home/'skills'/name)
        except (OSError,ValueError) as exc:
            state['external_dependencies'][name]={'status':'unavailable','error':type(exc).__name__}
    if not p['checkout_at_main'] or p['checkout_dirty']:
        state['action']='not refreshed: checkout is not clean published main; preserve installed candidate'
        return state
    if p['matches_main']:
        return state
    if (switches/'NO_AUTO_INSTALL').exists():
        state['action']='not refreshed: NO_AUTO_INSTALL is set'
        return state
    if ci.get('status')!='success' or tests.get('status')!='green':
        state['action']='not refreshed: exact main is not green on GitHub and locally'
        return state
    if dry:
        state['action']='would refresh (dry run)'
        return state
    before=_read(home/'jev/state.json')
    rc,out,err=run(['/usr/bin/python3','install.py','--enable','none'],cwd=repo,timeout=300,
                   env={**os.environ,'HERMES_HOME':str(home)})
    try:
        p=inspect()
        state.update(in_sync=p['installed_matches_checkout'],main_match=p['matches_main'],provenance=p)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):
        state.update(in_sync=False,main_match=False)
        state.pop('provenance',None)
    state.update(action=('refreshed' if rc==0 and state['main_match'] else 'install not verified'),
                 switches_unchanged=before==_read(home/'jev/state.json'),
                 note='Installed source is distinct from code already loaded by running processes; no restart performed')
    return state
