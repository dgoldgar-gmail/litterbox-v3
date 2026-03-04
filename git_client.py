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


    def _parse_name_status(self, output):
        """Helper to parse --name-status output into a readable list."""
        results = []
        for line in output.splitlines():
            if not line: continue
            parts = line.split("\t")
            change_type = parts[0]
            if change_type.startswith("R"):
                results.append(f"R: {parts[1]} -> {parts[2]}")
            else:
                results.append(f"{change_type}: {parts[1]}")
        return results

    def git_untracked(self):
        """Returns a list of files that are not yet tracked by Git."""
        # GitPython provides a built-in property for this
        return  self.repo.untracked_files

    def git_unstaged(self):
        """Returns a list of modified/deleted/added files in the working directory."""
        output = self.repo.git.diff("--name-status", "-M")
        return self._parse_name_status(output)

    def git_staged(self):
        """Returns a list of files currently in the index (staging area)."""
        output = self.repo.git.diff("--cached", "--name-status", "-M")
        return self._parse_name_status(output)

    def git_unstaged_diff(self):
        """Returns the actual diff text for unstaged changes."""
        return self.repo.git.diff()

    def git_staged_diff(self):
        """Returns the actual diff text for staged changes."""
        return self.repo.git.diff("--cached")

    def git_committed(self):
        """Returns files committed locally but not yet pushed to upstream."""
        # Compares current branch to its upstream tracking branch
        try:
            output = self.repo.git.diff("@{u}..HEAD", "--name-status", "-M")
            return self._parse_name_status(output)
        except Exception:
            return "No upstream branch found."

    def git_committed_diff(self):
        """Returns the diff text between local HEAD and upstream."""
        try:
            return self.repo.git.diff("@{u}..HEAD")
        except Exception:
            return "No upstream branch found."

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
