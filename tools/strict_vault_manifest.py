"""Portable recovery ZIP verifier with exact complete-member inventory.

The archive is a handoff, not a source of release authority. Manifest hashes
are only integrity checks against an independently pinned outer ZIP digest.
"""
from hashlib import sha256
from io import BytesIO
from zipfile import ZipFile,BadZipFile
import json,re,stat,unicodedata

HEX64=re.compile(r'[0-9a-f]{64}\Z')
MAX_ZIP=64*1024*1024
MAX_MEMBER=64*1024*1024
MAX_TOTAL=128*1024*1024
WINDOWS_DEVICES={'CON','PRN','AUX','NUL'} | {'COM'+str(n) for n in range(1,10)} | {'LPT'+str(n) for n in range(1,10)}


def _portable_win32_component(part):
    """Refuse names that lose identity or cannot be represented as Win32 files.

    This is a conservative cross-platform recovery-envelope policy, not a
    Windows path open or an extraction permission.
    """
    if (part.endswith((' ', '.')) or ':' in part or
            any(unicodedata.category(ch) in ('Cc', 'Cf') for ch in part) or
            len(part.encode('utf-16-le')) // 2 > 255):
        return False
    # Win32 DOS aliases treat superscript digits ¹²³ as COM/LPT 1,2,3.
    # Space immediately before a dot can disguise a device stem.
    stem = part.split('.', 1)[0].rstrip(' ').upper()
    for digit, ascii_digit in (('¹', '1'), ('²', '2'), ('³', '3')):
        stem = stem.replace(digit, ascii_digit)
    return stem not in WINDOWS_DEVICES


def verify(raw, *, expected_sha256=None):
    if type(raw) is not bytes or len(raw)>MAX_ZIP:
        raise ValueError('invalid archive bytes/size')
    if expected_sha256 is not None and (type(expected_sha256) is not str or
            not HEX64.fullmatch(expected_sha256) or
            sha256(raw).hexdigest()!=expected_sha256):
        raise ValueError('outer archive SHA mismatch')
    try:
        with ZipFile(BytesIO(raw)) as z:
            members=z.infolist()
            if len(members)>1000 or not any(i.filename=='MANIFEST.json' for i in members):
                raise ValueError('missing/oversized manifest census')
            names=[];folded=set();total=0
            for i in members:
                n=i.filename
                if (not n or n.startswith('/') or '\\' in n or
                        unicodedata.normalize('NFC',n)!=n or
                        any(c in ('','.','..') for c in n.split('/')) or
                        any(not _portable_win32_component(part) for part in n.split('/')) or
                        stat.S_ISLNK(i.external_attr >> 16) or i.is_dir() or
                        i.file_size>MAX_MEMBER):
                    raise ValueError('unsafe archive member')
                fold=n.casefold()
                if fold in folded:
                    raise ValueError('portable name collision')
                folded.add(fold);names.append(n);total+=i.file_size
                if total>MAX_TOTAL:
                    raise ValueError('expanded archive too large')
            # A ZIP member cannot also be an implicit parent directory on
            # Windows/portable extraction. Casefold handles cross-platform aliases.
            for folded_name in folded:
                for i in range(1,len(folded_name.split('/'))):
                    if '/'.join(folded_name.split('/')[:i]) in folded:
                        raise ValueError('portable file/directory prefix collision')
            if z.testzip() is not None:
                raise ValueError('bad archive CRC')
            manifest=json.loads(z.read('MANIFEST.json'),object_pairs_hook=_unique_pairs)
            if type(manifest) is not dict or set(manifest)!=(set(names)-{'MANIFEST.json'}):
                raise ValueError('manifest not complete inventory')
            for name,entry in manifest.items():
                if (type(entry) is not dict or set(entry)!={'bytes','sha256'} or
                        type(entry['bytes']) is not int or entry['bytes']<0 or
                        type(entry['sha256']) is not str or
                        not HEX64.fullmatch(entry['sha256'])):
                    raise ValueError('invalid manifest entry')
                data=z.read(name)
                if len(data)!=entry['bytes'] or sha256(data).hexdigest()!=entry['sha256']:
                    raise ValueError('manifest member hash/size mismatch')
            return {'members':len(names),'manifested_payloads':len(manifest),
                    'archive_sha256':sha256(raw).hexdigest(),
                    'integrity_only':True,'release_gate_credit':0}
    except (BadZipFile,UnicodeDecodeError,KeyError,TypeError,OverflowError,json.JSONDecodeError) as exc:
        raise ValueError('invalid ZIP or manifest encoding') from exc


def _unique_pairs(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate manifest key')
        out[k]=v
    return out
