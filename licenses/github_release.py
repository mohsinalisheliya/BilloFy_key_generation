import os
import requests
# pyrefly: ignore [missing-import]
from .models import SiteSetting


def push_to_github(version, title, notes, file_path):
    settings_obj = SiteSetting.load()
    token = settings_obj.github_token
    repo = settings_obj.github_repo

    if not token:
        return False, "GitHub token not configured. Add it in Settings page."
    if not repo:
        return False, "GitHub repo not configured. Add it in Settings page."

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        r = requests.post(
            f"https://api.github.com/repos/{repo}/releases",
            headers=headers,
            json={
                "tag_name": f"v{version}",
                "name": title,
                "body": notes or "No release notes provided.",
                "draft": False,
                "prerelease": False
            },
            timeout=15
        )

        if r.status_code == 401:
            return False, "GitHub token invalid or expired. Please update it in Settings."
        if r.status_code not in (200, 201):
            return False, f"Release creation failed: {r.status_code} - {r.text}"

        release_data = r.json()
        upload_url = release_data['upload_url'].split('{')[0]

        filename = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            upload_r = requests.post(
                f"{upload_url}?name={filename}",
                headers={**headers, "Content-Type": "application/octet-stream"},
                data=f,
                timeout=120
            )

        if upload_r.status_code not in (200, 201):
            return False, f"Asset upload failed: {upload_r.status_code} - {upload_r.text}"

        download_url = upload_r.json().get('browser_download_url')
        if not download_url:
            return False, "Upload succeeded but no download URL returned."

        return True, download_url

    except requests.exceptions.RequestException as e:
        return False, f"Network error: {str(e)}"