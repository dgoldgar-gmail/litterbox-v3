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

    def git_branch_changes(self, base_branch="main"):
        """
        Returns a list of files changed in the current branch
        since it diverged from the base_branch.
        """
        try:
            merge_base = self.repo.git.merge_base(base_branch, "HEAD")
            output = self.repo.git.diff(merge_base, "HEAD", "--name-status", "-M")

            return self._parse_name_status(output)
        except Exception as e:
            return f"Error comparing to {base_branch}: {str(e)}"

    def git_branch_diff(self, base_branch="main"):
        """
        Returns the full diff text for all changes in the current branch
        since it diverged from the base_branch.
        """
        try:
            merge_base = self.repo.git.merge_base(base_branch, "HEAD")
            return self.repo.git.diff(merge_base, "HEAD")
        except Exception as e:
            return f"Error generating diff from {base_branch}: {str(e)}"

    def add(self, files=None):
        """files can be a string, a list of strings, or None (adds all)."""
        with self._lock:
            if files:
                self.repo.index.add(files)
            else:
                self.repo.git.add(A=True) # git add .


    def commit(self, message, files=None, locked=False):
        """Commit specific files. If files is None, commit everything staged."""

        # Define the actual work in a helper or a nested function
        def perform_commit():
            try:
                if files:
                    self.repo.index.add(files)
                new_commit = self.repo.index.commit(message)
                logger.info(f"Committed: {new_commit.hexsha}")
                return new_commit
            except Exception as e:
                logger.error(f"Commit failed: {e}")
                return None

        # If already locked by the caller, just run it.
        # Otherwise, acquire the lock.
        if locked:
            return perform_commit()
        else:
            with self._lock:
                return perform_commit()

    def push(self, force=False):
        with self._lock:
            try:
                origin = self.repo.remote(name='origin')
                push_results = origin.push(force=force)
                parsed_results = []
                for info in push_results:
                    error = info.flags & (info.REJECTED | info.REMOTE_REJECTED | info.REMOTE_FAILURE)
                    parsed_results.append({
                        "branch": info.remote_ref_string,
                        "summary": info.summary.strip(),
                        "success": not bool(error),
                        "forced": bool(info.flags & info.FORCED_UPDATE) # Optional: track if it was actually a forced update
                    })
                return parsed_results
            except Exception as e:
                logger.error(f"Push failed: {e}")
                return [{"success": False, "summary": str(e), "branch": "unknown"}]

    def switch_branch(self, branch_name, create=False):
        """
        Switches the repository to a specified branch.
        Returns: True if successful, False/Error otherwise.
        """
        logger.info(f"Switching to branch: {branch_name}")

        with self._lock:
            try:
                # 1. Validation: Check if the repo is dirty
                if self.repo.is_dirty():
                    logger.warning("Repo has uncommitted changes. Switch might fail.")
                    # Optional: self.repo.git.stash()

                # 2. Logic: Create or Checkout
                if create and branch_name not in self.repo.branches:
                    logger.debug(f"Creating new branch: {branch_name}")
                    self.repo.git.checkout('-b', branch_name)
                else:
                    # Use git.checkout directly for better compatibility with remote branches
                    # or branches not yet in 'heads'
                    self.repo.git.checkout(branch_name)

                # 3. Verification
                current = self.repo.active_branch.name
                if current == branch_name:
                    logger.info(f"Successfully switched to {current}")
                    return True

            except Exception as e:
                logger.error(f"Failed to switch to {branch_name}: {e}")
                raise  # Re-raising allows the caller to handle the failure

    def revert_files(self, files):
        """Reverts specific files to their state in HEAD."""
        with self._lock:
            self.repo.git.checkout('HEAD', '--', files)

    def pull(self):
        with self._lock:
            origin = self.repo.remote(name='origin')
            origin.pull()

    def fetch(self, remote=None, all_remotes=False, prune=True):
            args = []

            if prune:
                args.append("--prune")

            if all_remotes:
                args.append("--all")
            elif remote:
                args.append(remote)

            try:
                output = self.repo.git.fetch(*args)
                return f"Fetch successful.\n{output}"
            except Exception as e:
                return f"Fetch failed: {str(e)}"

    def reset_to_head(self, hard=False):
        """Resets the index. If hard=True, discards all local changes."""
        with self._lock:
            if hard:
                self.repo.git.reset('--hard', 'HEAD')
            else:
                self.repo.git.reset('HEAD')

    def reset_work(self, mode="soft", files=None):
        """
        Handles three types of reset:
        - 'nuclear': Hard reset + Clean (Wipes everything)
        - 'soft': Unstages files (Keep changes)
        - 'files': Reverts specific files to HEAD state
        """
        with self._lock:
            if mode == "nuclear":
                self.repo.git.reset('--hard', 'HEAD')
                self.repo.git.clean('-fd')
                return "Nuclear reset complete. Working directory is clean."

            elif mode == "soft":
                self.repo.git.reset('HEAD')
                return "Files unstaged. Changes preserved."

            elif mode == "files" and files:
                self.repo.git.checkout('HEAD', '--', files)
                return f"Reverted {len(files)} files to HEAD state."

    def force_push(self):
        """Force pushes the current branch to origin."""
        with self._lock:
            try:
                origin = self.repo.remote(name='origin')
                info = origin.push(force=True)
                logger.warning(f"Force pushed {self.current_branch} to origin")
                return info
            except GitCommandError as e:
                logger.error(f"Force push failed: {e}")
                raise
    def rebase(self, upstream_branch="main"):
        """Rebases current branch onto the specified upstream branch."""
        with self._lock:
            try:
                logger.info(f"Rebasing {self.current_branch} onto {upstream_branch}")
                self.repo.git.rebase(upstream_branch)
                return True
            except GitCommandError as e:
                logger.error(f"Rebase conflict or failure: {e}")
                # Optional: self.repo.git.rebase('--abort')
                raise

    def find_actual_parent(self):
        """
        Finds the most recent commit that exists on origin/main
        that is also an ancestor of our current branch.
        """
        try:
            # We want the 'merge-base' specifically between us and the main remote
            # This is the most reliable way to find where you 'split' from the trunk
            parent_commit = self.repo.git.merge_base("HEAD", "origin/main")

            # Now we ask Git: "What are the names (tags/branches) at this commit?"
            # This will return something like "origin/main"
            return parent_commit.strip() # Returns the SHA, which is safest for squashing
        except Exception:
            # Fallback to the local 'main' if origin/main isn't fetched
            logger.info("Using fallback!!!!")
            return "main"

    def squash_since_divergence(self, message="Squash since divergence"):
            with self._lock:
                try:
                    base_branch_commit = self.find_actual_parent()
                    ancestors = self.repo.merge_base(self.repo.active_branch, base_branch_commit)
                    if not ancestors:
                        return {"success": False, "error": "No common ancestor found."}

                    common_ancestor = ancestors[0]
                    self.repo.git.reset('--soft', common_ancestor.hexsha)

                    new_commit = self.commit(message, locked=True)

                    if new_commit is None:
                        return {"success": False, "error": "The squash commit failed. Check logs."}

                    return {
                        "success": True,
                        "new_sha": new_commit.hexsha,
                        "message": f"Squashed to {base_branch_commit}",
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}

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


    def git_branches(self, include_remote=False):
        """Returns a list of local (and optionally remote) branch names."""
        with self._lock:
            branches = [b.name for b in self.repo.heads]

            if include_remote:
                # remote_branches will look like 'origin/main'
                remote_branches = [r.name for r in self.repo.remotes.origin.refs]
                # Combine and remove duplicates
                branches = list(set(branches + remote_branches))

            return sorted(branches)


    def git_log(self, limit=50):
        """Returns a list of the most recent commits with branch/remote refs."""
        with self._lock:
            log_data = []
            try:
                # Create a lookup map of commit hexsha -> list of ref names
                # This is much faster than searching refs for every single commit loop
                ref_map = {}
                for ref in self.repo.refs:
                    commit_hash = ref.commit.hexsha
                    if commit_hash not in ref_map:
                        ref_map[commit_hash] = []
                    ref_map[commit_hash].append(ref.name)

                for commit in self.repo.iter_commits(max_count=limit):
                    log_data.append({
                        "hash": commit.hexsha[:7],
                        "author": commit.author.name,
                        "date": commit.authored_datetime.strftime('%Y-%m-%d %H:%M'),
                        "message": commit.message.split('\n')[0], # Just the first line
                        "refs": ref_map.get(commit.hexsha, []) # Get refs for this commit
                    })
            except Exception as e:
                logger.error(f"Error fetching git log: {e}")

            return log_data


def do_test(client):
    print("======================================================>")
    print(f"\nCurrent branch: {client.current_branch}")
    print("======================================================>")
    print(f"git_unstaged -> {client.git_unstaged()}")
    print("======================================================>")
    print(f"git_staged -> {client.git_staged()}")
    print("======================================================>")
    print(f"git_committed -> {client.git_committed()}")
    print("======================================================>")
    print(f"git_untracked -> {client.git_untracked()}")
    print("======================================================>")
    print(f"git_branch_changes -> {client.git_branch_changes()}")
    print("======================================================>")
    print(f"git_unstaged_diff -> {client.git_unstaged_diff()}")
    print("======================================================>")
    print(f"git_staged_diff -> {client.git_staged_diff()}")
    print("======================================================>")
    print(f"git_committed_diff -> {client.git_committed_diff()}")
    print("======================================================>")
    print(f"git_committed_diff -> {client.git_branch_diff()}")
    print("======================================================>")

client = GitClient(".")
#print(client.find_actual_parent())
#print(client.git_log())
#print(client.git_branches())
#do_test(client)
#print(client.git_branch_diff("main"))

