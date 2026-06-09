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
        
        # Optional: check token scopes on init
        self._check_token_scopes()

    def _check_token_scopes(self):
        """Check what permissions the token has and warn if missing."""
        resp = self.session.get(f"{self.base_url}/user")
        if resp.ok:
            scopes = resp.headers.get("X-OAuth-Scopes", "")
            if "repo" not in scopes and "public_repo" not in scopes:
                print("⚠️  Warning: Your token lacks 'repo' or 'public_repo' scope.")
                print("   You will not be able to create repositories.")
                print("   Generate a new token at: https://github.com/settings/tokens\n")

    def create_repository(self, name: str, description: str = "", private: bool = False) -> dict:
        url = f"{self.base_url}/user/repos"
        payload = {
            "name": name,
            "description": description,
            "private": private
        }
        resp = self.session.post(url, json=payload)
        
        if resp.status_code == 403:
            error_detail = resp.json().get("message", "")
            raise PermissionError(
                f"GitHub API returned 403 Forbidden: {error_detail}\n"
                "This usually means your token lacks 'repo' or 'public_repo' scope.\n"
                "Fix: Go to GitHub Settings → Developer settings → Personal access tokens\n"
                "     and generate a new token with the required scopes."
            )
        
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
    try:
        github_client = GitHubClient()
        
        # Get the authenticated user's username
        owner = github_client.session.get("https://api.github.com/user").json()['login']
        print(f"\n✅ Authenticated as: {owner}\n")
        
        while True:
            # Show menu
            print("=" * 40)
            print("1. 📋 List repositories")
            print("2. ✨ Create repository")
            print("3. 🗑️  Delete repository")
            print("4. 🚪 Exit")
            print("=" * 40)
            
            choice = input("\nChoose (1-4): ").strip()
            
            # List repositories
            if choice == '1':
                repos = github_client.list_repositories()
                if not repos:
                    print("\n   No repositories found.\n")
                else:
                    print(f"\n   Found {len(repos)} repositories:\n")
                    for repo in repos:
                        print(f"   • {repo['name']}")
                        print(f"     {repo['html_url']}\n")
            
            # Create repository
            elif choice == '2':
                name = input("\n   Repository name: ").strip()
                if name:
                    private = input("   Private? (y/n): ").strip().lower() == 'y'
                    confirm = input(f"\n   Create '{name}'? (y/n): ").strip().lower()
                    
                    if confirm == 'y':
                        try:
                            repo = github_client.create_repository(name, "", private)
                            print(f"\n    Created: {repo['html_url']}\n")
                        except Exception as e:
                            print(f"\n    Error: {e}\n")
                else:
                    print("\n    Name required.\n")
            
            # Delete repository
            elif choice == '3':
                repo_name = input("\n   Repository name to delete: ").strip()
                if repo_name:
                    confirm = input(f"\n   Type '{repo_name}' to confirm: ").strip()
                    if confirm == repo_name:
                        deleted = github_client.delete_repository(owner, repo_name)
                        if deleted:
                            print(f"\n    Deleted: {repo_name}\n")
                        else:
                            print(f"\n    Delete failed\n")
                    else:
                        print("\n    Cancelled\n")
                else:
                    print("\n    Name required.\n")
            
            # Exit
            elif choice == '4':
                print("\n Goodbye!\n")
                break
            
            else:
                print("\n    Invalid choice\n")
                
    except Exception as e:
        print(f"\n Error: {e}\n")