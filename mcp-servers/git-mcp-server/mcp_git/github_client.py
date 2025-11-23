# mcp-servers/git-mcp-server/mcp_git/github_client.py
from __future__ import annotations

from typing import List, Dict, Any, Optional

import base64
import httpx

from .utils import get_required_env


class GitHubClient:

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 15.0,
    ) -> None:
        self.token = token or get_required_env("GITHUB_TOKEN")
        self.base_url = base_url or get_required_env(
            "GITHUB_API_BASE_URL",
            default="https://api.github.com",
        ).rstrip("/")

        self.client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=timeout,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        extra_headers = headers or {}
        # Merge headers (extra overrides default)
        request_headers = {**self.client.headers, **extra_headers}
        resp = self.client.request(
            method=method.upper(),
            url=path,
            params=params or {},
            headers=request_headers,
        )
        resp.raise_for_status()
        return resp

    def _get_json(
        self,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any] | List[Any]:
        """
        Convenience wrapper around GET returning JSON.
        """
        resp = self._request("GET", path, params=params, headers=headers)
        return resp.json()

    def get_repo(
        self,
        owner: str,
        repo: str,
    ) -> Dict[str, Any]:
        """
        Get repository metadata.
        """
        return self._get_json(f"/repos/{owner}/{repo}")  # type: ignore[return-value]

    def get_default_branch(
        self,
        owner: str,
        repo: str,
    ) -> str:
        """
        Return repository default branch name.
        """
        data = self.get_repo(owner, repo)
        default_branch = data.get("default_branch")  # type: ignore[assignment]
        if not isinstance(default_branch, str):
            raise RuntimeError(
                f"Repository {owner}/{repo} does not expose a default_branch field."
            )
        return default_branch

    def get_file_contents(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None,
    ) -> str:
        params: Dict[str, Any] = {}
        if ref:
            params["ref"] = ref

        data = self._get_json(
            f"/repos/{owner}/{repo}/contents/{path}",
            params=params,
        )
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected response type when fetching file content.")

        encoded = data.get("content")
        encoding = data.get("encoding")
        if not isinstance(encoded, str) or encoding != "base64":
            raise RuntimeError("Unsupported content encoding from GitHub API.")

        raw_bytes = base64.b64decode(encoded)
        # GitHub usually stores text files in UTF-8
        return raw_bytes.decode("utf-8", errors="replace")

    def get_pull_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        per_page: int = 100,
    ) -> List[Dict[str, Any]]:
        page = 1
        files: List[Dict[str, Any]] = []

        while True:
            data = self._get_json(
                f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
                params={"per_page": per_page, "page": page},
            )
            if not isinstance(data, list):
                raise RuntimeError("Unexpected response type for PR files.")

            if not data:
                break

            for item in data:
                if not isinstance(item, dict):
                    continue
                files.append(
                    {
                        "filename": item.get("filename"),
                        "status": item.get("status"),
                        "additions": item.get("additions"),
                        "deletions": item.get("deletions"),
                        "changes": item.get("changes"),
                        "blob_url": item.get("blob_url"),
                        "raw_url": item.get("raw_url"),
                        # `patch` contains unified diff for this file (may be large)
                        "patch": item.get("patch"),
                    }
                )

            if len(data) < per_page:
                # Last page
                break

            page += 1

        return files

    def get_pull_diff(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> str:
        resp = self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        return resp.text

    def close(self) -> None:
        self.client.close()