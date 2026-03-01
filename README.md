# BlackRoad Plane

> **The fastest, most intuitive issue tracker built for modern engineering teams.**  
> Inspired by Plane and Linear — cycles, modules, analytics, Stripe billing, and full E2E test coverage, all in one production-ready package.

[![npm version](https://img.shields.io/npm/v/blackroad-plane)](https://www.npmjs.com/package/blackroad-plane)
[![License](https://img.shields.io/badge/license-Proprietary-red)](./LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Installation](#3-installation)
   - [npm](#31-npm)
   - [pip](#32-pip)
4. [Quick Start](#4-quick-start)
5. [CLI Reference](#5-cli-reference)
6. [Python API Reference](#6-python-api-reference)
   - [IssueTracker](#61-issuetracker)
   - [Issues](#62-issues)
   - [Cycles](#63-cycles)
   - [Modules](#64-modules)
   - [Comments](#65-comments)
   - [Analytics](#66-analytics)
7. [Stripe Integration](#7-stripe-integration)
   - [Setup](#71-setup)
   - [Billing Plans](#72-billing-plans)
   - [Webhooks](#73-webhooks)
8. [E2E Testing](#8-e2e-testing)
   - [Running Tests](#81-running-tests)
   - [Test Coverage](#82-test-coverage)
9. [Database Schema](#9-database-schema)
10. [Configuration](#10-configuration)
11. [License](#11-license)

---

## 1. Overview

**BlackRoad Plane** is a production-grade issue tracking engine designed for teams that move fast.  
It ships with per-project sequence IDs, sprint cycles, feature modules, burnup/burndown analytics, bulk operations, and a Stripe-connected billing layer — all backed by SQLite for zero-dependency local storage and a clean Python API.

---

## 2. Features

| Feature | Description |
|---|---|
| **Sequenced Issues** | Per-project issue numbering (`PROJECT-1`, `PROJECT-2`, …) |
| **Cycles** | Sprint-like iterations with burnup / burndown analytics |
| **Modules** | Feature- and component-based issue grouping |
| **Priority & Status** | Urgent → None priority tiers; fully customizable workflow states |
| **Bulk Operations** | Update status, priority, assignees, or labels across many issues in one call |
| **Full-text Search** | Filter issues by status, priority, assignee, label, or cycle |
| **Comments & Activity** | Threaded discussion and a complete change-history log |
| **Analytics** | Velocity, cycle time, priority distribution, completion percentage |
| **Stripe Billing** | Workspace subscription management via Stripe Checkout & webhooks |
| **SQLite Backend** | Persistent storage at `~/.blackroad/issues.db` — no server required |

---

## 3. Installation

### 3.1 npm

BlackRoad Plane is published on [npm](https://www.npmjs.com/package/blackroad-plane) as a CLI wrapper for JavaScript / Node.js toolchains:

```bash
npm install blackroad-plane
# or globally
npm install -g blackroad-plane
```

After installing, the `blackroad-plane` binary is available on your `PATH`:

```bash
blackroad-plane --help
```

### 3.2 pip

For direct Python usage or embedding in a Python project:

```bash
pip install blackroad-plane
# upgrade to the latest release
pip install --upgrade blackroad-plane
```

**Requirements:** Python 3.9 or higher.

---

## 4. Quick Start

```python
from blackroad_plane import IssueTracker

tracker = IssueTracker()

# Create a project issue
issue_id = tracker.create_issue(
    project_id="my-app",
    title="Login fails on Safari",
    issue_type="bug",
    priority="high",
)
print(f"Created issue: {issue_id}")

# Open a sprint cycle
from datetime import datetime, timedelta
cycle_id = tracker.create_cycle(
    project_id="my-app",
    name="Sprint 1",
    start_date=datetime.now(),
    end_date=datetime.now() + timedelta(days=14),
)
tracker.add_to_cycle(issue_id, cycle_id)

# View analytics
analytics = tracker.get_project_analytics("my-app")
print(analytics)
```

---

## 5. CLI Reference

```
Usage: blackroad-plane <command> [options]

Commands:
  issues       List issues for a project
  create       Create a new issue
  analytics    Print project analytics

Options for `issues`:
  --project <id>    Project ID (required)
  --status  <s>     Filter by status (backlog | in_progress | done | …)

Options for `create`:
  <project_id>      Project ID (positional, required)
  <type>            Issue type: bug | feature | task | story | improvement
  <title>           Issue title (positional, required)
  --priority <p>    Priority: urgent | high | medium | low | none  [default: medium]

Options for `analytics`:
  <project_id>      Project ID (positional, required)
```

**Examples:**

```bash
# List open issues
blackroad-plane issues --project my-app --status open

# Create a high-priority bug
blackroad-plane create my-app bug "Login fails on Safari" --priority high

# View project analytics
blackroad-plane analytics my-app
```

---

## 6. Python API Reference

### 6.1 IssueTracker

```python
IssueTracker(db_path: str | None = None)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `db_path` | `str \| None` | `~/.blackroad/issues.db` | Path to the SQLite database file |

---

### 6.2 Issues

#### `create_issue`

```python
tracker.create_issue(
    project_id: str,
    title: str,
    description: str = "",
    issue_type: str = "task",   # bug | feature | task | story | improvement
    priority: str = "medium",   # urgent | high | medium | low | none
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
) -> str  # returns issue ID
```

#### `update_issue`

```python
tracker.update_issue(
    issue_id: str,
    **kwargs,   # title, description, status, priority, assignees,
                # labels, cycle_id, module_id, due_date, estimate_points
) -> bool
```

#### `get_issues`

```python
tracker.get_issues(
    project_id: str,
    filters: dict | None = None,
    # filter keys: status, priority, assignee, label, cycle_id
) -> list[Issue]
```

#### `bulk_update`

```python
tracker.bulk_update(
    issue_ids: list[str],
    **kwargs,   # same fields as update_issue
) -> int  # number of rows affected
```

---

### 6.3 Cycles

#### `create_cycle`

```python
tracker.create_cycle(
    project_id: str,
    name: str,
    start_date: datetime,
    end_date: datetime,
) -> str  # returns cycle ID
```

#### `add_to_cycle`

```python
tracker.add_to_cycle(issue_id: str, cycle_id: str) -> bool
```

#### `get_cycle_analytics`

```python
tracker.get_cycle_analytics(cycle_id: str) -> dict
# {total_issues, completed, remaining, progress_pct, remaining_points}
```

---

### 6.4 Modules

#### `create_module`

```python
tracker.create_module(
    project_id: str,
    name: str,
    description: str = "",
) -> str  # returns module ID
```

#### `add_to_module`

```python
tracker.add_to_module(issue_id: str, module_id: str) -> bool
```

#### `get_module_progress`

```python
tracker.get_module_progress(module_id: str) -> dict
# {total, by_status, completion_pct}
```

---

### 6.5 Comments

#### `comment`

```python
tracker.comment(issue_id: str, user: str, body: str) -> int  # comment ID
```

#### `get_comments`

```python
tracker.get_comments(issue_id: str) -> list[dict]
# [{id, user, body, created_at}, …]
```

---

### 6.6 Analytics

#### `get_project_analytics`

```python
tracker.get_project_analytics(project_id: str) -> dict
# {velocity, priority_distribution, status_distribution}
```

---

## 7. Stripe Integration

BlackRoad Plane supports workspace-level subscription billing via [Stripe](https://stripe.com).

### 7.1 Setup

1. Install the Stripe SDK:

   ```bash
   pip install stripe
   # or
   npm install stripe
   ```

2. Set your API keys as environment variables:

   ```bash
   export STRIPE_SECRET_KEY=sk_live_...
   export STRIPE_PUBLISHABLE_KEY=pk_live_...
   export STRIPE_WEBHOOK_SECRET=whsec_...
   ```

3. Configure your billing plan price IDs in your application config (see [Section 10](#10-configuration)).

### 7.2 Billing Plans

| Plan | Price | Issues | Cycles | Seats |
|---|---|---|---|---|
| **Starter** | $0 / mo | 100 | 1 | 1 |
| **Pro** | $12 / seat / mo | Unlimited | Unlimited | Up to 25 |
| **Enterprise** | Custom | Unlimited | Unlimited | Unlimited |

To create a Stripe Checkout session for a workspace upgrade:

```python
import stripe
import os

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]

session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[{
        "price": "price_YOUR_PRO_PRICE_ID",
        "quantity": seat_count,
    }],
    mode="subscription",
    success_url="https://your-app.com/billing/success?session_id={CHECKOUT_SESSION_ID}",
    cancel_url="https://your-app.com/billing/cancel",
    metadata={"workspace_id": workspace_id},
)
redirect_url = session.url
```

### 7.3 Webhooks

Register `https://your-app.com/stripe/webhook` in the [Stripe Dashboard](https://dashboard.stripe.com/webhooks).  
Handle at minimum the following events to keep subscription state in sync:

| Event | Action |
|---|---|
| `checkout.session.completed` | Activate workspace subscription |
| `invoice.paid` | Renew subscription, reset usage limits |
| `invoice.payment_failed` | Notify workspace admins; grace period begins |
| `customer.subscription.deleted` | Downgrade workspace to Starter plan |

```python
import stripe
from flask import Flask, request, abort

app = Flask(__name__)

@app.post("/stripe/webhook")
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ["STRIPE_WEBHOOK_SECRET"]
        )
    except stripe.error.SignatureVerificationError:
        abort(400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        workspace_id = session["metadata"]["workspace_id"]
        # activate_workspace_subscription(workspace_id)

    elif event["type"] == "customer.subscription.deleted":
        # downgrade_workspace(event["data"]["object"])
        pass

    return {"status": "ok"}
```

---

## 8. E2E Testing

### 8.1 Running Tests

The test suite covers all core tracker operations end-to-end using a temporary SQLite database.

```bash
# Install test dependencies
pip install pytest

# Run the full suite
pytest tests/ -v

# Run with coverage
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

### 8.2 Test Coverage

| Area | Tests |
|---|---|
| Issue CRUD | create, read, update, bulk-update |
| Cycle management | create cycle, add issues, analytics |
| Module management | create module, add issues, progress |
| Comments | add comment, list comments, count increment |
| Analytics | velocity, priority distribution, status distribution |
| Filters | status, priority, assignee, label, cycle filters |
| CLI | issues, create, analytics subcommands |

**Example test:**

```python
# tests/test_issue_tracker.py
import pytest
import tempfile
import os
from src.issue_tracker import IssueTracker

@pytest.fixture
def tracker(tmp_path):
    db = tmp_path / "test.db"
    return IssueTracker(db_path=str(db))

def test_create_and_get_issue(tracker):
    issue_id = tracker.create_issue("proj-1", "Fix login bug", issue_type="bug", priority="high")
    issues = tracker.get_issues("proj-1")
    assert len(issues) == 1
    assert issues[0].id == issue_id
    assert issues[0].title == "Fix login bug"
    assert issues[0].priority == "high"

def test_bulk_update(tracker):
    ids = [tracker.create_issue("proj-1", f"Issue {i}") for i in range(3)]
    affected = tracker.bulk_update(ids, status="in_progress")
    assert affected == 3
    for issue in tracker.get_issues("proj-1", {"status": "in_progress"}):
        assert issue.status == "in_progress"

def test_cycle_analytics(tracker):
    from datetime import datetime, timedelta
    cycle_id = tracker.create_cycle(
        "proj-1", "Sprint 1",
        datetime.now(), datetime.now() + timedelta(days=14)
    )
    issue_id = tracker.create_issue("proj-1", "Task A")
    tracker.add_to_cycle(issue_id, cycle_id)
    analytics = tracker.get_cycle_analytics(cycle_id)
    assert analytics["total_issues"] == 1
    assert analytics["remaining"] == 1
```

---

## 9. Database Schema

All data is stored in a single SQLite file (default: `~/.blackroad/issues.db`).

### `issues`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT PK | 8-char UUID |
| `workspace_id` | TEXT | Workspace identifier |
| `project_id` | TEXT | Project identifier |
| `sequence_id` | INTEGER | Per-project sequential number |
| `title` | TEXT | Issue title |
| `description` | TEXT | Markdown description |
| `type` | TEXT | `bug` \| `feature` \| `task` \| `story` \| `improvement` |
| `status` | TEXT | `backlog` \| `in_progress` \| `done` \| … |
| `priority` | TEXT | `urgent` \| `high` \| `medium` \| `low` \| `none` |
| `assignees` | TEXT | JSON array of user IDs |
| `labels` | TEXT | JSON array of label strings |
| `cycle_id` | TEXT | FK → `cycles.id` |
| `module_id` | TEXT | FK → `modules.id` |
| `created_by` | TEXT | User ID |
| `created_at` | TEXT | ISO-8601 timestamp |
| `updated_at` | TEXT | ISO-8601 timestamp |
| `due_date` | TEXT | ISO-8601 date (nullable) |
| `estimate_points` | INTEGER | Story-point estimate (nullable) |
| `link_count` | INTEGER | Attached link count |
| `attachment_count` | INTEGER | File attachment count |
| `comment_count` | INTEGER | Comment count (denormalised) |

### `cycles`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT PK | 8-char UUID |
| `project_id` | TEXT | Project identifier |
| `name` | TEXT | Cycle name |
| `status` | TEXT | `planned` \| `active` \| `paused` \| `completed` |
| `start_date` | TEXT | ISO-8601 timestamp |
| `end_date` | TEXT | ISO-8601 timestamp |
| `issues_count` | INTEGER | Total issues in cycle |
| `completed_count` | INTEGER | Completed issues count |
| `progress` | INTEGER | Completion percentage |

### `modules`

| Column | Type | Description |
|---|---|---|
| `id` | TEXT PK | 8-char UUID |
| `project_id` | TEXT | Project identifier |
| `name` | TEXT | Module name |
| `description` | TEXT | Module description |
| `status` | TEXT | `planned` \| `in_progress` \| `completed` |
| `lead` | TEXT | Lead user ID |
| `members` | TEXT | JSON array of user IDs |
| `issues_count` | INTEGER | Total issues in module |

### `comments`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `issue_id` | TEXT | FK → `issues.id` |
| `user` | TEXT | Commenter user ID |
| `body` | TEXT | Comment body (Markdown) |
| `created_at` | TEXT | ISO-8601 timestamp |

### `issue_activity`

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `issue_id` | TEXT | FK → `issues.id` |
| `user` | TEXT | Acting user ID |
| `action` | TEXT | Action type (e.g. `updated`) |
| `field` | TEXT | Changed field name |
| `old_value` | TEXT | Previous value |
| `new_value` | TEXT | New value |
| `timestamp` | TEXT | ISO-8601 timestamp |

---

## 10. Configuration

BlackRoad Plane is configured via environment variables or a `.env` file:

| Variable | Default | Description |
|---|---|---|
| `BLACKROAD_DB_PATH` | `~/.blackroad/issues.db` | SQLite database file path |
| `STRIPE_SECRET_KEY` | — | Stripe secret API key (`sk_live_…` or `sk_test_…`) |
| `STRIPE_PUBLISHABLE_KEY` | — | Stripe publishable key (`pk_live_…` or `pk_test_…`) |
| `STRIPE_WEBHOOK_SECRET` | — | Stripe webhook signing secret (`whsec_…`) |
| `STRIPE_PRO_PRICE_ID` | — | Stripe Price ID for the Pro plan |
| `STRIPE_ENTERPRISE_PRICE_ID` | — | Stripe Price ID for the Enterprise plan |

---

## 11. License

Copyright © 2024-2026 BlackRoad OS, Inc. All Rights Reserved.  
See [LICENSE](./LICENSE) for full terms.
