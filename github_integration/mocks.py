"""
MockPRData - Testing without real GitHub API calls

Provides realistic mock data for unit tests and local development.
"""

from typing import List
from .pr_fetcher import PRData, FileChange
from tasks.format_comments_task import GitHubReview


class MockPRData:
    """Mock GitHub PR data for testing."""
    
    @staticmethod
    def get_sample_pr(pr_number: int = 123) -> PRData:
        """
        Get a realistic sample PR with intentional code issues.
        
        Args:
            pr_number: PR number to use
            
        Returns:
            PRData with 3 files containing various code smells
        """
        # File 1: Python with security issue
        file1 = FileChange(
            filename="app/auth.py",
            patch="""@@ -1,10 +1,15 @@
 import os
+import requests
 
 def authenticate_user(username, password):
-    # TODO: Implement proper authentication
-    return True
+    # Hardcoded credentials - SECURITY ISSUE
+    API_KEY = "sk-1234567890abcdef"
+    
+    response = requests.post(
+        "https://api.example.com/auth",
+        headers={"Authorization": f"Bearer {API_KEY}"},
+        json={"username": username, "password": password}
+    )
+    return response.status_code == 200
""",
            language="python",
            additions=10,
            deletions=2,
            status="modified"
        )
        
        # File 2: JavaScript with performance issue
        file2 = FileChange(
            filename="frontend/utils.js",
            patch="""@@ -5,8 +5,18 @@
 
 function findUserById(users, targetId) {
-    return users.find(user => user.id === targetId);
+    // O(n²) nested loop - PERFORMANCE ISSUE
+    for (let i = 0; i < users.length; i++) {
+        for (let j = 0; j < users.length; j++) {
+            if (users[i].id === targetId) {
+                return users[i];
+            }
+        }
+    }
+    return null;
 }
""",
            language="javascript",
            additions=10,
            deletions=1,
            status="modified"
        )
        
        # File 3: Python with code smell
        file3 = FileChange(
            filename="services/user_service.py",
            patch="""@@ -1,5 +1,25 @@
 class UserService:
-    def get_user(self, user_id):
-        pass
+    def get_user(self, user_id):
+        # God class - SRP violation
+        user = self.db.query(user_id)
+        self.send_email(user.email)
+        self.log_access(user_id)
+        self.update_analytics(user_id)
+        self.check_permissions(user_id)
+        return user
+    
+    def send_email(self, email):
+        pass
+    
+    def log_access(self, user_id):
+        pass
+    
+    def update_analytics(self, user_id):
+        pass
+    
+    def check_permissions(self, user_id):
+        pass
""",
            language="python",
            additions=20,
            deletions=2,
            status="modified"
        )
        
        # Combine files
        files_changed = [file1, file2, file3]
        
        # Create full diff
        full_diff = f"""diff --git a/app/auth.py b/app/auth.py
--- a/app/auth.py
+++ b/app/auth.py
{file1.patch}

diff --git a/frontend/utils.js b/frontend/utils.js
--- a/frontend/utils.js
+++ b/frontend/utils.js
{file2.patch}

diff --git a/services/user_service.py b/services/user_service.py
--- a/services/user_service.py
+++ b/services/user_service.py
{file3.patch}
"""
        
        return PRData(
            repo_name="test-org/test-repo",
            pr_number=pr_number,
            pr_url=f"https://github.com/test-org/test-repo/pull/{pr_number}",
            title="Add user authentication and utilities",
            author="test-developer",
            files_changed=files_changed,
            full_diff=full_diff
        )
    
    @staticmethod
    def get_flawed_pr_diff() -> str:
        """
        Get a diff with multiple intentional flaws for testing.
        
        Returns:
            Unified diff string with code issues
        """
        return """diff --git a/vulnerable.py b/vulnerable.py
--- a/vulnerable.py
+++ b/vulnerable.py
@@ -1,5 +1,15 @@
+import pickle
+import os
+
 def process_data(user_input):
-    return user_input.strip()
+    # CRITICAL: Pickle deserialization vulnerability
+    data = pickle.loads(user_input)
+    
+    # CRITICAL: SQL injection vulnerability
+    query = f"SELECT * FROM users WHERE id = {data['user_id']}"
+    
+    # HIGH: Hardcoded secret
+    SECRET_KEY = "super-secret-key-12345"
+    
+    return query
"""
    
    @staticmethod
    def simulate_pr_comments(repo: str, pr_number: int) -> None:
        """
        Simulate posting comments (print to console instead of API call).
        
        Args:
            repo: Repository name
            pr_number: PR number
        """
        print(f"\n{'='*60}")
        print(f"SIMULATED PR REVIEW: {repo}#{pr_number}")
        print(f"{'='*60}\n")
        
        comments = [
            {
                "path": "app/auth.py",
                "line": 6,
                "body": "🔴 CRITICAL: Hardcoded API key detected. Move to environment variables."
            },
            {
                "path": "frontend/utils.js",
                "line": 9,
                "body": "🟡 HIGH: O(n²) nested loop. Use Array.find() or Map for O(n) lookup."
            },
            {
                "path": "services/user_service.py",
                "line": 4,
                "body": "🟠 MEDIUM: God class detected. Extract email, logging, and analytics to separate services (SRP)."
            }
        ]
        
        for comment in comments:
            print(f"📍 {comment['path']}:L{comment['line']}")
            print(f"   {comment['body']}\n")
        
        print(f"{'='*60}")
        print("✅ Review simulation complete")
        print(f"{'='*60}\n")
    
    @staticmethod
    def get_sample_github_review() -> GitHubReview:
        """
        Get a sample GitHubReview object for testing.
        
        Returns:
            GitHubReview with inline comments and summary
        """
        return GitHubReview(
            inline_comments=[
                {
                    "path": "app/auth.py",
                    "line": "6",
                    "body": "CRITICAL: Hardcoded API key 'sk-1234567890abcdef' detected on line 6. This is a security vulnerability. Move secrets to environment variables using python-dotenv or a secrets manager."
                },
                {
                    "path": "frontend/utils.js",
                    "line": "9",
                    "body": "HIGH: O(n²) time complexity detected in nested loops (lines 9-14). Replace with Array.find() or use a Map for O(n) lookup performance."
                },
                {
                    "path": "services/user_service.py",
                    "line": "4",
                    "body": "MEDIUM: Single Responsibility Principle violation. UserService has too many responsibilities (database, email, logging, analytics, permissions). Extract these into separate service classes."
                }
            ],
            summary_comment="""Found 3 issues requiring attention:
- 1 CRITICAL security issue (hardcoded credentials)
- 1 HIGH performance issue (O(n²) complexity)
- 1 MEDIUM design issue (SRP violation)

Please address the critical security issue before merging.""",
            review_state="REQUESTED_CHANGES"
        )
