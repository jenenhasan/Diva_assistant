class GitHubHandler:
    def __init__(self, dialog, github_service):
        self.dialog = dialog
        self.github = github_service

    def register(self, router):
        router.register(r"github|git hub", self.handle_github_menu)
        router.register(r"list repos|show my repositories", self.handle_list_repos)
        router.register(r"upload project", self.handle_upload_project)
        router.register(r"commit changes", self.handle_commit_changes)
        router.register(r"merge branches", self.handle_merge_branches)
        router.register(r"delete repo", self.handle_delete_repo)
        return self

    
    
    def handle_list_repos(self):
        """List all repositories."""
        self.dialog.show_thinking()
        result = self.github.list_repositories()
        self.dialog.hide_thinking()
        
        if isinstance(result, dict) and "error" in result:
            self.dialog.speak(f"Error: {result['error']}")
            return
        
        if not result:
            self.dialog.speak("No repositories found.")
            return
        
        self.dialog.speak(f"You have {len(result)} repositories.")
        for repo in result[:5]:  # Limit to first 5
            self.dialog.speak(f"{repo['name']}: {repo['description']}")
        if len(result) > 5:
            self.dialog.speak(f"And {len(result) - 5} more.")
    
    def handle_access_repo(self):
        """Access repository contents."""
        repo_name = self.dialog.listen_with_retry("Which repository would you like to access?")
        if not repo_name:
            return
        
        self.dialog.show_thinking()
        result = self.github.get_repository_contents(repo_name)
        self.dialog.hide_thinking()
        
        if isinstance(result, dict) and "error" in result:
            self.dialog.speak(f"Error: {result['error']}")
            return
        
        self.dialog.speak(f"Contents of repository:")
        for item in result[:10]:
            self.dialog.speak(f"- {item}")
        if len(result) > 10:
            self.dialog.speak(f"And {len(result) - 10} more items.")
    
    def handle_delete_repo(self):
        """Delete a repository."""
        repo_name = self.dialog.listen_with_retry(
            "Which repository would you like to delete? Please confirm the name.",
            "Please say the repository name again."
        )
        if not repo_name:
            return
        
        if not self.dialog.confirm(f"Are you sure you want to delete '{repo_name}'? This cannot be undone."):
            self.dialog.speak("Deletion cancelled.")
            return
        
        self.dialog.show_thinking()
        result = self.github.delete_repository(repo_name)
        self.dialog.hide_thinking()
        
        if result["success"]:
            self.dialog.speak(result["message"])
        else:
            self.dialog.speak(f"Failed to delete repository: {result['error']}")
    
    def handle_upload_project(self):
        """Upload a local project to a new repository."""
        repo_name = self.dialog.listen_with_retry("What should the repository be called?")
        if not repo_name:
            return
        
        description = self.dialog.listen_with_retry("Please say a short description.")
        if not description:
            description = ""
        
        folder_path = self.dialog.listen_with_retry("Please say the folder path to upload.")
        if not folder_path:
            return
        
        self.dialog.show_thinking()
        result = self.github.upload_project(repo_name, description, folder_path)
        self.dialog.hide_thinking()
        
        if result["success"]:
            self.dialog.speak(f"Project '{repo_name}' uploaded successfully.")
            if result.get("log"):
                self.dialog.speak(f"Uploaded {len(result['log'])} files.")
        else:
            self.dialog.speak(f"Upload failed: {result['error']}")
    
    def handle_commit_changes(self):
        """Commit local changes to a repository."""
        repo_name = self.dialog.listen_with_retry("Enter the repository name (e.g., username/reponame):")
        if not repo_name:
            return
        
        folder_path = self.dialog.listen_with_retry("Enter the local folder path to commit:")
        if not folder_path:
            return
        
        commit_message = self.dialog.listen_with_retry("Enter the commit message:")
        if not commit_message:
            commit_message = "Voice assistant commit"
        
        branch_name = self.dialog.listen_with_retry("Enter the branch name (default is main):")
        if not branch_name:
            branch_name = "main"
        
        self.dialog.show_thinking()
        result = self.github.commit_changes(repo_name, folder_path, commit_message, branch_name)
        self.dialog.hide_thinking()
        
        if result["success"]:
            self.dialog.speak(result["message"])
        else:
            self.dialog.speak(f"Commit failed: {result['error']}")
    
    def handle_merge_branches(self):
        """Merge branches in a repository."""
        repo_name = self.dialog.listen_with_retry("Enter the repository name (e.g., username/reponame):")
        if not repo_name:
            return
        
        base_branch = self.dialog.listen_with_retry("Enter the base branch to merge INTO (e.g., main):")
        if not base_branch:
            return
        
        head_branch = self.dialog.listen_with_retry("Enter the branch to merge FROM:")
        if not head_branch:
            return
        
        self.dialog.show_thinking()
        result = self.github.merge_branches(repo_name, base_branch, head_branch)
        self.dialog.hide_thinking()
        
        if result["success"]:
            self.dialog.speak(result["message"])
        else:
            self.dialog.speak(f"Merge failed: {result['error']}")
    
    def handle_github_menu(self):
        """Main menu for GitHub commands (voice-driven)."""
        self.dialog.speak("What would you like to do with GitHub?")
        self.dialog.speak("You can say: list repositories, access repository, delete repository, upload project, commit changes, or merge branches.")
        
        choice = self.dialog.listen_with_retry("What would you like to do?")
        if not choice:
            return
        
        if "list" in choice:
            self.handle_list_repos()
        elif "access" in choice:
            self.handle_access_repo()
        elif "delete" in choice:
            self.handle_delete_repo()
        elif "upload" in choice:
            self.handle_upload_project()
        elif "commit" in choice:
            self.handle_commit_changes()
        elif "merge" in choice:
            self.handle_merge_branches()
        else:
            self.dialog.speak("I didn't understand that GitHub command.")


if __name__ == "__main__":
    from unittest.mock import MagicMock
    
    # Mock DialogManager
    class MockDialog:
        def __init__(self):
            self.responses = []
            self.response_index = 0
        
        def speak(self, text):
            print(f"[ASSISTANT] {text}")
        
        def listen_with_retry(self, prompt=None, retry_prompt=None):
            if self.response_index < len(self.responses):
                ans = self.responses[self.response_index]
                self.response_index += 1
                return ans
            return ""
        
        def show_thinking(self):
            print("[THINKING...]")
        
        def hide_thinking(self):
            print("[DONE]")
        
        def confirm(self, question):
            print(f"[CONFIRM] {question}")
            return True
    
    # Mock GitHubService
    class MockGitHubService:
        def list_repositories(self):
            return [{"name": "test-repo", "description": "Test repository", "url": "https://github.com/test/test-repo"}]
        
        def get_repository_contents(self, name):
            return ["README.md", "src/main.py"]
        
        def delete_repository(self, name):
            return {"success": True, "message": f"Repository '{name}' deleted"}
        
        def upload_project(self, name, desc, path):
            return {"success": True, "log": ["Uploaded file1.py", "Uploaded file2.py"]}
        
        def commit_changes(self, repo, path, msg, branch):
            return {"success": True, "message": f"Committed to {branch}", "sha": "abc123"}
        
        def merge_branches(self, repo, base, head):
            return {"success": True, "message": f"Merged {head} into {base}"}
    
    # Test
    print("\n🧪 TESTING GitHubHandler\n")
    mock_dialog = MockDialog()
    mock_dialog.responses = ["list repositories"]
    
    mock_service = MockGitHubService()
    handler = GitHubHandler(mock_dialog, mock_service)
    handler.handle_github_menu()