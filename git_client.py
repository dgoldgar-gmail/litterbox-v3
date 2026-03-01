import logging
from git import Repo, GitCommandError
from threading import Lock

logger = logging.getLogger(__name__)

class GitClient:
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self._lock = Lock()

        if self.repo.bare:
            raise Exception(f"Repo at {repo_path} is bare or invalid.")

    # 0. Tell me what branch I'm on
    @property
    def current_branch(self):
        return self.repo.active_branch.name

    def get_status(self):
        status = {
            "branch": self.repo.active_branch.name,
            "is_dirty": self.repo.is_dirty(),
            "untracked": self.repo.untracked_files,
            "unstaged": [],
            "staged": [],
            "staged_diff": "",
            "unstaged_diff": ""
        }

        output = self.repo.git.diff("--name-status", "-M")
        for line in output.splitlines():
            parts = line.split("\t")
            change_type = parts[0]
            if change_type.startswith("R"):
                status["unstaged"].append(f"R: {parts[1]} -> {parts[2]}")
            else:
                status["unstaged"].append(f"{change_type}: {parts[1]}")

        output = self.repo.git.diff("--cached", "--name-status", "-M")
        for line in output.splitlines():
            parts = line.split("\t")
            change_type = parts[0]
            if change_type.startswith("R"):
                status["staged"].append(f"R: {parts[1]} -> {parts[2]}")
            else:
                status["staged"].append(f"{change_type}: {parts[1]}")

        status["unstaged_diff"] = self.repo.git.diff("HEAD")
        status['staged_diff'] = self.repo.git.diff("--cached")

        return status

    # 2. Diff with upstream ( find staged changes )
    def get_upstream_diff(self):
        tracking_branch = self.repo.active_branch.tracking_branch()
        if not tracking_branch:
            return ["No upstream branch configured."]

        # Using raw git for reliability
        output = self.repo.git.diff(
            tracking_branch.commit,
            name_status=True,
            cached=True
        )

        summary = []

        for line in output.splitlines():
            parts = line.split("\t")
            change_type = parts[0]
            if change_type.startswith("R"):
                # Renamed: just treat as "M" for display purposes
                new_path = parts[2]
                summary.append(f"M: {new_path}")
            else:
                path = parts[1]
                summary.append(f"{change_type}: {path}")

        return summary

    # 3. Add files
    def add(self, files=None):
        """files can be a string, a list of strings, or None (adds all)."""
        with self._lock:
            if files:
                self.repo.index.add(files)
            else:
                self.repo.git.add(A=True) # git add .

    # 4. Commit
    def commit(self, message, files=None):
        """Commit specific files. If files is None, commit everything staged."""
        with self._lock:
            try:
                if files:
                    # Stage only the specified files first
                    self.repo.index.add(files)
                new_commit = self.repo.index.commit(message)
                logger.info(f"Committed: {new_commit.hexsha}")
                return new_commit
            except Exception as e:
                logger.error(f"Commit failed: {e}")
                return None

    # 5. Push
    def push(self):
        with self._lock:
            origin = self.repo.remote(name='origin')
            info = origin.push()
            return info

    # 6. Switch branch
    def switch_branch(self, branch_name, create=False):
        logger.info(f"Switching to branch: {branch_name}")
        with self._lock:
            if create and branch_name not in self.repo.branches:
                self.repo.git.checkout('-b', branch_name)
            else:
                self.repo.heads[branch_name].checkout()

    # 7. Revert files (checkout)
    def revert_files(self, files):
        """Reverts specific files to their state in HEAD."""
        with self._lock:
            self.repo.git.checkout('HEAD', '--', files)

    # 8. Pull
    def pull(self):
        with self._lock:
            origin = self.repo.remote(name='origin')
            origin.pull()

    # 9. Reset to HEAD
    def reset_to_head(self, hard=False):
        """Resets the index. If hard=True, discards all local changes."""
        with self._lock:
            if hard:
                self.repo.git.reset('--hard', 'HEAD')
            else:
                self.repo.git.reset('HEAD')

    # 10. Force Push
    def force_push(self):
        """Force pushes the current branch to origin."""
        with self._lock:
            try:
                origin = self.repo.remote(name='origin')
                # Use 'force=True' or '+' prefix in refspec
                info = origin.push(force=True)
                logger.warning(f"Force pushed {self.current_branch} to origin")
                return info
            except GitCommandError as e:
                logger.error(f"Force push failed: {e}")
                raise

    # 11. Rebase to <branch_name>
    def rebase(self, upstream_branch="main"):
        """Rebases current branch onto the specified upstream branch."""
        with self._lock:
            try:
                logger.info(f"Rebasing {self.current_branch} onto {upstream_branch}")
                # We use the git object directly for rebase commands
                self.repo.git.rebase(upstream_branch)
                return True
            except GitCommandError as e:
                logger.error(f"Rebase conflict or failure: {e}")
                # Optional: self.repo.git.rebase('--abort')
                raise

    # 12. Squash Commits
    def squash_since_divergence(self, base_branch="main", message="Squashed commit"):
        """
        Finds the common ancestor with base_branch and squashes
        all local commits into a single new commit.
        """
        with self._lock:
            try:
                # Find the 'merge-base' (where we diverged)
                common_ancestor = self.repo.merge_base(self.repo.active_branch, base_branch)[0]

                # Soft reset moves HEAD back to ancestor but keeps changes in staging
                self.repo.git.reset('--soft', common_ancestor.hexsha)

                # Commit the staged changes as one single block
                return self.commit(message)
            except Exception as e:
                logger.error(f"Squash failed: {e}")
                raise

    # 12. Get unpushed commits
    def get_unpushed_commits(self):
            """Returns a list of commit objects that are local but not on remote."""
            with self._lock:
                active_branch = self.repo.active_branch
                tracking_branch = active_branch.tracking_branch()

                if not tracking_branch:
                    logger.warning(f"Branch {active_branch.name} has no upstream.")
                    return []

                # Range syntax: 'origin/main..main'
                rev_range = f"{tracking_branch.name}..{active_branch.name}"

                try:
                    # Returns a list of commit objects
                    commits = list(self.repo.iter_commits(rev_range))

                    # If you just want the messages/shas for logging:
                    for c in commits:
                        logger.info(f"Unpushed: {c.hexsha[:7]} - {c.summary}")

                    return commits
                except GitCommandError:
                    return []


def do_test(client):
    print(f"\nCurrent branch: {client.current_branch}")
    print(f"status -> {client.get_status()}")
    print(f"upstream diff -> {client.get_upstream_diff()}")
    print(f"unpushed commits -> {client.get_unpushed_commits()}")

"""
client = GitClient(".")
do_test(client)
"""
