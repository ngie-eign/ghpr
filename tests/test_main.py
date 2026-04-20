"""End-to-end tests for `ghpr`."""

# Stuff that doesn't need to be fixed:

# ruff: noqa: S101

# Stuff that's worth fixing, but is being suppressed for now.

# ruff: noqa: ANN001, ANN201, FIX002, TD002, TD003

import os
import pathlib
import shutil
from contextlib import contextmanager

import git
import pytest
from click.testing import CliRunner

from ghpr import __main__

from . import format_result, sandbox, setup_freebsd_remote


class TestInit:
    """`ghpr init` tests."""

    @staticmethod
    def test_from_non_git_repo() -> None:
        """Confirm that pointing ghpr at a repo without a freebsd remote fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(__main__.cli, ["init"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    def test_without_freebsd_remote(bare_repo: ...) -> None:
        """Confirm that pointing ghpr at a repo without a freebsd remote fails."""
        runner = CliRunner()
        with runner.isolated_filesystem(bare_repo):
            result = runner.invoke(__main__.cli, ["init"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    @pytest.mark.parametrize(
        "remote",
        [
            "https://bogus/src",
            "git@bogus:src",
            "git+ssh://bogus/src",
        ],
    )
    def test_bogus_remotes(bare_repo: ..., remote: str) -> None:
        """Confirm that pointing ghpr at a repo with a bogus freebsd remote fails.

        This is not an exhaustive battery of tests.
        """
        setup_freebsd_remote(bare_repo, remote)
        runner = CliRunner()
        with runner.isolated_filesystem(bare_repo):
            result = runner.invoke(__main__.cli, ["init"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    @pytest.mark.parametrize(
        "remote",
        [
            __main__.ALLOWED_STAGING_URLS[0].upper(),
            *__main__.ALLOWED_STAGING_URLS,
        ],
    )
    def test_allowed_remotes(bare_repo: ..., remote: str) -> None:
        """Confirm that pointing ghpr at a repo with a bogus.

        This is not an exhaustive battery of tests.
        """
        setup_freebsd_remote(bare_repo, remote)
        runner = CliRunner()
        with runner.isolated_filesystem(bare_repo):
            result = runner.invoke(__main__.cli, ["init"])
            assert result.exit_code == 0, format_result(result)

    @staticmethod
    def test_dry_run(setup_staging: ...) -> None:
        """Confirm that `--dry-run` works."""
        runner = CliRunner()
        staging_repo = setup_staging
        with runner.isolated_filesystem(staging_repo):
            result = runner.invoke(__main__.cli, ["--dry-run", "init"])
            assert result.exit_code == 0, format_result(result)

    @staticmethod
    def test_force(default_freebsd_remote: ...) -> None:
        """Confirm that `--force` is effectively a no-op if run on fresh repo."""
        runner = CliRunner()
        with runner.isolated_filesystem(default_freebsd_remote):
            result = runner.invoke(__main__.cli, ["init", "--force"])
            assert result.exit_code == 0, format_result(result)
            assert "has already been initialized" not in result.output

    @staticmethod
    def test_init_already_inited_succeeds(default_freebsd_remote: ...) -> None:
        """Confirm behavior when  `--force` works."""
        runner = CliRunner()
        with runner.isolated_filesystem(default_freebsd_remote):
            result = runner.invoke(__main__.cli, ["init"])
            assert result.exit_code == 0, format_result(result)

            result = runner.invoke(__main__.cli, ["init"])
            assert result.exit_code == 0, format_result(result)
            assert "has already been initialized" in result.output

            result = runner.invoke(__main__.cli, ["init", "--force"])
            assert result.exit_code == 0, format_result(result)
            assert "Cleaning up existing " in result.output
            assert "Cleanup complete" in result.output

    @staticmethod
    def test_verbose(default_freebsd_remote: ...) -> None:
        """Confirm that `--verbose` works."""
        runner = CliRunner()
        with runner.isolated_filesystem(default_freebsd_remote):
            result = runner.invoke(__main__.cli, ["--verbose", "init"])
            assert result.exit_code == 0, format_result(result)
            assert result.output_bytes, format_result(result)


class TestPush:
    """`ghpr push` tests."""

    @staticmethod
    def test_no_init_fails() -> None:
        """Confirm that running the command without running `ghpr init` first fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(__main__.cli, ["push"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    @pytest.mark.xfail
    def test_dry_run(setup_staging: ...) -> None:
        """Confirm that `--dry-run` works."""
        staging_repo = setup_staging
        runner = CliRunner()
        with runner.isolated_filesystem(staging_repo):
            result = runner.invoke(__main__.cli, ["--dry-run", "push"])
            assert result.exit_code == 0, format_result(result)


class TestStage:
    """`ghpr stage` tests."""

    @staticmethod
    def test_no_init_fails() -> None:
        """Confirm that running the command without running `ghpr init` first fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(__main__.cli, ["stage", "0"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    @pytest.mark.xfail
    def test_dry_run(setup_staging: ...) -> None:
        """Confirm that `--dry-run` works."""
        staging_repo = setup_staging
        runner = CliRunner()
        with runner.isolated_filesystem(staging_repo):
            dummy_pr = "0"
            result = runner.invoke(__main__.cli, ["--dry-run", "stage", dummy_pr])
            assert result.exit_code == 0, format_result(result)


class TestStatus:
    """`ghpr status` tests."""

    @staticmethod
    def test_no_init_fails() -> None:
        """Confirm that running the command without running `ghpr init` first fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(__main__.cli, ["status"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    def test_dry_run(setup_staging: ...) -> None:
        """Confirm that `--dry-run` works."""
        staging_repo = setup_staging
        runner = CliRunner()
        with runner.isolated_filesystem(staging_repo):
            result = runner.invoke(__main__.cli, ["--dry-run", "status"])
            assert result.exit_code == 0, format_result(result)


class TestUnstage:
    """`ghpr unstage` tests."""

    @staticmethod
    def test_no_init_fails() -> None:
        """Confirm that running the command without running `ghpr init` first fails."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(__main__.cli, ["unstage", "0"])
            assert result.exit_code != 0, format_result(result)

    @staticmethod
    @pytest.mark.xfail
    def test_dry_run(setup_staging: ...) -> None:
        """Confirm that `--dry-run` works."""
        staging_repo = setup_staging
        runner = CliRunner()
        with runner.isolated_filesystem(staging_repo):
            result = runner.invoke(__main__.cli, ["--dry-run", "unstage", "0"])
            assert result.exit_code == 0, format_result(result)


class TestGitHelper:
    @staticmethod
    def test_dry_run(setup_staging) -> None:
        """Confirm that `--dry-run` works."""
        staging_repo = setup_staging
        with sandbox(staging_repo):
            assert __main__.GitHelper.branch_exists("main")
            assert not __main__.GitHelper.branch_exists("doesnotexist")
