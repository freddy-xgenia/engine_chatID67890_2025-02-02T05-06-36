import json
import logging
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

import dotenv
import pathspec
import requests
from fastapi import APIRouter, HTTPException

# load environment variables
dotenv.load_dotenv(verbose=True)
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN", "")
GITHUB_USER_REPO_API_URL = os.getenv("GITHUB_USER_REPO_API_URL", "")
GITHUB_REPO_API_URL = os.getenv("GITHUB_REPO_API_URL", "")

# router for the sandbox
sandbox_router = APIRouter()

# Logging setup
logger = logging.getLogger(__name__)


base_path = Path(__file__).resolve().parents[1]


def load_gitignore_patterns():
    gitignore_path = base_path / ".gitignore"
    if not gitignore_path.exists():
        return pathspec.PathSpec.from_lines("gitwildmatch", [])

    with open(gitignore_path, "r") as f:
        lines = f.readlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def get_dict_file_n_content(path: Path = base_path) -> Dict[str, str]:
    dict_file_n_content = {}
    spec = load_gitignore_patterns()
    for item in path.iterdir():
        if not spec.match_file(item.name):
            if item.is_file():
                with open(item, "r") as file:
                    item_relative_path = item.relative_to(base_path)
                    dict_file_n_content[str(item_relative_path)] = file.read()
            elif item.is_dir():
                dict_file_n_content.update(get_dict_file_n_content(item))
    return dict_file_n_content


@sandbox_router.get(
    "/create_sandbox/{chat_id}",
    summary="Create a CodeSandbox and return its URL",
)
async def create_sandbox(chat_id: str):
    try:
        ### Create new github repo ###
        github_headers = {
            "Authorization": f"token {GITHUB_API_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        datetime_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
        github_repo_name = f"engine_{chat_id}_{datetime_str}"
        github_payload = {
            "name": github_repo_name,
            "description": f"Repo created using Github API at {datetime_str}",
            "private": False,
            "auto_init": True,
        }

        github_response = requests.post(
            url=GITHUB_USER_REPO_API_URL,
            headers=github_headers,
            json=github_payload,
        )
        github_repo_owner = github_response.json()["owner"]["login"]
        github_repo_url = github_response.json()["html_url"]

        ### Check latest commit sha ###
        github_sha_response = requests.get(
            url=f"{GITHUB_REPO_API_URL}/{github_repo_owner}/{github_repo_name}/commits/main",
            headers=github_headers,
        )
        commit_sha = github_sha_response.json()["sha"]

        ### Create new tree for commit ###
        tree_data = []
        for file_path, content in get_dict_file_n_content().items():
            tree_data.append(
                {
                    "path": file_path,
                    "mode": "100644",  # (100644 for a normal file)
                    "type": "blob",
                    "content": content,
                }
            )

        github_tree_payload = {
            "base_tree": commit_sha,
            "tree": tree_data,
        }

        github_tree_response = requests.post(
            url=f"{GITHUB_REPO_API_URL}/{github_repo_owner}/{github_repo_name}/git/trees",
            headers=github_headers,
            data=json.dumps(github_tree_payload),
        )
        tree_sha = github_tree_response.json()["sha"]

        ### Create new commit ###
        github_commit_payload = {
            "message": "Initial engine and plugins commit",
            "parents": [commit_sha],
            "tree": tree_sha,
        }

        github_commit_response = requests.post(
            url=f"{GITHUB_REPO_API_URL}/{github_repo_owner}/{github_repo_name}/git/commits",
            headers=github_headers,
            data=json.dumps(github_commit_payload),
        )
        new_commit_sha = github_commit_response.json()["sha"]

        ### Update the main branch with the new commit ###
        github_push_payload = {
            "sha": new_commit_sha,
            "force": True,
        }
        github_push_response = requests.patch(
            url=f"{GITHUB_REPO_API_URL}/{github_repo_owner}/{github_repo_name}/git/refs/heads/main",
            headers=github_headers,
            data=json.dumps(github_push_payload),
        )

        return {
            "status_code": github_push_response.status_code,
            "codesandbox_url": f"https://codesandbox.io/p/github/{github_repo_owner}/{github_repo_name}/main?import=true",
            "github_repo_url": github_repo_url,
        }

    except Exception as e:
        logger.error(e)
        raise e
    # except urllib.error.HTTPError as e:
    #     logger.error("HTTP Error: %s - %s", e.code, e.reason)
    #     raise HTTPException(status_code=e.code, detail=f"HTTP Error: {e.reason}")
    # except urllib.error.URLError as e:
    #     logger.error("Failed to create sandbox: %s", e.reason)
    #     raise HTTPException(
    #         status_code=500, detail=f"Failed to create sandbox: {e.reason}"
    #     )
