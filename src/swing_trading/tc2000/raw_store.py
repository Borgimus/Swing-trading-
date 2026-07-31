from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from swing_trading.tc2000.models import ScanUpload, StoredRawBatch


class RawStorageError(OSError):
    """Raised when immutable raw import evidence cannot be preserved."""


class FileSystemRawBatchStore:
    def __init__(self, root: Path) -> None:
        self._root = root

    def persist(
        self,
        batch_sha256: str,
        uploads: tuple[ScanUpload, ...],
        content_hashes: tuple[str, ...],
        received_at: datetime,
    ) -> StoredRawBatch:
        final_dir = self._root / batch_sha256
        manifest_path = final_dir / "manifest.json"
        if final_dir.exists():
            return self._verify_existing(
                final_dir, batch_sha256, uploads, content_hashes, received_at
            )

        temp_dir = self._root / f".{batch_sha256}.tmp-{uuid4().hex}"
        try:
            self._root.mkdir(parents=True, exist_ok=True)
            temp_dir.mkdir(mode=0o700)
            file_uris: list[str] = []
            manifest_files: list[dict[str, str | int]] = []
            for index, (upload, content_hash) in enumerate(
                zip(uploads, content_hashes, strict=True)
            ):
                raw_path = temp_dir / f"file-{index:02d}.raw"
                raw_path.write_bytes(upload.content)
                os.chmod(raw_path, 0o600)
                file_uris.append(str(final_dir / raw_path.name))
                manifest_files.append(
                    {
                        "file_index": index,
                        "original_filename": upload.filename,
                        "content_sha256": content_hash,
                        "stored_name": raw_path.name,
                    }
                )
            manifest = {
                "batch_sha256": batch_sha256,
                "received_at": received_at.isoformat(),
                "files": manifest_files,
            }
            (temp_dir / "manifest.json").write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")),
                encoding="utf-8",
            )
            os.chmod(temp_dir / "manifest.json", 0o600)
            try:
                temp_dir.rename(final_dir)
            except OSError:
                if not final_dir.exists():
                    raise
                shutil.rmtree(temp_dir)
                return self._verify_existing(
                    final_dir, batch_sha256, uploads, content_hashes, received_at
                )
            return StoredRawBatch(manifest_uri=str(manifest_path), file_uris=tuple(file_uris))
        except Exception as exc:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise RawStorageError("failed to preserve raw TC2000 batch") from exc

    @staticmethod
    def _verify_existing(
        final_dir: Path,
        batch_sha256: str,
        uploads: tuple[ScanUpload, ...],
        content_hashes: tuple[str, ...],
        received_at: datetime,
    ) -> StoredRawBatch:
        del received_at  # Reception time differs on replay and is not part of immutable identity.
        manifest_path = final_dir / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("batch_sha256") != batch_sha256:
                raise RawStorageError("stored manifest batch hash mismatch")
            manifest_files = manifest.get("files")
            if not isinstance(manifest_files, list) or len(manifest_files) != len(uploads):
                raise RawStorageError("stored manifest file count mismatch")
            file_uris: list[str] = []
            for index, (upload, expected_hash) in enumerate(
                zip(uploads, content_hashes, strict=True)
            ):
                entry = manifest_files[index]
                if (
                    entry.get("file_index") != index
                    or entry.get("original_filename") != upload.filename
                    or entry.get("content_sha256") != expected_hash
                ):
                    raise RawStorageError("stored manifest evidence mismatch")
                raw_path = final_dir / f"file-{index:02d}.raw"
                actual_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
                if actual_hash != expected_hash:
                    raise RawStorageError("stored raw file hash mismatch")
                file_uris.append(str(raw_path))
            return StoredRawBatch(
                manifest_uri=str(manifest_path),
                file_uris=tuple(file_uris),
            )
        except RawStorageError:
            raise
        except Exception as exc:
            raise RawStorageError("failed to verify existing raw TC2000 batch") from exc
