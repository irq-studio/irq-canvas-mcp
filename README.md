# irq-canvas-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server for Canvas LMS integration. Provides tools for course management, assignment handling, discussion facilitation, quizzes, rubrics, and student analytics.

## Installation

```bash
git clone https://github.com/irq-studio/irq-canvas-mcp.git
cd irq-canvas-mcp
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install -e .
```

## Configuration

1. Copy the environment template and fill in your Canvas API credentials:

```bash
cp .env.example .env
```

Required variables in `.env`:

| Variable | Description |
|----------|-------------|
| `CANVAS_API_TOKEN` | Your Canvas API access token |
| `CANVAS_API_URL` | Canvas API base URL (e.g. `https://yourschool.instructure.com/api/v1`) |

2. Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "irq-canvas": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/irq-canvas-mcp",
        "irq-canvas-mcp"
      ]
    }
  }
}
```

See `.mcp.json.example` for a complete example.

## Multi-Instance Setup

To connect to multiple Canvas instances (e.g. production + development, or multiple schools), copy and edit the config template:

```bash
cp config.example.yml config.yml
```

Define each instance with its own URL and token. See `config.example.yml` for the full schema.

## Available Tools

### Courses
- `list_courses` — List all courses
- `get_course_details` — Get details for a specific course
- `get_course_content_overview` — Get content overview (assignments, modules, pages)

### Assignments
- `list_assignments` — List assignments in a course
- `get_assignment_details` — Get assignment details
- `update_assignment` — Update an assignment
- `delete_assignment` / `bulk_delete_assignments` — Delete assignments
- `list_submissions` — List assignment submissions
- `get_assignment_analytics` — Get assignment analytics
- `assign_peer_review` / `list_peer_reviews` — Manage peer reviews

### Discussions & Announcements
- `list_discussion_topics` / `get_discussion_topic_details` — Browse discussions
- `list_discussion_entries` / `get_discussion_entry_details` — Browse entries
- `get_discussion_with_replies` — Get full discussion thread
- `post_discussion_entry` / `reply_to_discussion_entry` — Post and reply
- `create_discussion_topic` / `delete_discussion_topic` — Manage topics
- `list_announcements` / `create_announcement` / `delete_announcement` — Manage announcements
- `bulk_delete_announcements` — Bulk delete announcements

### Pages
- `list_pages` / `get_page_content` / `get_page_details` / `get_front_page` — Read pages
- `create_page` / `edit_page_content` — Write pages
- `publish_page` / `unpublish_page` — Manage page visibility

### Modules
- `list_modules` / `list_module_items` — Browse modules
- `create_module` / `delete_module` / `bulk_delete_modules` — Manage modules
- `publish_module` / `unpublish_module` — Module visibility
- `bulk_publish_modules` / `bulk_unpublish_modules` — Bulk module visibility
- `add_item_to_module` / `add_page_to_module` / `add_assignment_to_module` — Add items
- `add_quiz_to_module` / `add_external_link_to_module` / `add_subheader_to_module` — Add items
- `bulk_add_items_to_module` — Bulk add items
- `delete_module_item` / `bulk_delete_module_items` — Remove items
- `delete_external_links_from_module` — Remove external links
- `update_module_item_indent` / `bulk_update_indent` — Adjust indentation
- `get_module_structure_tree` — Get module tree view

### Quizzes
- `list_quizzes` — List quizzes
- `create_quiz` / `update_quiz` / `rename_quiz` — Manage quizzes
- `delete_quiz` / `bulk_delete_quizzes` — Delete quizzes
- `add_quiz_question` — Add questions
- `import_quiz_from_markdown` — Import quiz from markdown

### Rubrics
- `list_all_rubrics` / `list_assignment_rubrics` — List rubrics
- `get_rubric_details` / `get_assignment_rubric_details` — Get rubric details
- `create_rubric` / `update_rubric` / `delete_rubric` — Manage rubrics
- `associate_rubric_with_assignment` — Link rubric to assignment
- `get_submission_rubric_assessment` / `grade_with_rubric` — Grade with rubrics

### External Tools
- `list_external_tools` / `get_external_tool_details` — Browse LTI tools
- `update_external_tool` — Update tool configuration

### Users & Analytics
- `list_users` / `list_groups` — List users and groups
- `get_student_analytics` — Get student analytics
- `get_anonymization_status` — Check FERPA anonymization status
- `create_student_anonymization_map` — Create anonymized student map

## Privacy & FERPA

This server includes built-in FERPA-compliant data anonymization. Student data is automatically anonymized before being sent to AI models. Configure via:

- `ENABLE_DATA_ANONYMIZATION=true` (default)
- `ANONYMIZATION_DEBUG=false`

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

## Credits

Based on [canvas-mcp](https://github.com/vishalsachdev/canvas-mcp) by Vishal Sachdev.

## License

MIT
