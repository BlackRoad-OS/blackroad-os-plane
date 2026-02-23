"""
Issue tracking system inspired by Plane and Linear.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Set
import sqlite3
import json
from pathlib import Path


@dataclass
class Issue:
    """Represents an issue."""
    id: str
    workspace_id: str
    project_id: str
    sequence_id: int
    title: str
    description: str = ""
    type: str = "task"  # bug, feature, task, story, improvement
    status: str = "backlog"
    priority: str = "medium"  # urgent, high, medium, low, none
    assignees: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    cycle_id: Optional[str] = None
    module_id: Optional[str] = None
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    estimate_points: Optional[int] = None
    link_count: int = 0
    attachment_count: int = 0
    comment_count: int = 0


@dataclass
class Cycle:
    """Represents a cycle (sprint-like)."""
    id: str
    project_id: str
    name: str
    status: str = "planned"  # planned, active, paused, completed
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    issues_count: int = 0
    completed_count: int = 0
    progress: int = 0


@dataclass
class Module:
    """Represents a module/feature group."""
    id: str
    project_id: str
    name: str
    description: str = ""
    status: str = "planned"
    lead: str = ""
    members: List[str] = field(default_factory=list)
    issues_count: int = 0


class IssueTracker:
    """Core issue tracking engine."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = Path.home() / ".blackroad" / "issues.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS issues (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                project_id TEXT NOT NULL,
                sequence_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'task',
                status TEXT DEFAULT 'backlog',
                priority TEXT DEFAULT 'medium',
                assignees TEXT,
                labels TEXT,
                cycle_id TEXT,
                module_id TEXT,
                created_by TEXT,
                created_at TEXT,
                updated_at TEXT,
                due_date TEXT,
                estimate_points INTEGER,
                link_count INTEGER DEFAULT 0,
                attachment_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS cycles (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT DEFAULT 'planned',
                start_date TEXT,
                end_date TEXT,
                issues_count INTEGER DEFAULT 0,
                completed_count INTEGER DEFAULT 0,
                progress INTEGER DEFAULT 0
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'planned',
                lead TEXT,
                members TEXT,
                issues_count INTEGER DEFAULT 0
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id TEXT NOT NULL,
                user TEXT,
                body TEXT,
                created_at TEXT,
                FOREIGN KEY(issue_id) REFERENCES issues(id)
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS issue_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id TEXT NOT NULL,
                user TEXT,
                action TEXT,
                field TEXT,
                old_value TEXT,
                new_value TEXT,
                timestamp TEXT,
                FOREIGN KEY(issue_id) REFERENCES issues(id)
            )
        ''')

        conn.commit()
        conn.close()

    def create_issue(self, project_id: str, title: str, description: str = "",
                    issue_type: str = "task", priority: str = "medium",
                    assignees: Optional[List[str]] = None,
                    labels: Optional[List[str]] = None) -> str:
        """Create a new issue."""
        import uuid
        issue_id = str(uuid.uuid4())[:8]
        workspace_id = "default"  # Simplified
        
        assignees = assignees or []
        labels = labels or []

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get next sequence ID for this project
        c.execute('SELECT MAX(sequence_id) FROM issues WHERE project_id = ?',
                 (project_id,))
        max_seq = c.fetchone()[0] or 0
        sequence_id = max_seq + 1

        now = datetime.now().isoformat()
        c.execute('''
            INSERT INTO issues
            (id, workspace_id, project_id, sequence_id, title, description,
             type, priority, assignees, labels, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (issue_id, workspace_id, project_id, sequence_id, title, description,
              issue_type, priority, json.dumps(assignees), json.dumps(labels),
              now, now))

        conn.commit()
        conn.close()
        return issue_id

    def update_issue(self, issue_id: str, **kwargs) -> bool:
        """Update an issue with flexible kwargs."""
        allowed_fields = {
            'title', 'description', 'status', 'priority', 'assignees',
            'labels', 'cycle_id', 'module_id', 'due_date', 'estimate_points'
        }

        # Filter to allowed fields
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        # Convert lists to JSON
        for field in ['assignees', 'labels']:
            if field in updates:
                updates[field] = json.dumps(updates[field])

        updates['updated_at'] = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [issue_id]

        c.execute(f'UPDATE issues SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
        return True

    def create_cycle(self, project_id: str, name: str,
                    start_date: datetime, end_date: datetime) -> str:
        """Create a cycle."""
        import uuid
        cycle_id = str(uuid.uuid4())[:8]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO cycles
            (id, project_id, name, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (cycle_id, project_id, name, start_date.isoformat(),
              end_date.isoformat()))
        conn.commit()
        conn.close()
        return cycle_id

    def add_to_cycle(self, issue_id: str, cycle_id: str) -> bool:
        """Add an issue to a cycle."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE issues SET cycle_id = ? WHERE id = ?',
                 (cycle_id, issue_id))
        conn.commit()
        conn.close()
        return True

    def create_module(self, project_id: str, name: str,
                     description: str = "") -> str:
        """Create a module."""
        import uuid
        module_id = str(uuid.uuid4())[:8]

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO modules
            (id, project_id, name, description)
            VALUES (?, ?, ?, ?)
        ''', (module_id, project_id, name, description))
        conn.commit()
        conn.close()
        return module_id

    def add_to_module(self, issue_id: str, module_id: str) -> bool:
        """Add an issue to a module."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE issues SET module_id = ? WHERE id = ?',
                 (module_id, issue_id))
        conn.commit()
        conn.close()
        return True

    def bulk_update(self, issue_ids: List[str], **kwargs) -> int:
        """Update multiple issues at once."""
        if not issue_ids:
            return 0

        allowed_fields = {
            'title', 'description', 'status', 'priority', 'assignees',
            'labels', 'cycle_id', 'module_id'
        }

        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return 0

        for field in ['assignees', 'labels']:
            if field in updates:
                updates[field] = json.dumps(updates[field])

        updates['updated_at'] = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values())

        placeholders = ', '.join(['?' for _ in issue_ids])
        c.execute(f'UPDATE issues SET {set_clause} WHERE id IN ({placeholders})',
                 values + issue_ids)

        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected

    def get_issues(self, project_id: str, filters: Optional[Dict] = None) -> List[Issue]:
        """Get issues with optional filters."""
        filters = filters or {}
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        query = 'SELECT * FROM issues WHERE project_id = ?'
        params = [project_id]

        if 'status' in filters:
            query += ' AND status = ?'
            params.append(filters['status'])
        if 'priority' in filters:
            query += ' AND priority = ?'
            params.append(filters['priority'])
        if 'assignee' in filters:
            # Note: assignees is JSON, so this is approximate
            query += " AND assignees LIKE ?"
            params.append(f"%{filters['assignee']}%")
        if 'label' in filters:
            query += " AND labels LIKE ?"
            params.append(f"%{filters['label']}%")
        if 'cycle_id' in filters:
            query += ' AND cycle_id = ?'
            params.append(filters['cycle_id'])

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        issues = []
        for row in rows:
            issues.append(Issue(
                id=row[0], workspace_id=row[1], project_id=row[2],
                sequence_id=row[3], title=row[4], description=row[5],
                type=row[6], status=row[7], priority=row[8],
                assignees=json.loads(row[9] or "[]"),
                labels=json.loads(row[10] or "[]"),
                cycle_id=row[11], module_id=row[12],
                created_by=row[13],
                created_at=datetime.fromisoformat(row[14]),
                updated_at=datetime.fromisoformat(row[15]),
                due_date=datetime.fromisoformat(row[16]) if row[16] else None,
                estimate_points=row[17],
                link_count=row[18],
                attachment_count=row[19],
                comment_count=row[20]
            ))
        return issues

    def get_cycle_analytics(self, cycle_id: str) -> Dict:
        """Get analytics for a cycle (burnup/burndown data)."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT COUNT(*), SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END)
            FROM issues WHERE cycle_id = ?
        ''', (cycle_id,))

        total, completed = c.fetchone()
        completed = completed or 0

        c.execute('''
            SELECT SUM(CASE WHEN estimate_points IS NOT NULL THEN estimate_points ELSE 1 END)
            FROM issues WHERE cycle_id = ? AND status != 'done'
        ''', (cycle_id,))

        remaining_points = c.fetchone()[0] or 0
        conn.close()

        return {
            "total_issues": total,
            "completed": completed,
            "remaining": total - completed,
            "progress_pct": int((completed / total * 100) if total > 0 else 0),
            "remaining_points": remaining_points
        }

    def get_module_progress(self, module_id: str) -> Dict:
        """Get progress for a module."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT COUNT(*) FROM issues WHERE module_id = ?
        ''', (module_id,))
        total = c.fetchone()[0]

        c.execute('''
            SELECT status, COUNT(*) FROM issues
            WHERE module_id = ?
            GROUP BY status
        ''', (module_id,))

        by_status = {}
        for status, count in c.fetchall():
            by_status[status] = count

        completed = by_status.get('done', 0)
        conn.close()

        return {
            "total": total,
            "by_status": by_status,
            "completion_pct": int((completed / total * 100) if total > 0 else 0)
        }

    def get_project_analytics(self, project_id: str) -> Dict:
        """Get high-level project analytics."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Velocity (average issues completed per cycle)
        c.execute('''
            SELECT AVG(completed_count) FROM cycles WHERE project_id = ?
        ''', (project_id,))
        velocity = c.fetchone()[0] or 0

        # Priority distribution
        c.execute('''
            SELECT priority, COUNT(*) FROM issues
            WHERE project_id = ?
            GROUP BY priority
        ''', (project_id,))

        priority_dist = {p: c for p, c in c.fetchall()}

        # Status distribution
        c.execute('''
            SELECT status, COUNT(*) FROM issues
            WHERE project_id = ?
            GROUP BY status
        ''', (project_id,))

        status_dist = {s: c for s, c in c.fetchall()}

        conn.close()

        return {
            "velocity": velocity,
            "priority_distribution": priority_dist,
            "status_distribution": status_dist
        }

    def comment(self, issue_id: str, user: str, body: str) -> int:
        """Add a comment to an issue."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO comments (issue_id, user, body, created_at)
            VALUES (?, ?, ?, ?)
        ''', (issue_id, user, body, datetime.now().isoformat()))

        # Increment comment count
        c.execute('''
            UPDATE issues SET comment_count = comment_count + 1
            WHERE id = ?
        ''', (issue_id,))

        conn.commit()
        comment_id = c.lastrowid
        conn.close()
        return comment_id

    def get_comments(self, issue_id: str) -> List[Dict]:
        """Get all comments for an issue."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT id, user, body, created_at FROM comments
            WHERE issue_id = ?
            ORDER BY created_at
        ''', (issue_id,))

        comments = []
        for comment_id, user, body, created_at in c.fetchall():
            comments.append({
                "id": comment_id,
                "user": user,
                "body": body,
                "created_at": created_at
            })

        conn.close()
        return comments


# CLI interface
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Issue tracking system")
    subparsers = parser.add_subparsers(dest="command")

    # issues command
    issues_parser = subparsers.add_parser("issues")
    issues_parser.add_argument("--project", required=True)
    issues_parser.add_argument("--status", default=None)

    # create command
    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("project_id")
    create_parser.add_argument("type")
    create_parser.add_argument("title")
    create_parser.add_argument("--priority", default="medium")

    # analytics command
    analytics_parser = subparsers.add_parser("analytics")
    analytics_parser.add_argument("project_id")

    args = parser.parse_args()
    tracker = IssueTracker()

    if args.command == "issues":
        filters = {}
        if args.status:
            filters['status'] = args.status
        issues = tracker.get_issues(args.project, filters)
        for issue in issues:
            print(f"[{issue.sequence_id}] {issue.title} ({issue.status})")
    elif args.command == "create":
        issue_id = tracker.create_issue(args.project_id, args.title,
                                       issue_type=args.type, priority=args.priority)
        print(f"Issue created: {issue_id}")
    elif args.command == "analytics":
        analytics = tracker.get_project_analytics(args.project_id)
        print(f"Velocity: {analytics['velocity']}")
        print(f"Status: {analytics['status_distribution']}")
