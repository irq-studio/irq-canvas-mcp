"""External Tools (LTI) management tools for Canvas API."""

from typing import Union, Optional, Dict, Any, List
import json
from fastmcp import FastMCP

from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.cache import get_course_id, get_course_code
from ..core.validation import validate_params
from ..core.dates import format_date


def register_external_tool_tools(mcp: FastMCP):
    """Register external tool (LTI) management tools."""

    # ===== EXTERNAL TOOL LIST & READ OPERATIONS =====

    @mcp.tool(name="canvas_list_external_tools")
    @validate_params
    async def list_external_tools(
        course_identifier: Union[str, int],
        search_term: Optional[str] = None,
        placement: Optional[str] = None,
        include_parents: bool = False
    ) -> str:
        """List all external tools (LTI apps) for a specific course.

        Args:
            course_identifier: The Canvas course code or ID
            search_term: Filter by partial tool name
            placement: Filter by placement type (e.g., 'course_navigation', 'assignment_selection')
            include_parents: Include tools from parent accounts

        Returns:
            JSON string with list of external tools including IDs, names, URLs, and configurations
        """
        course_id = await get_course_id(course_identifier)

        params = {"per_page": 100}
        if search_term:
            params["search_term"] = search_term
        if placement:
            params["placement"] = placement
        if include_parents:
            params["include_parents"] = True

        tools = await fetch_all_paginated_results(
            f"/courses/{course_id}/external_tools",
            params
        )

        if isinstance(tools, dict) and "error" in tools:
            return json.dumps({
                "error": f"Failed to fetch external tools: {tools['error']}",
                "course_id": course_id
            })

        if not tools:
            course_display = await get_course_code(course_id) or course_identifier
            return json.dumps({
                "message": f"No external tools found for course {course_display}",
                "course_id": course_id,
                "tools": []
            })

        # Format tool information
        tools_info = []
        for tool in tools:
            tool_info = {
                "id": tool.get("id"),
                "name": tool.get("name"),
                "description": tool.get("description", ""),
                "url": tool.get("url", ""),
                "domain": tool.get("domain", ""),
                "consumer_key": tool.get("consumer_key", ""),
                "privacy_level": tool.get("privacy_level", ""),
                "workflow_state": tool.get("workflow_state", ""),
                "custom_fields": tool.get("custom_fields", {}),
                "created_at": format_date(tool.get("created_at")),
                "updated_at": format_date(tool.get("updated_at"))
            }
            tools_info.append(tool_info)

        course_display = await get_course_code(course_id) or course_identifier
        return json.dumps({
            "course": course_display,
            "course_id": course_id,
            "total_tools": len(tools_info),
            "tools": tools_info
        }, indent=2)

    @mcp.tool(name="canvas_get_ext_tool_details")
    @validate_params
    async def get_external_tool_details(
        course_identifier: Union[str, int],
        tool_id: Union[str, int]
    ) -> str:
        """Get detailed configuration for a specific external tool.

        Args:
            course_identifier: The Canvas course code or ID
            tool_id: The external tool ID

        Returns:
            JSON string with complete tool configuration including placements and custom fields
        """
        course_id = await get_course_id(course_identifier)

        response = await make_canvas_request(
            "get",
            f"/courses/{course_id}/external_tools/{tool_id}"
        )

        if "error" in response:
            return json.dumps({
                "error": f"Failed to fetch tool details: {response['error']}",
                "course_id": course_id,
                "tool_id": tool_id
            })

        # Extract key configuration details
        tool_details = {
            "id": response.get("id"),
            "name": response.get("name"),
            "description": response.get("description", ""),
            "url": response.get("url", ""),
            "domain": response.get("domain", ""),
            "consumer_key": response.get("consumer_key", ""),
            "privacy_level": response.get("privacy_level", ""),
            "workflow_state": response.get("workflow_state", ""),
            "custom_fields": response.get("custom_fields", {}),
            "text": response.get("text", ""),
            "icon_url": response.get("icon_url", ""),
            "vendor_help_link": response.get("vendor_help_link", ""),
            "is_rce_favorite": response.get("is_rce_favorite", False),
            "created_at": format_date(response.get("created_at")),
            "updated_at": format_date(response.get("updated_at")),
            # Include any placement configurations
            "placements": {}
        }

        # Extract placement configurations (e.g., course_navigation, assignment_selection)
        placement_types = [
            "course_navigation", "assignment_selection", "link_selection",
            "editor_button", "homework_submission", "migration_selection",
            "user_navigation", "account_navigation", "similarity_detection"
        ]

        for placement_type in placement_types:
            if placement_type in response:
                tool_details["placements"][placement_type] = response[placement_type]

        course_display = await get_course_code(course_id) or course_identifier
        return json.dumps({
            "course": course_display,
            "course_id": course_id,
            "tool": tool_details
        }, indent=2)

    # ===== EXTERNAL TOOL UPDATE OPERATIONS =====

    @mcp.tool(name="canvas_update_external_tool")
    @validate_params
    async def update_external_tool(
        course_identifier: Union[str, int],
        tool_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        domain: Optional[str] = None,
        privacy_level: Optional[str] = None,
        custom_fields: Optional[str] = None,
        consumer_key: Optional[str] = None,
        shared_secret: Optional[str] = None
    ) -> str:
        """Update an existing external tool configuration.

        Args:
            course_identifier: The Canvas course code or ID
            tool_id: The external tool ID to update
            name: New tool name
            description: New tool description
            url: New launch URL
            domain: New domain
            privacy_level: New privacy level ('anonymous', 'name_only', 'email_only', 'public')
            custom_fields: JSON string of custom fields (e.g., '{"email": "user@example.com"}')
            consumer_key: New consumer key (if changing)
            shared_secret: New shared secret (required if changing authentication)

        Returns:
            JSON string with updated tool configuration or error message
        """
        course_id = await get_course_id(course_identifier)

        # Build update payload
        payload = {}

        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if url is not None:
            payload["url"] = url
        if domain is not None:
            payload["domain"] = domain
        if privacy_level is not None:
            if privacy_level not in ["anonymous", "name_only", "email_only", "public"]:
                return json.dumps({
                    "error": f"Invalid privacy_level: {privacy_level}. Must be one of: anonymous, name_only, email_only, public",
                    "course_id": course_id,
                    "tool_id": tool_id
                })
            payload["privacy_level"] = privacy_level
        if consumer_key is not None:
            payload["consumer_key"] = consumer_key
        if shared_secret is not None:
            payload["shared_secret"] = shared_secret

        # Handle custom fields
        if custom_fields is not None:
            try:
                fields_dict = json.loads(custom_fields) if isinstance(custom_fields, str) else custom_fields
                # Canvas expects custom_fields[field_name] format
                for field_name, field_value in fields_dict.items():
                    payload[f"custom_fields[{field_name}]"] = field_value
            except json.JSONDecodeError as e:
                return json.dumps({
                    "error": f"Invalid JSON for custom_fields: {str(e)}",
                    "course_id": course_id,
                    "tool_id": tool_id
                })

        if not payload:
            return json.dumps({
                "error": "No update parameters provided",
                "course_id": course_id,
                "tool_id": tool_id
            })

        response = await make_canvas_request(
            "put",
            f"/courses/{course_id}/external_tools/{tool_id}",
            data=payload
        )

        if "error" in response:
            return json.dumps({
                "error": f"Failed to update external tool: {response['error']}",
                "course_id": course_id,
                "tool_id": tool_id,
                "attempted_updates": list(payload.keys())
            })

        course_display = await get_course_code(course_id) or course_identifier
        return json.dumps({
            "success": True,
            "message": f"Successfully updated external tool '{response.get('name')}'",
            "course": course_display,
            "course_id": course_id,
            "tool_id": response.get("id"),
            "updated_fields": list(payload.keys()),
            "tool": {
                "id": response.get("id"),
                "name": response.get("name"),
                "url": response.get("url"),
                "domain": response.get("domain"),
                "privacy_level": response.get("privacy_level"),
                "custom_fields": response.get("custom_fields", {}),
                "updated_at": format_date(response.get("updated_at"))
            }
        }, indent=2)
