"""Admit nested agent recovery ZIP members by exact SHA-256, not filenames alone.

No archive extraction or execution. A nested archive without a member-level
manifest is explicitly unqualified, not silently accepted as equivalent.
"""
import hashlib, io, json, re, stat, unicodedata, zipfile
from pathlib import PurePosixPath
from strict_vault_manifest import _portable_win32_component
SHA=re.compile('[0-9a-f]{64}\\Z')
MAX_MEMBER=12*1024*1024
MAX_TOTAL=32*1024*1024

def _strict_json(blob):
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('duplicate manifest JSON key')
            result[k]=v
        return result
    return json.loads(blob.decode('utf-8'),object_pairs_hook=unique)

def admit(blob, *, depth=0, max_depth=2):
    if type(blob) is not bytes or len(blob)>MAX_TOTAL or type(depth) is not int or depth<0:
        raise ValueError('invalid recovery bytes')
    if depth>max_depth:raise ValueError('nested recovery depth exceeded')
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        infos=z.infolist();names=[x.filename for x in infos]
        if len(names)!=len(set(names)) or not names:raise ValueError('duplicate/empty archive')
        total=0
        folded=set()
        for item in infos:
            p=PurePosixPath(item.filename)
            if (item.is_dir() or p.is_absolute() or '..' in p.parts or
                '\\' in item.filename or '\x00' in item.filename or
                not item.filename or any(part in ('','.','..') for part in item.filename.split('/')) or
                unicodedata.normalize('NFC',item.filename)!=item.filename or
                any(not _portable_win32_component(part) for part in item.filename.split('/')) or
                item.flag_bits&1 or item.file_size>MAX_MEMBER or
                stat.S_IFMT(item.external_attr>>16) not in (0,stat.S_IFREG)):
                raise ValueError('unsafe ZIP member')
            fold=item.filename.casefold()
            if fold in folded:raise ValueError('portable ZIP member alias collision')
            folded.add(fold)
            total+=item.file_size
        if total>MAX_TOTAL:raise ValueError('recovery expanded byte budget exceeded')
        for folded_name in folded:
            parts=folded_name.split('/')
            for stop in range(1,len(parts)):
                if '/'.join(parts[:stop]) in folded:
                    raise ValueError('portable ZIP file/directory prefix collision')
        manifest_names=[n for n in names if n in ('MANIFEST.json','MANIFEST-H25.json','ARCHIVE-MANIFEST.json')]
        if not manifest_names:raise ValueError('no manifest')
        # Do not treat a provenance-only manifest as a complete member digest census.
        candidates=[]
        for name in manifest_names:
            parsed=_strict_json(z.read(name))
            if type(parsed) is dict and type(parsed.get('members')) is dict:
                candidates.append((name,parsed))
        if len(candidates)!=1:raise ValueError('missing/ambiguous member-level manifest')
        name,manifest=candidates[0]
        members=manifest['members']
        if set(members)!=set(names)-{name}:raise ValueError('missing/extra ZIP members')
        nested=[]
        for member in names:
            if member==name:continue
            info=members[member]
            if type(info) is str:
                expected_sha=info;expected_size=None
            elif type(info) is dict and set(info)=={'bytes','sha256'} and type(info['bytes']) is int and info['bytes']>=0:
                expected_sha=info['sha256'];expected_size=info['bytes']
            else:
                raise ValueError('malformed member digest')
            if type(expected_sha) is not str or SHA.fullmatch(expected_sha) is None:
                raise ValueError('malformed member SHA')
            payload=z.read(member)
            if (expected_size is not None and len(payload)!=expected_size) or hashlib.sha256(payload).hexdigest()!=expected_sha:
                raise ValueError('member content/size mismatch: '+member)
            if member.endswith('.zip'):
                if depth>=max_depth:
                    nested.append({'name':member,'status':'nested_not_examined_depth_limit'})
                else:
                    try:
                        result=admit(payload,depth=depth+1,max_depth=max_depth)
                        nested.append({'name':member,'status':'manifest_verified','members':result['members']})
                    except ValueError as exc:
                        if 'no manifest' in str(exc) or 'member-level manifest' in str(exc):
                            nested.append({'name':member,'status':'nested_member_manifest_missing'})
                        else:raise
        return {'schema':'ur-recovery-nested-admission/1','members':len(members),
                'nested':nested,'complete_recursive_admission':all(x['status']=='manifest_verified' for x in nested),
                'release_gate_credit':0}
