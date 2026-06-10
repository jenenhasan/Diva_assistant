import os
import base64
from pathlib import Path
from github import Github, GithubException
from github import InputGitTreeElement
from fuzzywuzzy import process
from dotenv import load_dotenv

load_dotenv()


class GitHubService:
    """Pure service for GitHub operations. No dialog, no speak/listen."""
    
    EXCLUDE = ['.git', '__pycache__', '.DS_Store', '.vscode', '.conda', 'node_modules']
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
        self.github = Github(self.token)
    
    @staticmethod
    def _should_exclude(path: Path) -> bool:
        """Check if a path should be excluded from upload."""
        return any(exclude in str(path) for exclude in GitHubService.EXCLUDE)
    
    def _get_user(self):
        """Get authenticated user."""
        return self.github.get_user()
    
    def list_repositories(self) -> list:
        """List all repositories for the authenticated user."""
        try:
            repos = list(self._get_user().get_repos())
            return [
                {
                    "name": repo.name,
                    "description": repo.description or "No description available",
                    "url": repo.html_url
                }
                for repo in repos
            ]
        except Exception as e:
            return {"error": str(e)}
    
    def get_repository_contents(self, repo_name: str) -> list:
        """Get contents of a repository at root level."""
        try:
            all_repos = [repo.full_name for repo in self._get_user().get_repos()]
            matched_repo = process.extractOne(repo_name, all_repos)
            
            if matched_repo and matched_repo[1] > 70:
                repo = self.github.get_repo(matched_repo[0])
                contents = repo.get_contents("")
                return [content.path for content in contents]
            else:
                return {"error": "Repository not found or couldn't match the name well enough."}
        except Exception as e:
            return {"error": str(e)}
    
    def delete_repository(self, repo_name: str) -> dict:
        """Delete a repository by name."""
        try:
            all_repos = [repo.full_name for repo in self._get_user().get_repos()]
            matched_repo = process.extractOne(repo_name, all_repos)
            
            if matched_repo and matched_repo[1] > 70:
                repo = self.github.get_repo(matched_repo[0])
                repo.delete()
                return {"success": True, "message": f"Repository '{matched_repo[0]}' deleted successfully."}
            else:
                return {"success": False, "error": "Repository not found or couldn't match the name well enough."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def upload_project(self, repo_name: str, description: str, folder_path: str) -> dict:
        """Upload a local project to a new GitHub repository."""
        try:
            project_dir = Path(folder_path.strip().replace("\\", "/")).resolve()
            if not project_dir.exists() or not project_dir.is_dir():
                return {"success": False, "error": f"Folder path '{folder_path}' does not exist or is not a directory."}
            
            user = self._get_user()
            
            try:
                new_repo = user.create_repo(repo_name, description=description)
            except GithubException as ge:
                if ge.status == 422 and "name already exists" in str(ge.data):
                    return {"success": False, "error": f"A repository named '{repo_name}' already exists."}
                return {"success": False, "error": ge.data.get("message", "Unknown error")}
            
            upload_log = []
            
            for file_path in project_dir.rglob("*"):
                if self._should_exclude(file_path):
                    continue
                
                if file_path.is_file():
                    relative_path = str(file_path.relative_to(project_dir))
                    
                    with open(file_path, "rb") as f:
                        content = f.read()
                    
                    try:
                        new_repo.get_contents(relative_path)
                        upload_log.append(f"Skipped '{relative_path}': Already exists.")
                        continue
                    except GithubException as ge:
                        if ge.status != 404:
                            return {"success": False, "error": f"File check failed: {ge.data.get('message', 'Unknown error')}"}
                    
                    try:
                        new_repo.create_file(relative_path, "Initial commit", content)
                        upload_log.append(f"Uploaded: {relative_path}")
                    except GithubException as ge:
                        return {"success": False, "error": f"Upload failed: {ge.data.get('message', 'Unknown error')}"}
            
            upload_log.append(f"Project '{repo_name}' uploaded successfully.")
            return {"success": True, "log": upload_log}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_or_create_branch(self, repo, branch_name, base_branch="main"):
        """Get existing branch or create from base branch."""
        try:
            return repo.get_branch(branch_name)
        except GithubException as e:
            if e.status == 404:
                base = repo.get_branch(base_branch)
                repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=base.commit.sha)
                return repo.get_branch(branch_name)
            raise
    
    def commit_changes(self, repo_name: str, local_dir: str, commit_message: str, branch_name: str = "main") -> dict:
        """Commit all changes from a local directory to a repository branch."""
        try:
            repo = self.github.get_repo(repo_name)
            branch = self._get_or_create_branch(repo, branch_name, base_branch="main")
            commit = repo.get_git_commit(branch.commit.sha)
            base_tree = commit.tree
            
            tree_elements = []
            
            for root, dirs, files in os.walk(local_dir):
                for file in files:
                    full_path = os.path.join(root, file)
                    if self._should_exclude(Path(full_path)):
                        continue
                    
                    rel_path = os.path.relpath(full_path, local_dir).replace("\\", "/")
                    with open(full_path, "rb") as f:
                        content = f.read()
                    
                    try:
                        text = content.decode("utf-8")
                        blob = repo.create_git_blob(text, "utf-8")
                    except UnicodeDecodeError:
                        encoded = base64.b64encode(content).decode("utf-8")
                        blob = repo.create_git_blob(encoded, "base64")
                    
                    tree_elements.append(InputGitTreeElement(
                        path=rel_path, mode="100644", type="blob", sha=blob.sha
                    ))
            
            new_tree = repo.create_git_tree(tree_elements, base_tree)
            new_commit = repo.create_git_commit(commit_message, new_tree, [commit])
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.edit(new_commit.sha)
            
            return {"success": True, "message": f"Batched commit to branch '{branch_name}': {commit_message}", "sha": new_commit.sha}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def merge_branches(self, repo_name: str, base_branch: str, head_branch: str, commit_message: str = None) -> dict:
        """Merge one branch into another."""
        try:
            repo = self.github.get_repo(repo_name)
            
            if base_branch == head_branch:
                return {"success": False, "error": "Cannot merge identical branches"}
            
            try:
                repo.get_branch(base_branch)
                repo.get_branch(head_branch)
            except GithubException as ge:
                if ge.status == 404:
                    return {"success": False, "error": f"Branch not found: {ge.data.get('message', 'Unknown branch')}"}
                raise
            
            merge_result = repo.merge(
                base=base_branch,
                head=head_branch,
                commit_message=commit_message or f"Merge {head_branch} into {base_branch}"
            )
            
            return {"success": True, "message": f"Merged successfully. Commit SHA: {merge_result.sha}"}
        
        except GithubException as ge:
            if ge.status == 409:
                return {"success": False, "error": "Merge conflict. Resolve manually in GitHub."}
            return {"success": False, "error": f"GitHub API error: {ge.data.get('message', str(ge))}"}
        except Exception as e:
            return {"success": False, "error": str(e)}