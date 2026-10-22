#!/usr/bin/env python3
"""Read-only Git-blob crosswalk for *preserved* recovery ZIP code members.

Find exact Git blob occurrences on a specified repository revision, including
nested archive members. A matching blob is only a deduplication lead: it is
never semantic integration, authorized publication, release QA or permission
to remove the archived source. Manifest and rights review remain independent.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import zipfile
import zlib

SHA40 = re.compile(r'[0-9a-f]{40}\Z')
SOURCE_SUFFIXES = ('.py', '.c', '.cc', '.cpp', '.cxx', '.h', '.hpp', '.hh', '.rs', '.js', '.ts', '.tsx', '.sh', '.ps1', '.yml', '.yaml', '.cmake')
PATCH_SUFFIXES = ('.patch', '.diff')
MAX_ARCHIVE = 64 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_MEMBER = 32 * 1024 * 1024
MAX_MEMBERS = 10000


def git_blob(data):
    if type(data) is not bytes:
        raise ValueError('Git blob input must be bytes')
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def index_git_tree(tree_output):
    """Index complete git ls-tree -rz REF bytes by exact Git SHA-1."""
    if type(tree_output) is not bytes or (tree_output and not tree_output.endswith(b'\0')):
        raise ValueError('incomplete NUL-terminated git tree census')
    if not tree_output:
        return {}
    lookup = {}
    for record in tree_output[:-1].split(b'\0'):
        try:
            meta, path = record.split(b'\t', 1)
            mode, kind, sha = meta.split(b' ')
            sha = sha.decode('ascii')
            name = path.decode('utf-8')
        except (ValueError, UnicodeDecodeError):
            raise ValueError('invalid git tree record') from None
        if not name or not SHA40.fullmatch(sha):
            raise ValueError('invalid git object identity')
        if kind == b'blob':
            lookup.setdefault(sha, []).append(name)
        elif kind not in (b'tree', b'commit'):
            raise ValueError('unknown git tree object kind')
    return {sha: sorted(paths) for sha, paths in lookup.items()}


def crosswalk(archive, tree_output, *, max_depth=2):
    """Observe member equality without asserting semantic integration."""
    if (type(archive) is not bytes or len(archive) > MAX_ARCHIVE or
            type(max_depth) is not int or not 0 <= max_depth <= 3):
        raise ValueError('invalid archive/depth')
    index = index_git_tree(tree_output)
    observed = []
    counters = {'uncompressed_bytes': 0, 'members': 0, 'nested_archives': 0}

    def walk(blob, prefix, depth):
        if len(blob) > MAX_ARCHIVE:
            raise ValueError('nested ZIP exceeds byte budget')
        try:
            with zipfile.ZipFile(io.BytesIO(blob)) as zipped:
                seen = set()
                entries = zipped.infolist()
                counters['members'] += len(entries)
                if counters['members'] > MAX_MEMBERS or not entries:
                    raise ValueError('empty or oversized source archive')
                for info in entries:
                    name = info.filename
                    path = PurePosixPath(name)
                    if (not name or info.is_dir() or path.is_absolute() or
                            '..' in path.parts or '\\' in name or '\x00' in name or
                            any(part in ('', '.', '..') for part in name.split('/')) or
                            info.flag_bits & 1 or
                            stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG)):
                        raise ValueError('unsafe ZIP member')
                    folded = name.casefold()
                    if folded in seen:
                        raise ValueError('duplicate/aliased ZIP member')
                    seen.add(folded)
                    counters['uncompressed_bytes'] += info.file_size
                    if (info.file_size > MAX_MEMBER or
                            counters['uncompressed_bytes'] > MAX_EXPANDED):
                        raise ValueError('expanded ZIP budget exceeded')
                    payload = zipped.read(info)
                    fullname = prefix + name
                    if name.lower().endswith('.zip'):
                        counters['nested_archives'] += 1
                        if depth < max_depth:
                            walk(payload, fullname + '!/', depth + 1)
                        else:
                            observed.append({'member': fullname,
                                             'status': 'nested_unexamined_depth_limit'})
                    elif name.lower().endswith(SOURCE_SUFFIXES + PATCH_SUFFIXES):
                        sha = git_blob(payload)
                        paths = index.get(sha, [])
                        observed.append({'member': fullname, 'bytes': len(payload),
                                         'member_sha256': hashlib.sha256(payload).hexdigest(),
                                         'git_blob_sha': sha,
                                         'kind': 'patch' if name.lower().endswith(PATCH_SUFFIXES) else 'source_or_test',
                                         'status': 'exact_git_blob_observed' if paths else 'unmatched_needs_review',
                                         'git_paths': paths,
                                         'same_path': name in paths})
        except (zipfile.BadZipFile, zipfile.LargeZipFile, EOFError, NotImplementedError, zlib.error) as exc:
            raise ValueError('invalid or corrupt source ZIP') from exc

    walk(archive, '', 0)
    exact = sum(v['status'] == 'exact_git_blob_observed' for v in observed)
    return {'schema': 'ur-archive-git-blob-crosswalk/1',
            'outer_sha256': hashlib.sha256(archive).hexdigest(),
            'members_scanned': counters['members'],
            'nested_archives_encountered': counters['nested_archives'],
            'source_like_members': sum('git_blob_sha' in v for v in observed),
            'exact_blob_occurrences': exact,
            'unmatched_or_unexamined': len(observed) - exact,
            'items': observed,
            'member_manifest_authenticated': False,
            'automatic_integration_decisions': 0,
            'archive_deletion_authorized': False,
            'release_gate_credit': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--repo', type=Path, default=Path('.'))
    parser.add_argument('--ref', default='main')
    args = parser.parse_args()
    if args.ref.startswith('-'):
        parser.error('ref must not be an option')
    tree = subprocess.run(['git', '-C', str(args.repo), 'ls-tree', '-r', '-z', args.ref],
                          check=True, stdout=subprocess.PIPE).stdout
    print(json.dumps(crosswalk(args.archive.read_bytes(), tree), indent=2))


if __name__ == '__main__':
    main()
