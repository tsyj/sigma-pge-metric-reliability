"""Verify a writable Git copy and detect missing/tampered public assets."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sigma_audit import cache as C


def main():
    cases = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / 'data'
        shutil.copytree(C.DATA_ROOT, root)
        md = root / 'reference/PREREG_multienv_metrology.md'
        # A Git checkout has writable files; this is a disposable test copy.
        md.chmod(0o644)
        with patch.multiple(C, DATA_ROOT=str(root), MULTIENV_MD=str(md),
                            MULTIENV_SEAL_ALT=str(md.with_suffix('.sha256'))):
            assert C.release_snapshot_status()['ok']
            cases.append('writable checkout accepted as snapshot only')
            target = root / 'cache/primitives_zonal.npz'
            original = target.read_bytes()
            target.write_bytes(original + b'changed')
            assert not C.release_snapshot_status()['ok']
            cases.append('cache mutation rejected')
            target.write_bytes(original)
            target.unlink()
            assert not C.release_snapshot_status()['ok']
            cases.append('missing cache rejected')
            target.write_bytes(original)
            manifest = root / 'RELEASE_MANIFEST.json'
            original_manifest = manifest.read_bytes()
            obj = json.loads(original_manifest)
            obj['files'].pop('cache/primitives_zonal.npz')
            manifest.write_text(json.dumps(obj))
            assert not C.release_snapshot_status()['ok']
            cases.append('omitted required registration rejected')
            manifest.write_bytes(original_manifest)
            md.write_bytes(md.read_bytes() + b'changed')
            assert not C.release_snapshot_status()['ok']
            cases.append('preregistration mutation rejected')
    print('release snapshot: %d/%d PASS' % (len(cases), len(cases)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
