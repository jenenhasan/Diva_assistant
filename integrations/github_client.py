import os
import requests
from dotenv import load_dotenv
load_dotenv()

class GitHubClient:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GitHub token required")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        })
        self.base_url = "https://api.github.com"

    def create_repository(self, name: str, description: str = "", private: bool = False) -> dict:
        url = f"{self.base_url}/user/repos"
        resp = self.session.post(url, json={"name": name, "description": description, "private": private})
        resp.raise_for_status()
        return resp.json()

    def list_repositories(self, username: str = None) -> list:
        if username:
            url = f"{self.base_url}/users/{username}/repos"
        else:
            url = f"{self.base_url}/user/repos"
        resp = self.session.get(url)
        resp.raise_for_status()
        return resp.json()

    def delete_repository(self, owner: str, repo: str) -> bool:
        url = f"{self.base_url}/repos/{owner}/{repo}"
        resp = self.session.delete(url)
        return resp.status_code == 204

    def create_file(self, owner: str, repo: str, path: str, content: str, commit_message: str, branch: str = "main") -> dict:
        # content should be base64 encoded string
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        payload = {
            "message": commit_message,
            "content": content,
            "branch": branch
        }
        resp = self.session.put(url, json=payload)
        resp.raise_for_status()
        return resp.json()
    

if __name__ == '__main__':
    github_client = GitHubClient()
    repos = github_client.list_repositories()
    print(f"Found {len(repos)} repositories")