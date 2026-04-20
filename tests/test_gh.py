"""'ghpr.gh' module tests.

TODO: improve these tests by further mocking out the inputs/outputs of `GHHelper`.
"""

import json
import subprocess
from unittest.mock import patch

from ghpr import gh


class TestGHHelperPRCommands:
    """GHHelper PR-related command test suite."""

    @staticmethod
    def test_checkout(setup_staging: ...) -> None:
        """Test `gh pr checkout` integration."""
        staging_repo = setup_staging
        ghh = gh.GHHelper(staging_repo, verbose=True)
        with patch.object(ghh, "run") as mock_run:
            ghh.pr_checkout(0, "bogus")
            mock_run.assert_called()

    @staticmethod
    def test_close(setup_staging: ...) -> None:
        """Test `gh pr close` integration."""
        staging_repo = setup_staging
        ghh = gh.GHHelper(staging_repo, verbose=True)
        with patch.object(ghh, "run") as mock_run:
            ghh.pr_close(0)
            mock_run.assert_called()

    @staticmethod
    def test_edit(setup_staging: ...) -> None:
        """Test `gh pr edit` integration."""
        staging_repo = setup_staging
        ghh = gh.GHHelper(staging_repo, verbose=True)
        with patch.object(ghh, "run") as mock_run:
            ghh.pr_edit(0, add_label="campbell_soup")
            mock_run.assert_called()

    @staticmethod
    def test_view_dry_run(setup_staging: ...) -> None:
        """Test `gh pr view` (dry-run) integration."""
        staging_repo = setup_staging
        ghh = gh.GHHelper(staging_repo, dry_run=True, verbose=True)
        with patch.object(ghh, "gh_pr") as mock_gh_pr:
            assert ghh.pr_view(0) == gh._DRY_RUN_VIEW_RESULTS
            mock_gh_pr.assert_not_called()

    @staticmethod
    def test_view_mocked(setup_staging: ...) -> None:
        """Test `gh pr view` (mocked) integration."""
        staging_repo = setup_staging
        ghh = gh.GHHelper(staging_repo, verbose=True)
        with patch.object(ghh, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                [],
                returncode=0,
                stdout=json.dumps({"bogus": "json"}),
                stderr="",
            )
            ghh.pr_view(0)
            mock_run.assert_called()
