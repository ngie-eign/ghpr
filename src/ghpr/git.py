"""Git subroutines/interfaces."""

import contextlib
import subprocess
from typing import Self

import click


class GitHelper:
    """git command wrapper."""

    def __init__(
        self: Self,
        *,
        dry_run: bool = False,
        verbose: bool = False,
        working_dir: ... = None,
    ) -> None:
        self.dry_run = dry_run
        self.verbose = verbose

    def _print_cmd(self: Self, cmd: list[str]) -> None:
        """Print command if verbose or dry-run mode is enabled."""
        if self.verbose or self.dry_run:
            click.echo(f"+ {' '.join(cmd)}")

    def run(
        self: Self,
        args: list[str],
        check: bool = True,
        capture: bool = False,
        safe: bool = False,
    ) -> subprocess.CompletedProcess:
        """Run a git command."""
        cmd = ["git", *args]
        self._print_cmd(cmd)
        if self.dry_run and not safe:
            # In dry-run mode, don't execute anything
            class FakeResult:
                stdout = ""
                stderr = ""
                returncode = 0

            return FakeResult()
        if capture:
            return subprocess.run(cmd, capture_output=True, text=True, check=check)
        return subprocess.run(cmd, check=check)

    def branch_exists(self: Self, branch: str) -> bool:
        """Check if a branch exists."""
        cmd = ["git", "rev-parse", "--verify", branch]
        self._print_cmd(cmd)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            check=False,
        )
        return proc.returncode == 0

    def checkout(
        self: Self,
        branch: str,
        create: bool = False,
        base: str | None = None,
    ) -> None:
        """Checkout a branch, optionally creating it."""
        cmd = ["checkout"]
        if create:
            cmd.append("-b")
        cmd.append(branch)
        if base:
            cmd.append(base)
        self.run(cmd)

    def rebase(
        self: Self,
        base: str,
        onto: str | None = None,
        interactive: bool = False,
        exec_cmd: str | None = None,
    ) -> None:
        """Rebase current branch."""
        cmd = ["rebase"]
        if interactive:
            cmd.append("-i")
        if onto:
            cmd.extend(["--onto", onto])
        if exec_cmd:
            cmd.extend(["--exec", exec_cmd])
        cmd.append(base)
        self.run(cmd)

    def push(
        self: Self,
        remote: str,
        refspec: str,
        force: bool = False,
        push_option: str | None = None,
    ) -> bool:
        """Push to remote, return True if successful."""
        cmd = ["push"]
        if push_option:
            cmd.extend(["--push-option", push_option])
        if force:
            cmd.append("--force")
        cmd.extend([remote, refspec])
        try:
            self.run(cmd)
        except subprocess.CalledProcessError:
            return False
        else:
            return True

    def fetch(self: Self, remote: str) -> None:
        """Fetch from remote."""
        self.run(["fetch", remote], safe=True)

    def pull(self: Self, rebase: bool = True) -> None:
        """Pull from current upstream."""
        cmd = ["pull"]
        if rebase:
            cmd.append("--rebase")
        self.run(cmd)

    def delete_branch(self: Self, branch: str, force: bool = True) -> None:
        """Delete a branch."""
        flag = "-D" if force else "-d"
        self.run(
            ["branch", flag, branch],
            check=False,  # The branch might not exist
        )

    def move_branch(self: Self, branch: str, target: str = "HEAD") -> None:
        """Force-move a branch to a specific commit and check it out."""
        # Force-move the branch pointer
        self.run(["branch", "-f", branch, target])
        # Check out the branch
        self.run(["checkout", branch])

    def get_commits_with_trailer(
        self: Self,
        base: str,
        head: str,
        trailer: str,
        value: str,
    ) -> list[str]:
        """Get commit hashes that contain a specific trailer value."""
        cmd = [
            "log",
            "--format=%H",
            "--grep",
            f"^{trailer}: .*{value}",
            f"{base}..{head}",
        ]
        result = self.run(cmd, capture=True, safe=True)
        return [
            line.strip()
            for line in result.stdout.strip().splitlines(keepends=False)
            if line.strip()
        ]

    def cherry_pick(self: Self, commits: list[str]) -> None:
        """Cherry-pick commits."""
        cmd = ["cherry-pick"]
        cmd.extend(commits)
        self.run(cmd)


class GitConfig(GitHelper):
    """Helper class for git config operations."""

    def get(self: Self, key: str, default: str | None = None) -> str | None:
        """Get a git config value."""
        cmd = ["git", "config", "--get", key]
        self._print_cmd(cmd)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return default

    def get_all(self: Self, key: str) -> list[str]:
        """Get all values for a git config key."""
        cmd = ["git", "config", "--get-all", key]
        self._print_cmd(cmd)
        if self.dry_run:
            return []
        result = subprocess.run(
            cmd,
            check=False,  # The section might not exist
            safe=True,
            capture_output=True,
            text=True,
        )
        return [
            line.strip()
            for line in result.stdout.strip().splitlines(keepends=False)
            if line.strip()
        ]

    def set(
        self: Self,
        key: str,
        value: ...,
        config_type: str | None = None,
        add: bool = False,
    ) -> None:
        """Set a git config value."""
        cmd = ["git", "config"]
        if config_type:
            cmd.extend(["--type", config_type])
        if add:
            cmd.append("--add")
        cmd.extend([key, value])
        self._print_cmd(cmd)
        if self.dry_run:
            return
        subprocess.run(cmd, check=True)

    def unset(self: Self, key: str, value: str | None = None) -> None:
        """Unset a git config value."""
        cmd = ["git", "config", "--unset"]
        cmd.append(key)
        if value:
            cmd.append(value)
        self._print_cmd(cmd)
        if self.dry_run:
            return
        with contextlib.suppress(subprocess.CalledProcessError):  # Key might not exist
            subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)

    def remove_section(self: Self, section: str) -> None:
        """Remove a git config section."""
        cmd = ["git", "config", "--remove-section", section]
        self._print_cmd(cmd)
        if self.dry_run:
            return
        subprocess.run(
            cmd,
            check=False,  # The section might not exist
            stderr=subprocess.DEVNULL,
        )
