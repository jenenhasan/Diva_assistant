import unittest
from integrations.github_client import GitHubClient
import time 
import sys
import os 
#this will add the  integrations folder to the python path 
# sys.path.insert(0 , os.path.abspath(os.path.join(os.path.dirname(__file__) , '../integrations')))
class TestGithubClient(unittest.TestCase):
    def setUp(self):
        self.client= GitHubClient()
        self.owner = self.client.session.get(            
            "https://api.github.com/user"
        ).json()['login']

        self.test_repo = f"test-repo-{int(time.time())}"
    # just so i clean every thing
    def tearDown(self):
        try : 
            self.client.delete_repository(self.owner , self.test_repo)

        except : 
            pass
    def test_create_public_repo(self):
        repo = self.client.create_repository(
            self.test_repo, 
            "Test repo", 
            private=False
        )
        self.assertEqual(repo['name'], self.test_repo)
        self.assertEqual(repo['private'], False)
        self.assertIn('html_url', repo)

    def test_create_private_repo(self):
        repo = self.client.create_repository(
            f"{self.test_repo}-private", 
            'Private test' , 
            private=True

        )
        self.assertTrue(repo['private'])
    def test_create_duplicate_repository_fails(self):
        self.client.create_repository(self.test_repo , "First")
        with self.assertRaises(Exception):
            self.client.create_repository(self.test_repo , "Duplicate")

    def test_delete_repo_success(self):
        self.client.create_repository(self.test_repo , "To delete")
        result = self.client.delete_repository(self.owner , self.test_repo)
        self.assertTrue(result)

    def test_delete_nonexistance_repo_returns_false(self):
        result = self.client.delete_repository(
            self.owner , 
            "defenitly-does-not-exist-12345"
        )
        self.assertFalse(result)
    def test_list_repo_return_list(self):
        repos = self.client.list_repositories()
        self.assertIsInstance(repos , list)
        if len(repos) > 0 : 
            self.assertIn('name' , repos[0])
            self.assertIn('html_url' , repos[0])

if __name__ == '__main__': 
    unittest.main(verbosity=2)



