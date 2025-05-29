from __future__ import annotations

import base64
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field
from strif import hash_file
from typing_extensions import override

from textpress.api.textpress_env import ApiConfig, get_api_config

if TYPE_CHECKING:
    from httpx import Client, Response

log = logging.getLogger(__name__)


# Debug logging for API calls.
log_api = log.debug


class Route(Enum):
    """
    Textpress API routes.
    """

    user = "/api/user"
    sync_manifest = "/api/sync/manifest"
    sync_presign_batch = "/api/sync/presign-batch"
    sync_commit = "/api/sync/commit"

    def _route_url(self, api_root: str) -> str:
        return f"{api_root}{self.value}"

    @override
    def __str__(self):
        return self.value

    def get(self, config: ApiConfig, params: dict[str, Any] | None = None) -> Response:
        from textpress.api.http_client import get_http_client

        client = get_http_client()
        url = self._route_url(config.api_root)
        headers = {"x-api-key": config.api_key}
        log_api(">> GET %s - headers: %s - params: %s", url, headers, params)
        response = client.get(url, headers=headers, params=params)
        log_api("<< GET %s - response: %s", url, response)

        response.raise_for_status()
        return response

    def post(self, config: ApiConfig, json_data: dict[str, Any]) -> Response:
        from textpress.api.http_client import get_http_client

        client = get_http_client()
        url = self._route_url(config.api_root)
        headers = {
            "Content-Type": "application/json",
            "x-api-key": config.api_key,
        }
        log_api(">> POST %s - headers: %s - json: %s", url, headers, json_data)
        response = client.post(url, headers=headers, json=json_data)
        log_api("<< POST %s - response: %s", url, response)

        response.raise_for_status()
        return response


class UserProfileResponse(BaseModel):
    # TODO: Be consistent in api on snake_case vs camelCase.
    model_config = ConfigDict(populate_by_name=True)  # pyright: ignore

    user_id: str = Field(..., alias="userId")
    username: str


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
    uploads: list[PresignUploadInfo] = Field(default_factory=list)
    delete: list[DeleteFileMetadata] = Field(default_factory=list)
    base_version: int = Field(..., alias="baseVersion")


class ManifestResponse(BaseModel):
    version: int
    generated_at: datetime = Field(..., alias="generatedAt")
    files: dict[str, str]
    """Maps file path to MD5 hash."""


def get_manifest(config: ApiConfig) -> ManifestResponse:
    """
    Fetch the current manifest from the Textpress API.
    """
    response = Route.sync_manifest.get(config)
    return ManifestResponse.model_validate(response.json())


def get_user(config: ApiConfig) -> UserProfileResponse:
    """
    Fetch the user profile from the Textpress API.
    """
    response = Route.user.get(config)
    return UserProfileResponse.model_validate(response.json())


def get_presigned_urls(
    config: ApiConfig,
    base_version: int,
    files_to_upload: list[Path],
    files_to_delete: list[str] | None = None,
) -> PresignResponse:
    """
    Gets presigned URLs for uploading files.
    """
    from kash.utils.file_utils.file_formats_model import Format, detect_file_format

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

    request_data_json = presign_req.model_dump(by_alias=True, exclude_none=True)
    response = Route.sync_presign_batch.post(config=config, json_data=request_data_json)
    return PresignResponse.model_validate(response.json())


def upload_file(client: Client, file_path: Path, upload_info: dict[str, Any]) -> None:
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


def sync_commit(
    config: ApiConfig,
    base_version: int,
    uploaded_files_details: list[PresignUploadInfo],
    files_to_delete_paths: list[str] | None = None,
) -> ManifestResponse:
    """
    Commits the changes to the manifest.
    """
    if files_to_delete_paths is None:
        files_to_delete_paths = []

    uploads_metadata: list[UploadFileMetadata] = []
    for info in uploaded_files_details:
        # Convert base64 Content-MD5 back to hex to match presign format
        md5_hex = base64.b64decode(info.headers["Content-MD5"]).hex()

        uploads_metadata.append(
            UploadFileMetadata(
                path=info.path,
                md5=md5_hex,
                contentType=info.headers["Content-Type"],
            )
        )

    delete_metadata: list[DeleteFileMetadata] = [
        DeleteFileMetadata(path=p) for p in files_to_delete_paths
    ]

    commit_req = CommitRequest(
        baseVersion=base_version, uploads=uploads_metadata, delete=delete_metadata
    )
    request_data_json = commit_req.model_dump(by_alias=True, exclude_none=True)

    response = Route.sync_commit.post(config=config, json_data=request_data_json)

    return ManifestResponse.model_validate(response.json())


def publish_files(
    upload_paths: list[Path], delete_paths: list[str] | None = None
) -> ManifestResponse:
    """
    Publishes files (uploads and deletes) to Textpress.
    """
    from textpress.api.http_client import get_http_client

    config = get_api_config()

    if delete_paths is None:
        delete_paths = []

    manifest: ManifestResponse = get_manifest(config)
    log_api("<< get_manifest response: %s", manifest)

    presign_response: PresignResponse = get_presigned_urls(
        config, manifest.version, upload_paths, delete_paths
    )

    upload_info_map = {info.path: info for info in presign_response.uploads}

    upload_client = get_http_client()
    uploaded_files_details: list[PresignUploadInfo] = []
    for file_path in upload_paths:
        if file_path.name in upload_info_map:
            upload_info = upload_info_map[file_path.name]
            upload_file(upload_client, file_path, upload_info.model_dump())
            uploaded_files_details.append(upload_info)
        else:
            log_api(
                "File %s was requested for upload but not included in presign response (already up-to-date?)",
                file_path.name,
            )

    commit_response: ManifestResponse = sync_commit(
        config,
        manifest.version,
        uploaded_files_details,
        files_to_delete_paths=delete_paths,
    )

    return commit_response
