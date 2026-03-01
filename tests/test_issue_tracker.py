"""
End-to-end tests for BlackRoad Plane IssueTracker.
Run with: pytest tests/ -v
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from issue_tracker import IssueTracker


@pytest.fixture
def tracker(tmp_path):
    db = tmp_path / "test.db"
    return IssueTracker(db_path=str(db))


# ---------------------------------------------------------------------------
# Issues
# ---------------------------------------------------------------------------

class TestIssues:
    def test_create_issue_returns_id(self, tracker):
        issue_id = tracker.create_issue("proj-1", "Fix login bug")
        assert issue_id is not None
        assert len(issue_id) > 0

    def test_create_issue_defaults(self, tracker):
        tracker.create_issue("proj-1", "Task A")
        issues = tracker.get_issues("proj-1")
        assert len(issues) == 1
        assert issues[0].status == "backlog"
        assert issues[0].priority == "medium"
        assert issues[0].type == "task"

    def test_create_issue_with_fields(self, tracker):
        issue_id = tracker.create_issue(
            "proj-1", "Safari bug",
            description="Fails on Safari 17",
            issue_type="bug",
            priority="high",
            assignees=["alice"],
            labels=["browser"],
        )
        issues = tracker.get_issues("proj-1")
        assert issues[0].id == issue_id
        assert issues[0].type == "bug"
        assert issues[0].priority == "high"
        assert issues[0].assignees == ["alice"]
        assert issues[0].labels == ["browser"]

    def test_sequence_ids_are_per_project(self, tracker):
        tracker.create_issue("proj-1", "A")
        tracker.create_issue("proj-1", "B")
        tracker.create_issue("proj-2", "C")
        p1 = tracker.get_issues("proj-1")
        p2 = tracker.get_issues("proj-2")
        seq_ids_p1 = sorted(i.sequence_id for i in p1)
        assert seq_ids_p1 == [1, 2]
        assert p2[0].sequence_id == 1

    def test_update_issue(self, tracker):
        issue_id = tracker.create_issue("proj-1", "Old title")
        result = tracker.update_issue(issue_id, title="New title", status="in_progress")
        assert result is True
        issues = tracker.get_issues("proj-1")
        assert issues[0].title == "New title"
        assert issues[0].status == "in_progress"

    def test_update_issue_invalid_field_ignored(self, tracker):
        issue_id = tracker.create_issue("proj-1", "Task")
        result = tracker.update_issue(issue_id, nonexistent_field="x")
        assert result is False

    def test_bulk_update(self, tracker):
        ids = [tracker.create_issue("proj-1", f"Issue {i}") for i in range(3)]
        affected = tracker.bulk_update(ids, status="in_progress")
        assert affected == 3
        issues = tracker.get_issues("proj-1", {"status": "in_progress"})
        assert len(issues) == 3

    def test_bulk_update_empty_list(self, tracker):
        assert tracker.bulk_update([], status="done") == 0

    def test_get_issues_filter_status(self, tracker):
        tracker.create_issue("proj-1", "A")
        id2 = tracker.create_issue("proj-1", "B")
        tracker.update_issue(id2, status="done")
        done = tracker.get_issues("proj-1", {"status": "done"})
        assert len(done) == 1
        assert done[0].title == "B"

    def test_get_issues_filter_priority(self, tracker):
        tracker.create_issue("proj-1", "Low", priority="low")
        tracker.create_issue("proj-1", "Urgent", priority="urgent")
        urgent = tracker.get_issues("proj-1", {"priority": "urgent"})
        assert len(urgent) == 1
        assert urgent[0].title == "Urgent"

    def test_get_issues_filter_label(self, tracker):
        tracker.create_issue("proj-1", "A", labels=["backend"])
        tracker.create_issue("proj-1", "B", labels=["frontend"])
        backend = tracker.get_issues("proj-1", {"label": "backend"})
        assert len(backend) == 1

    def test_get_issues_filter_assignee(self, tracker):
        tracker.create_issue("proj-1", "A", assignees=["alice"])
        tracker.create_issue("proj-1", "B", assignees=["bob"])
        alice_issues = tracker.get_issues("proj-1", {"assignee": "alice"})
        assert len(alice_issues) == 1
        assert alice_issues[0].assignees == ["alice"]


# ---------------------------------------------------------------------------
# Cycles
# ---------------------------------------------------------------------------

class TestCycles:
    def test_create_cycle(self, tracker):
        cycle_id = tracker.create_cycle(
            "proj-1", "Sprint 1",
            datetime.now(), datetime.now() + timedelta(days=14),
        )
        assert cycle_id is not None

    def test_add_to_cycle(self, tracker):
        cycle_id = tracker.create_cycle(
            "proj-1", "Sprint 1",
            datetime.now(), datetime.now() + timedelta(days=14),
        )
        issue_id = tracker.create_issue("proj-1", "Task A")
        result = tracker.add_to_cycle(issue_id, cycle_id)
        assert result is True
        by_cycle = tracker.get_issues("proj-1", {"cycle_id": cycle_id})
        assert len(by_cycle) == 1

    def test_cycle_analytics(self, tracker):
        cycle_id = tracker.create_cycle(
            "proj-1", "Sprint 1",
            datetime.now(), datetime.now() + timedelta(days=14),
        )
        issue_id = tracker.create_issue("proj-1", "Task A")
        tracker.add_to_cycle(issue_id, cycle_id)
        analytics = tracker.get_cycle_analytics(cycle_id)
        assert analytics["total_issues"] == 1
        assert analytics["completed"] == 0
        assert analytics["remaining"] == 1
        assert analytics["progress_pct"] == 0
        assert analytics["remaining_points"] == 1  # defaults to 1 when no estimate

    def test_cycle_analytics_with_completion(self, tracker):
        cycle_id = tracker.create_cycle(
            "proj-1", "Sprint 1",
            datetime.now(), datetime.now() + timedelta(days=14),
        )
        id1 = tracker.create_issue("proj-1", "A")
        id2 = tracker.create_issue("proj-1", "B")
        tracker.add_to_cycle(id1, cycle_id)
        tracker.add_to_cycle(id2, cycle_id)
        tracker.update_issue(id1, status="done")
        analytics = tracker.get_cycle_analytics(cycle_id)
        assert analytics["total_issues"] == 2
        assert analytics["completed"] == 1
        assert analytics["progress_pct"] == 50


# ---------------------------------------------------------------------------
# Modules
# ---------------------------------------------------------------------------

class TestModules:
    def test_create_module(self, tracker):
        module_id = tracker.create_module("proj-1", "Auth", "Authentication module")
        assert module_id is not None

    def test_add_to_module(self, tracker):
        module_id = tracker.create_module("proj-1", "Auth")
        issue_id = tracker.create_issue("proj-1", "JWT support")
        result = tracker.add_to_module(issue_id, module_id)
        assert result is True

    def test_module_progress(self, tracker):
        module_id = tracker.create_module("proj-1", "Auth")
        id1 = tracker.create_issue("proj-1", "A")
        id2 = tracker.create_issue("proj-1", "B")
        tracker.add_to_module(id1, module_id)
        tracker.add_to_module(id2, module_id)
        tracker.update_issue(id2, status="done")
        progress = tracker.get_module_progress(module_id)
        assert progress["total"] == 2
        assert progress["completion_pct"] == 50
        assert progress["by_status"]["done"] == 1


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

class TestComments:
    def test_add_and_get_comment(self, tracker):
        issue_id = tracker.create_issue("proj-1", "Bug A")
        comment_id = tracker.comment(issue_id, "alice", "Reproduced on macOS")
        assert comment_id is not None
        comments = tracker.get_comments(issue_id)
        assert len(comments) == 1
        assert comments[0]["user"] == "alice"
        assert comments[0]["body"] == "Reproduced on macOS"

    def test_comment_increments_count(self, tracker):
        issue_id = tracker.create_issue("proj-1", "Bug A")
        tracker.comment(issue_id, "alice", "First")
        tracker.comment(issue_id, "bob", "Second")
        issues = tracker.get_issues("proj-1")
        assert issues[0].comment_count == 2

    def test_multiple_comments_ordered(self, tracker):
        issue_id = tracker.create_issue("proj-1", "Bug A")
        tracker.comment(issue_id, "alice", "First")
        tracker.comment(issue_id, "bob", "Second")
        comments = tracker.get_comments(issue_id)
        assert len(comments) == 2
        assert comments[0]["user"] == "alice"
        assert comments[1]["user"] == "bob"


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

class TestAnalytics:
    def test_project_analytics_empty(self, tracker):
        analytics = tracker.get_project_analytics("proj-empty")
        assert analytics["velocity"] == 0
        assert analytics["priority_distribution"] == {}
        assert analytics["status_distribution"] == {}

    def test_project_analytics_priority_distribution(self, tracker):
        tracker.create_issue("proj-1", "A", priority="high")
        tracker.create_issue("proj-1", "B", priority="high")
        tracker.create_issue("proj-1", "C", priority="low")
        analytics = tracker.get_project_analytics("proj-1")
        dist = analytics["priority_distribution"]
        assert dist.get("high") == 2
        assert dist.get("low") == 1

    def test_project_analytics_status_distribution(self, tracker):
        id1 = tracker.create_issue("proj-1", "A")
        id2 = tracker.create_issue("proj-1", "B")
        tracker.update_issue(id1, status="done")
        analytics = tracker.get_project_analytics("proj-1")
        dist = analytics["status_distribution"]
        assert dist.get("done") == 1
        assert dist.get("backlog") == 1
