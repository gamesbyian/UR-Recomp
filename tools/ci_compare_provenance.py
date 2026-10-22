"""Strict read-only source-bound GitHub compare admission, no CI gate awards."""
import re
SHA=re.compile('[0-9a-f]{40}\\Z')

def assess(*, main_sha, pr_head_sha, compare):
    if (any(type(s) is not str or SHA.fullmatch(s) is None for s in (main_sha,pr_head_sha))
            or type(compare) is not dict):
        raise ValueError('invalid source epoch')
    expected={'base','head','base_commit','merge_base_commit','status','ahead_by','behind_by','total_commits','too_large','files'}
    if not expected <= set(compare):raise ValueError('missing compare provenance')
    if compare['base']!=main_sha or compare['head']!=pr_head_sha:
        raise ValueError('compare query not bound to current main and PR head')
    base=compare['base_commit']; merge=compare['merge_base_commit']
    if (type(base) is not dict or type(merge) is not dict or
            base.get('sha')!=main_sha or
            type(merge.get('sha')) is not str or SHA.fullmatch(merge['sha']) is None):
        raise ValueError('compare response does not bind current main')
    ahead=compare['ahead_by'];behind=compare['behind_by'];status=compare['status']
    if (type(ahead) is not int or type(behind) is not int or min(ahead,behind)<0 or
            type(compare['total_commits']) is not int or compare['total_commits']<0 or
            type(compare['too_large']) not in (bool,type(None))):
        raise ValueError('invalid compare counters')
    derived=('identical' if ahead==behind==0 else
             'ahead' if ahead>0 and behind==0 else
             'behind' if ahead==0 and behind>0 else 'diverged')
    if status!=derived or (behind==0 and merge['sha']!=main_sha) or (ahead==0 and merge['sha']==main_sha and behind>0):
        raise ValueError('compare ancestry/status contradiction')
    if type(compare['files']) is not list or len(compare['files'])>300:
        raise ValueError('missing/truncated changed-file census')
    names=[]
    for f in compare['files']:
        if type(f) is not dict or type(f.get('filename')) is not str or not f['filename']:
            raise ValueError('invalid changed-file census')
        names.append(f['filename'])
    if len(names)!=len(set(names)):
        raise ValueError('duplicate changed file')
    return {'schema':'ur-pr-compare-epoch/1','main':main_sha,'head':pr_head_sha,
            'merge_base':merge['sha'],'ahead':ahead,'behind':behind,
            'changed_files':names,'main_merge_tree_qualified':False,
            'decision':'HOLD_NO_DIFF' if ahead==0 else 'HOLD_MERGE_TREE_UNTESTED',
            'independent_windows_qa_accepted':False,'release_gate_credit':0}
