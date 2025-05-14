from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from kash.config.logger import get_logger
from kash.utils.file_utils.file_formats_model import Format, detect_file_format
from prettyfmt import fmt_lines
from pydantic import BaseModel, Field
from strif import hash_file

from texpr.textpress_env import Env

log = get_logger(__name__)


log_api = log.debug


CLIENT_TIMEOUT = 120


class UploadFileMetadata(BaseModel):
    """Metadata for a file to be uploaded."""

    path: str
    md5: str
    content_type: str = Field(..., alias="contentType")


class DeleteFileMetadata(BaseModel):
    """Metadata for a file to be deleted (used in presign)."""

    path: str


class PresignRequest(BaseModel):
    """Request payload for getting presigned URLs."""

    base_version: int = Field(..., alias="baseVersion")
    uploads: list[UploadFileMetadata]
    delete: list[DeleteFileMetadata]


class CommitRequest(BaseModel):
    """Request payload for committing changes."""

    base_version: int = Field(..., alias="baseVersion")
    uploads: list[UploadFileMetadata]
    delete: list[DeleteFileMetadata]


class PresignUploadInfo(BaseModel):
    """Information returned for each file in the presign response."""

    path: str
    url: str
    headers: dict[str, str]


class PresignResponse(BaseModel):
    """Response payload from the presign endpoint."""

    uploads: list[PresignUploadInfo] = Field(default_factory=list)
    delete: list[str] = Field(default_factory=list)
    base_version: int = Field(..., alias="baseVersion")
    expires_in: int | None = Field(default=None, alias="expiresIn")


class ManifestResponse(BaseModel):
    """Response payload for manifest endpoints."""

    version: int
    generated_at: datetime = Field(..., alias="generatedAt")
    files: dict[str, str]
    """Maps file path to MD5 hash."""


def get_manifest(client: httpx.Client, api_root: str, api_key: str) -> ManifestResponse:
    """
    Fetch the current manifest from the Textpress API.
    """
    url = f"{api_root}/api/sync/manifest"
    headers = {"x-api-key": api_key}
    response = client.get(url, headers=headers)
    response.raise_for_status()
    return ManifestResponse.model_validate(response.json())


def get_presigned_urls(
    client: httpx.Client,
    api_root: str,
    api_key: str,
    base_version: int,
    files_to_upload: list[Path],
    files_to_delete: list[str] | None = None,
) -> PresignResponse:
    """
    Gets presigned URLs for uploading files.
    """
    if files_to_delete is None:
        files_to_delete = []

    uploads_metadata: list[UploadFileMetadata] = []
    delete_metadata: list[DeleteFileMetadata] = []

    for file_path in files_to_upload:
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        format = detect_file_format(file_path) or Format.binary
        mime = format.mime_type or "application/octet-stream"
        md5 = hash_file(file_path, "md5").hex  # API expects hex
        uploads_metadata.append(UploadFileMetadata(path=file_path.name, md5=md5, contentType=mime))

    for file_path_str in files_to_delete:
        delete_metadata.append(DeleteFileMetadata(path=file_path_str))

    presign_req = PresignRequest(
        baseVersion=base_version,
        uploads=uploads_metadata,
        delete=delete_metadata,
    )

    url = f"{api_root}/api/sync/presign-batch"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    request_data_json = presign_req.model_dump(by_alias=True, exclude_none=True)
    log_api(">> get_presigned_urls: %s - %s - %s", url, headers, presign_req)

    response = client.post(url, headers=headers, json=request_data_json)
    response.raise_for_status()
    return PresignResponse.model_validate(response.json())


def upload_file(client: httpx.Client, file_path: Path, upload_info: dict[str, Any]) -> None:
    """
    Uploads a single file using the presigned URL and headers.
    """
    url: str = upload_info["url"]
    headers: dict[str, str] = upload_info["headers"]

    log_api(">> upload_file: %s - %s", url, headers)
    with open(file_path, "rb") as f:
        content = f.read()
        # httpx handles Content-Length automatically
        response = client.put(url, headers=headers, content=content)
    response.raise_for_status()


def commit_manifest(
    client: httpx.Client,
    api_root: str,
    api_key: str,
    base_version: int,
    uploaded_files_details: list[PresignUploadInfo],
    files_to_delete_paths: list[str] | None = None,
) -> ManifestResponse:
    """
    Commits the changes to the manifest using Pydantic models.
    """
    if files_to_delete_paths is None:
        files_to_delete_paths = []

    uploads_metadata: list[UploadFileMetadata] = []
    for info in uploaded_files_details:
        uploads_metadata.append(
            UploadFileMetadata(
                path=info.path,
                md5=info.headers["Content-MD5"],
                contentType=info.headers["Content-Type"],
            )
        )

    delete_metadata: list[DeleteFileMetadata] = [
        DeleteFileMetadata(path=p) for p in files_to_delete_paths
    ]

    commit_req = CommitRequest(
        baseVersion=base_version, uploads=uploads_metadata, delete=delete_metadata
    )
    url = f"{api_root}/api/sync/commit"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    request_data_json = commit_req.model_dump(by_alias=True, exclude_none=True)

    log_api(">> commit_manifest: %s - %s - %s", url, headers, commit_req)
    response = client.post(url, headers=headers, json=request_data_json)
    response.raise_for_status()

    return ManifestResponse.model_validate(response.json())


def publish_files(
    upload_paths: list[Path], delete_paths: list[str] | None = None
) -> ManifestResponse:
    """
    Publishes files (uploads and deletes) to Textpress.
    """
    api_root = Env.TEXTPRESS_API_ROOT.read_str()
    api_key = Env.TEXTPRESS_API_KEY.read_str()
    if delete_paths is None:
        delete_paths = []

    log.message("Publishing files:\n%s", fmt_lines(upload_paths))

    with httpx.Client(timeout=CLIENT_TIMEOUT) as client:
        manifest: ManifestResponse = get_manifest(client, api_root, api_key)
        log_api("<< get_manifest response: %s", manifest)

        presign_response: PresignResponse = get_presigned_urls(
            client, api_root, api_key, manifest.version, upload_paths, delete_paths
        )
        log_api("<< get_presigned_urls response: %s", presign_response)

        upload_info_map = {info.path: info for info in presign_response.uploads}

        uploaded_files_details: list[PresignUploadInfo] = []
        for file_path in upload_paths:
            if file_path.name in upload_info_map:
                upload_info = upload_info_map[file_path.name]
                upload_file(client, file_path, upload_info.model_dump())
                uploaded_files_details.append(upload_info)
            else:
                log_api(
                    "File %s was requested for upload but not included in presign response (already up-to-date?)",
                    file_path.name,
                )

        commit_response: ManifestResponse = commit_manifest(
            client,
            api_root,
            api_key,
            manifest.version,
            uploaded_files_details,
            files_to_delete_paths=delete_paths,
        )

        log_api("<< commit_manifest response: %s", commit_response)

        return commit_response
