#!/usr/bin/env python3
"""Read-only verifier for immutable #1990 hosted Windows NTFS artifact ZIPs.

Does not certify physical power-cut, electrical short-write or release QA.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(path, expected_schema):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None, 'ZIP CRC mismatch'
        names=z.namelist()
        assert len(names)==len(set(names)), 'duplicate archive members'
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in names)
        result=json.loads(z.read('result.json'))
        assert result['schema']==expected_schema
        assert result['release_gate_credit']==0
        assert result['human_operator'] is False
        members=result.get('exact_before_full_two_cold_binary_members',
                           result.get('actual_source_bytes'))
        assert isinstance(members,dict) and members
        for name,claim in members.items():
            data=z.read('source-bytes/'+name)
            assert len(data)==claim['bytes'],name+' length'
            assert sha(data)==claim['sha256'],name+' SHA'
        return result,len(members),sha(path.read_bytes())


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pre-intent',required=True,type=Path)
    p.add_argument('--postraw',required=True,type=Path)
    a=p.parse_args()
    pre,npre,hpre=check(a.pre_intent,'ur-real-original-cmd-ntfs-disk-full/1')
    post,npost,hpost=check(a.postraw,'ur-real-win32-ntfs-full-postraw-typed/1')
    assert pre['actual_isolated_vhd_ntfs_full'] is True
    assert pre['actual_native_cmd_exit8_during_original_guest_save'] is True
    assert pre['real_power_loss_or_partial_write'] is False
    assert post['actual_raw_plus_durable_intent_before_disk_full'] is True
    assert post['original_source_postraw_typed_refused_exit8'] is True
    assert post['independent_second_process_win32_error']==112
    assert post['recovery_intent_reconciled_once'] is True
    assert post['two_fresh_original_Windows_cold_boots'] is True
    assert post['electrical_power_cut_or_partial_disk_write'] is False
    def digest(r, n):return r['actual_source_bytes'][n]['sha256']
    assert digest(post,'postraw.raw.bin')!=digest(post,'before.raw.bin')
    assert digest(post,'postraw.typed.bin')==digest(post,'before.typed.bin')
    assert digest(post,'recovered.raw.bin')==digest(post,'postraw.raw.bin')
    assert digest(post,'recovered.typed.bin')!=digest(post,'postraw.typed.bin')
    assert digest(post,'cold2.raw.bin')==digest(post,'recovered.raw.bin')
    assert digest(post,'cold2.typed.bin')==digest(post,'recovered.typed.bin')
    assert digest(post,'denied.typed.bin')==digest(post,'before.typed.bin')
    assert digest(post,'denied.raw.bin')==digest(post,'postraw.raw.bin')
    assert pre['original_cmd_sha256']==post['original_cmd_sha256']
    print(json.dumps({'status':'PASS','scope':'hosted original Windows NTFS artifact receipts only',
      'pre_intent_zip_sha256':hpre,'postraw_zip_sha256':hpost,
      'verified_binary_members':npre+npost,'actual_full_volume':True,
      'actual_postraw_typed_refusal':True,'two_cold_boots':True,
      'electrical_power_cut_tested':False,'release_gate_credit':0},sort_keys=True,indent=2))

if __name__=='__main__':main()
