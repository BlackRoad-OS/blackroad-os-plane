# BlackRoad Plane

Issue tracking system inspired by Plane and Linear. Fast, intuitive issue management with cycles, modules, and detailed analytics.

## Features

- **Issues with sequences**: Per-project issue numbering and tracking
- **Cycles**: Sprint-like iterations with burnup/burndown analytics
- **Modules**: Feature/component-based issue grouping
- **Priority & Status**: Flexible issue prioritization and workflow states
- **Bulk operations**: Update multiple issues simultaneously
- **Full-text search**: Filter and find issues across the system
- **Comments & activity**: Discussion threads and change history
- **Analytics**: Velocity, cycle time, priority distribution
- **SQLite backend**: Persistent storage at `~/.blackroad/issues.db`

## Installation

```bash
python -m pip install --upgrade pip
```

## Usage

```bash
# List open issues
python src/issue_tracker.py issues --project PROJECT_ID --status open

# Create an issue
python src/issue_tracker.py create PROJECT_ID bug "Login fails on Safari" --priority high

# View project analytics
python src/issue_tracker.py analytics PROJECT_ID
```

## Database Schema

- `issues`: Issue definitions, metadata, and status
- `cycles`: Sprint/iteration planning and tracking
- `modules`: Feature modules and groupings
- `comments`: Issue discussion and comments
- `issue_activity`: Change history and activity log
