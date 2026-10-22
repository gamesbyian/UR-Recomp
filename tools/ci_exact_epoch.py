"""Read-only PR CI epoch classifier, never an acceptance or merge decision."""
import re

NAMES = frozenset({'Repository hygiene','Project tooling unit tests',
                   'Baldosa native Windows x64 bridge feasibility'})
SHA = re.compile(r'[0-9a-f]{40}\Z')

def classify(main_sha, merge_base_sha, pr_head_sha, pr_number, ahead, behind, runs):
    if any(type(x) is not str or not SHA.fullmatch(x)
           for x in (main_sha,merge_base_sha,pr_head_sha)):
        raise ValueError('missing exact source identity')
    if type(pr_number) is not int or pr_number < 1:
        raise ValueError('invalid PR identity')
    if any(type(x) is not int or x < 0 for x in (ahead,behind)) or ahead == 0:
        raise ValueError('invalid diff count or no proposed changes')
    if type(runs) is not list or len(runs) != len(NAMES):
        raise ValueError('missing or excessive workflow receipts')
    seen_names,seen_ids=set(),set()
    for run in runs:
        if type(run) is not dict or set(run) != {'id','name','event','status','conclusion',
                                                'head_sha','pr_number','run_attempt','base_sha'}:
            raise ValueError('incomplete workflow identity')
        if (type(run['id']) is not int or run['id'] <= 0 or run['id'] in seen_ids or
            type(run['run_attempt']) is not int or run['run_attempt'] < 1 or
            type(run['name']) is not str or run['name'] not in NAMES or
            run['name'] in seen_names or run['event'] != 'pull_request' or
            run['status'] != 'completed' or run['conclusion'] != 'success' or
            run['head_sha'] != pr_head_sha or
            type(run['pr_number']) is not int or run['pr_number'] != pr_number or
            type(run['base_sha']) is not str or not SHA.fullmatch(run['base_sha'])):
            raise ValueError('workflow is not uniquely associated with exact PR head')
        seen_ids.add(run['id']);seen_names.add(run['name'])
    bases={r['base_sha'] for r in runs}
    if len(bases)!=1:
        raise ValueError('inconsistent workflow base epochs')
    return {'schema':'ur-agent4-ci-epoch/2','pr_number':pr_number,'head_sha':pr_head_sha,
            'main_sha':main_sha,'merge_base_sha':merge_base_sha,
            'workflow_head_success':seen_names==NAMES,
            'workflow_run_ids':sorted(seen_ids),
            'workflow_base_sha':next(iter(bases)),
            'current_merge_tree_qualified':False,
            'merge_base_current':merge_base_sha==main_sha and behind==0,
            'disposition':'HOLD_CURRENT_MAIN_MERGE_TREE_UNTESTED',
            'windows_release_accepted':False,'release_gate_credit':0}
