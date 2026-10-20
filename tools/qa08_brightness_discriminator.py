#!/usr/bin/env python3
"""ROM-free empirical integer brightness fit on immutable QA08 source observations.

This matches the *observed* renderer's 88 main-source/final pairs only. It
cannot prove hardware colour maths, P7 equivalence or historical source epoch.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, zipfile, io, stat, struct

ARCHIVE_SHA='10bd91c7be06e3ac832675f2b5268bf179a2b03b5f07dcf8fd632fad18372ec2'
ANCHORS={(53,41),(65,52),(70,58),(84,77),(175,145),(187,160),(190,161),(202,182)}
FRAMES=set(range(5176,5187))

def scale_channel(v, brightness):
    if type(v) is not int or not 0<=v<=31 or type(brightness) is not int or not 0<=brightness<=15:
        raise ValueError('invalid five-bit channel or brightness')
    return (((v<<3)|(v>>2))*brightness)//15

def expected_rgb(word, brightness):
    if len(word)!=4 or any(c not in '0123456789abcdef' for c in word):
        raise ValueError('invalid RGB555 source word')
    value=int(word,16)
    return tuple(scale_channel((value>>shift)&31,brightness) for shift in (0,5,10))


# Lexical schema: do not allow alternate spellings of the same observed word.
import re
_DECIMAL = re.compile(r'(?:0|[1-9][0-9]*)\Z')
_HEX2 = re.compile(r'[0-9a-f]{2}\Z')
_HEX4 = re.compile(r'[0-9a-f]{4}\Z')
def _canonical_observation(fields, typ):
    for key in ('frame','x','logical_y','ppu_line'):
        if not _DECIMAL.fullmatch(fields[key]):
            raise ValueError('noncanonical coordinate lexeme: '+key)
    if typ.endswith('SOURCE'):
        for key in ('index','inidisp','cgadsub','cgwsel'):
            if not _HEX2.fullmatch(fields[key]):
                raise ValueError('noncanonical source hex: '+key)
        for key in ('selected_rgb555','cgram_index_word','cgram6c','cgram6d','cgram6e','cgram6f'):
            if not _HEX4.fullmatch(fields[key]):
                raise ValueError('noncanonical RGB555: '+key)
    else:
        for key in ('inidisp','tm','ts'):
            if not _HEX2.fullmatch(fields[key]):
                raise ValueError('noncanonical final hex: '+key)
        if not _HEX4.fullmatch(fields['fixed']):
            raise ValueError('noncanonical fixed colour')
        rgb=fields['RGB8'].split(',')
        if len(rgb)!=3 or any(not _DECIMAL.fullmatch(c) or int(c)>255 for c in rgb):
            raise ValueError('noncanonical final RGB8')

def parse(rows):
    pairs={}; stages=Counter()
    for line in rows:
        toks=line.split(); typ=toks[0]
        if typ not in ('UR_QA08_LATE_PPU_SOURCE','UR_QA08_LATE_PPU_FINAL'):
            raise ValueError('unexpected source row')
        fields={}
        for token in toks[1:]:
            if '=' not in token: raise ValueError('malformed field')
            k,v=token.split('=',1)
            if k in fields:raise ValueError('duplicate field')
            fields[k]=v
        # Source-stage and final-stage records are separate immutable schemas.
        # Reject extraneous verdict claims or borrowed register fields rather
        # than silently ignoring them during an independent evidence audit.
        coordinate_fields={'frame','x','logical_y','ppu_line'}
        source_fields=coordinate_fields|{'sub','layer','directcolor','index',
            'selected_rgb555','cgram_index_word','cgram6c','cgram6d',
            'cgram6e','cgram6f','inidisp','cgadsub','cgwsel'}
        final_fields=coordinate_fields|{'RGB8','inidisp','fixed','tm','ts'}
        if set(fields)!=(final_fields if typ.endswith('FINAL') else source_fields):
            raise ValueError('source/final row schema contradiction')
        _canonical_observation(fields, typ)
        frame=int(fields['frame']);xy=(int(fields['x']),int(fields['logical_y']))
        if frame not in FRAMES or xy not in ANCHORS or int(fields['ppu_line'])!=xy[1]+1:
            raise ValueError('source coordinate out of scope')
        stage='final' if typ.endswith('FINAL') else fields['sub']
        if typ.endswith('SOURCE') and stage not in ('0','1'):
            raise ValueError('source cannot impersonate final')
        if typ.endswith('FINAL') and 'sub' in fields:
            raise ValueError('final cannot carry source stage')
        if stage not in ('0','1','final'):raise ValueError('unknown source stage')
        key=(frame,xy)
        if stage in pairs.setdefault(key,{}):raise ValueError('duplicate source stage')
        pairs[key][stage]=fields;stages[stage]+=1
    if len(pairs)!=88 or stages!=Counter({'0':88,'1':88,'final':88}):
        raise ValueError('incomplete bounded sample')
    words=Counter()
    frame_palette_snapshots={}
    for key, rec in pairs.items():
        main,sub,final=(rec[stage] for stage in ('0','1','final'))
        if (main['directcolor']!='0' or main['layer']!='0' or
            main['inidisp']!='0e' or final['inidisp']!='0e' or
            sub['inidisp']!='0e'):
            raise ValueError('unexpected colour source/brightness')
        # The bounded observer emitted both source stages for each pixel.
        # Require the same effective-CGRAM snapshot at a given source frame;
        # otherwise a corrupted sub stage or off-coordinate anchor can pass
        # the main-to-final brightness correlation unnoticed.
        slots=('cgram6c','cgram6d','cgram6e','cgram6f')
        palette=tuple(main[slot] for slot in slots)
        if any(sub[slot]!=main[slot] for slot in slots):
            raise ValueError('main/sub CGRAM snapshot contradiction')
        frame=key[0]
        prior=frame_palette_snapshots.setdefault(frame,palette)
        if prior!=palette:
            raise ValueError('same-frame CGRAM snapshot contradiction')
        if (sub['layer']!='5' or sub['directcolor']!='0' or
            sub['index']!='00' or sub['selected_rgb555']!='39ce' or
            sub['cgram_index_word']!=sub['selected_rgb555']):
            raise ValueError('unexpected sub-screen source identity')
        if (main['cgadsub']!=sub['cgadsub'] or
            main['cgwsel']!=sub['cgwsel']):
            raise ValueError('main/sub colour-math register contradiction')
        # Pin the complete bounded colour-math register witness, not only
        # the empirical selected-word -> final RGB8 correlation.
        if any(rec[stage].get('cgadsub')!='7f' or
               rec[stage].get('cgwsel')!='02' for stage in ('0','1')):
            raise ValueError('unexpected source register witness')
        if (final.get('fixed')!='0000' or final.get('tm')!='13' or
            final.get('ts')!='10'):
            raise ValueError('unexpected final pixel register witness')
        slot=int(main['index'],16)
        if slot not in range(0x6c,0x70):raise ValueError('unexpected palette index')
        word=main['selected_rgb555']
        if word!=main['cgram_index_word'] or word!=main[f'cgram{slot:02x}']:
            raise ValueError('CGRAM selected-word contradiction')
        expected=expected_rgb(word,14)
        actual=tuple(int(c) for c in final['RGB8'].split(','))
        if actual!=expected:raise ValueError(f'brightness fit mismatch at {key}: {actual} != {expected}')
        words[word]+=1
    if len(words)!=4:raise ValueError('incomplete four-word palette census')
    return {'schema':'qa08-current-source-integer-brightness-fit/1',
            'source_triplets':88,'source_frames':11,
            'observed_rgb555_to_rgb8':{w:list(expected_rgb(w,14)) for w in sorted(words)},
            'observed_counts':dict(sorted(words.items())),
            'model':'expand RGB5 to RGB8 via (v<<3)|(v>>2), then floor(expanded*14/15)',
            'model_is_empirical_not_hardware_proof':True,
            'same_epoch_original_native_proven':False,
            'release_gate_credit':0}

def _canonical_source_rows(blob):
    """Preserve the observed CRLF record envelope, without splitlines aliases.

    Python splitlines also treats vertical tab/form feed as row separators,
    silently admitting a different source transcript when an archive is
    repinned for adversarial validation.
    """
    if (type(blob) is not bytes or not blob.endswith(b'\r\n') or
            blob.count(b'\r\n') != 264):
        raise ValueError('QA08 source log CRLF envelope mismatch')
    lines = blob[:-2].split(b'\r\n')
    if (len(lines) != 264 or any(
            not line or any(byte < 32 or byte > 126 for byte in line)
            for line in lines)):
        raise ValueError('QA08 source log contains noncanonical row bytes')
    return [line.decode('ascii') for line in lines]


def _crc_witness(blob):
    """Validate one immutable 5,484-field guest trace, not historical RF017 parity."""
    if type(blob) is not bytes or not blob.endswith(b'\r\n'):
        raise ValueError('guest CRC record envelope')
    rows=blob[:-2].split(b'\r\n')
    if len(rows)!=5484 or any(re.fullmatch(rb'0x[0-9a-f]{8}', row) is None for row in rows):
        raise ValueError('guest CRC frame count or lexeme')
    return hashlib.sha256(blob).hexdigest()


# Exact key set observed in the pinned source-epoch receipt.
STATUS_KEYS = frozenset(['QA08_QA10_release_accepted', 'actual_off_executable_sha256', 'actual_on_executable_sha256', 'actual_source_P7_ON_OFF_noninterference_proven', 'actual_source_process_runs', 'complete_guest_replay_equivalence_proven', 'final_diagnostic_outcome', 'historical_RF017_guest_CRC_qualified', 'off_CRC_sha256', 'off_actual_guest_frames', 'off_bounded_source_rows', 'off_matches_historical_RF017_CRC', 'on_CRC_sha256', 'on_actual_guest_frames', 'on_bounded_source_rows', 'on_matches_historical_RF017_CRC', 'original_USA_ROM_sha256', 'real_two_pad_script_sha256', 'refusal', 'same_epoch_ON_OFF_guest_CRC_equal', 'schema', 'unadmitted_PPU_observation_only', 'unadmitted_live_PPU_sample'])

def _noninterference_witness(archive):
    on=archive.read('on-guest-crc.txt')
    off=archive.read('off-guest-crc.txt')
    on_sha=_crc_witness(on)
    off_sha=_crc_witness(off)
    if on!=off:
        raise ValueError('ON/OFF guest CRC divergence')
    status_raw=archive.read('status.json')
    try:
        status=json.loads(status_raw.decode('utf-8'), object_pairs_hook=_unique_json_pairs)
    except (ValueError, UnicodeDecodeError):
        raise ValueError('invalid QA08 status receipt')
    expected={'on_CRC_sha256':on_sha,'off_CRC_sha256':off_sha,
              'on_actual_guest_frames':5484,'off_actual_guest_frames':5484,
              'same_epoch_ON_OFF_guest_CRC_equal':True,
              'actual_source_P7_ON_OFF_noninterference_proven':False,
              'historical_RF017_guest_CRC_qualified':False,
              'QA08_QA10_release_accepted':False,
              # The receipt also contains unadmitted diagnostic metadata.
              # These values must not be allowed to turn into release claims
              # inside a synthetically re-pinned archive.
              'actual_source_process_runs':2,
              'complete_guest_replay_equivalence_proven':False,
              'final_diagnostic_outcome':'REFUSED',
              'on_bounded_source_rows':264,
              'off_bounded_source_rows':1,
              'on_matches_historical_RF017_CRC':False,
              'off_matches_historical_RF017_CRC':False,
              'unadmitted_PPU_observation_only':True,
              'schema':'QA08-native-Windows-optin-pixel-witness/1',
              'actual_off_executable_sha256':'819a8f0d7d8730c07b0ec2e2e28228d44787a1d26a20df8d5bc8d80edceb6411',
              'actual_on_executable_sha256':'31ef9f65630d31e905f75bfc8ae26adce0cf6378ee9eb8f1d227eaa8563cba5a',
              'original_USA_ROM_sha256':'859ec99fdc25dd9b239d9085bf656e4f49c93a32faa5bb248da83efd68ebd478',
              'real_two_pad_script_sha256':'ef74ec51fa585aa76652f4a14d2727f0074434b3925522ab2607e3bd29aa0194',
              'refusal':'same-epoch ON/OFF guest CRC matched but historic RF017 CRC did not'}
    # This immutable witness has a fixed receipt schema. Unknown fields can
    # masquerade as independently approved gates in downstream consumers.
    if (type(status) is not dict or set(status) != STATUS_KEYS or any(
        key not in status or type(status[key]) is not type(value) or status[key]!=value
        for key,value in expected.items()
    )):
        raise ValueError('QA08 status contradicts bounded guest CRC evidence')
    # A synthetic archive re-pin must not turn the bounded diagnostic sample
    # into historical source parity, change its pixels, or substitute binaries.
    sample=status['unadmitted_live_PPU_sample']
    if (type(sample) is not list or len(sample)!=8 or
            hashlib.sha256(json.dumps(sample,sort_keys=True,ensure_ascii=False,
                                      separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
            != '3f97ea717148ad8f187b3c667af7e5c061ba557699db6a52cc5c2e0df9cc21d3'):
        raise ValueError('QA08 unadmitted source sample differs from pinned epoch')
    if archive.read('off-source.log')!=b'\r\n':
        raise ValueError('observer-OFF unexpectedly produced source samples')


def _unique_json_pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:
            raise ValueError('duplicate QA08 status key')
        result[key]=value
    return result


def _strict_zip_envelope(blob, archive):
    """Refuse noncanonical ZIP wrappers before interpreting a pinned source epoch.

    ZIP readers commonly accept a self-extracting prefix, a ZIP comment, or
    trailing unindexed bytes. Those are useful general-purpose ZIP features,
    but the five-member QA08 diagnostic transport does not produce them.
    This is an archive-envelope guard, not a source-pixel or release verdict.
    """
    eocd = blob.rfind(b'PK\x05\x06')
    if eocd < 0 or eocd + 22 != len(blob):
        raise ValueError('QA08 archive has comment or unindexed trailer')
    signature, disk, central_disk, on_disk, total, size, offset, comment = \
        struct.unpack_from('<IHHHHIIH', blob, eocd)
    if (signature != 0x06054b50 or disk or central_disk or
            on_disk != 5 or total != 5 or comment or
            offset + size != eocd or archive.start_dir != offset):
        raise ValueError('QA08 archive central-directory envelope mismatch')
    if not archive.infolist() or archive.infolist()[0].header_offset != 0:
        raise ValueError('QA08 archive has unindexed prefix')


def audit(path):
    blob=Path(path).read_bytes()
    if hashlib.sha256(blob).hexdigest()!=ARCHIVE_SHA:
        raise ValueError('immutable source archive mismatch')
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        _strict_zip_envelope(blob, z)
        expected={'status.json','on-source.log','on-guest-crc.txt',
                  'off-source.log','off-guest-crc.txt'}
        members=z.infolist()
        names=[m.filename for m in members]
        if len(names)!=len(expected) or set(names)!=expected:
            raise ValueError('QA08 archive member namespace contradiction')
        if any(m.is_dir() or (m.external_attr & 0x10) or
               (m.flag_bits & 1) or m.file_size > 1024*1024 or
               stat.S_IFMT(m.external_attr >> 16) not in (0,stat.S_IFREG)
               for m in members):
            raise ValueError('QA08 archive member type/size contradiction')
        if z.testzip() is not None:raise ValueError('ZIP CRC')
        _noninterference_witness(z)
        return parse(_canonical_source_rows(z.read('on-source.log')))
if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1]),indent=2,sort_keys=True))
