"""Other MCP tools for Canvas API (pages, users, analytics)."""

from typing import Union, Optional
from fastmcp import FastMCP

from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.cache import get_course_id, get_course_code
from ..core.validation import validate_params
from ..core.dates import format_date, truncate_text
from ..core.anonymization import anonymize_response_data


def register_other_tools(mcp: FastMCP):
    """Register other MCP tools (pages, users, analytics)."""

    # ===== PAGE TOOLS =====
    
    @mcp.tool(name="canvas_list_pages")
    @validate_params
    async def list_pages(course_identifier: Union[str, int],
                        sort: Optional[str] = "title", 
                        order: Optional[str] = "asc",
                        search_term: Optional[str] = None,
                        published: Optional[bool] = None) -> str:
        """List pages for a specific course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            sort: Sort criteria ('title', 'created_at', 'updated_at')
            order: Sort order ('asc' or 'desc')
            search_term: Search for pages containing this term in title or body
            published: Filter by published status (True, False, or None for all)
        """
        course_id = await get_course_id(course_identifier)
        
        params = {"per_page": 100}
        
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
        if search_term:
            params["search_term"] = search_term
        if published is not None:
            params["published"] = published
        
        pages = await fetch_all_paginated_results(f"/courses/{course_id}/pages", params)
        
        if isinstance(pages, dict) and "error" in pages:
            return f"Error fetching pages: {pages['error']}"
        
        if not pages:
            return f"No pages found for course {course_identifier}."
        
        pages_info = []
        for page in pages:
            url = page.get("url", "No URL")
            title = page.get("title", "Untitled page")
            published_status = "Published" if page.get("published", False) else "Unpublished"
            is_front_page = page.get("front_page", False)
            updated_at = format_date(page.get("updated_at"))
            
            front_page_indicator = " (Front Page)" if is_front_page else ""
            
            pages_info.append(
                f"URL: {url}\nTitle: {title}{front_page_indicator}\nStatus: {published_status}\nUpdated: {updated_at}\n"
            )
        
        course_display = await get_course_code(course_id) or course_identifier
        return f"Pages for Course {course_display}:\n\n" + "\n".join(pages_info)

    @mcp.tool(name="canvas_get_page_content")
    @validate_params
    async def get_page_content(course_identifier: Union[str, int], page_url_or_id: str) -> str:
        """Get the full content body of a specific page.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            page_url_or_id: The page URL or page ID
        """
        course_id = await get_course_id(course_identifier)
        
        response = await make_canvas_request("get", f"/courses/{course_id}/pages/{page_url_or_id}")
        
        if "error" in response:
            return f"Error fetching page content: {response['error']}"
        
        title = response.get("title", "Untitled")
        body = response.get("body", "")
        published = response.get("published", False)
        
        if not body:
            return f"Page '{title}' has no content."
        
        course_display = await get_course_code(course_id) or course_identifier
        status = "Published" if published else "Unpublished"
        
        return f"Page Content for '{title}' in Course {course_display} ({status}):\n\n{body}"

    @mcp.tool(name="canvas_get_page_details")
    @validate_params
    async def get_page_details(course_identifier: Union[str, int], page_url_or_id: str) -> str:
        """Get detailed information about a specific page.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            page_url_or_id: The page URL or page ID
        """
        course_id = await get_course_id(course_identifier)
        
        response = await make_canvas_request("get", f"/courses/{course_id}/pages/{page_url_or_id}")
        
        if "error" in response:
            return f"Error fetching page details: {response['error']}"
        
        title = response.get("title", "Untitled")
        url = response.get("url", "N/A")
        body = response.get("body", "")
        created_at = format_date(response.get("created_at"))
        updated_at = format_date(response.get("updated_at"))
        published = response.get("published", False)
        front_page = response.get("front_page", False)
        locked_for_user = response.get("locked_for_user", False)
        editing_roles = response.get("editing_roles", "")
        
        # Handle last edited by user info
        last_edited_by = response.get("last_edited_by", {})
        editor_name = last_edited_by.get("display_name", "Unknown") if last_edited_by else "Unknown"
        
        # Clean up body text for display
        if body:
            # Remove HTML tags for cleaner display
            import re
            body_clean = re.sub(r'<[^>]+>', '', body)
            body_clean = body_clean.strip()
            if len(body_clean) > 500:
                body_clean = body_clean[:500] + "..."
        else:
            body_clean = "No content"
        
        status_info = []
        if published:
            status_info.append("Published")
        else:
            status_info.append("Unpublished")
        
        if front_page:
            status_info.append("Front Page")
        
        if locked_for_user:
            status_info.append("Locked")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Page Details for Course {course_display}:\n\n"
        result += f"Title: {title}\n"
        result += f"URL: {url}\n"
        result += f"Status: {', '.join(status_info)}\n"
        result += f"Created: {created_at}\n"
        result += f"Updated: {updated_at}\n"
        result += f"Last Edited By: {editor_name}\n"
        result += f"Editing Roles: {editing_roles or 'Not specified'}\n"
        result += f"\nContent Preview:\n{body_clean}"
        
        return result

    @mcp.tool(name="canvas_get_front_page")
    @validate_params
    async def get_front_page(course_identifier: Union[str, int]) -> str:
        """Get the front page content for a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
        """
        course_id = await get_course_id(course_identifier)
        
        response = await make_canvas_request("get", f"/courses/{course_id}/front_page")
        
        if "error" in response:
            return f"Error fetching front page: {response['error']}"
        
        title = response.get("title", "Untitled")
        body = response.get("body", "")
        updated_at = format_date(response.get("updated_at"))
        
        if not body:
            return f"Course front page '{title}' has no content."
        
        # Try to get the course code for display
        course_display = await get_course_code(course_id) or course_identifier
        return f"Front Page '{title}' for Course {course_display} (Updated: {updated_at}):\n\n{body}"

    @mcp.tool(name="canvas_create_page")
    @validate_params
    async def create_page(course_identifier: Union[str, int],
                         title: str,
                         body: str,
                         published: bool = True,
                         front_page: bool = False,
                         editing_roles: str = "teachers") -> str:
        """Create a new page in a Canvas course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            title: The title of the new page
            body: The HTML content for the page
            published: Whether the page should be published (default: True)
            front_page: Whether this should be the course front page (default: False)
            editing_roles: Who can edit the page (default: "teachers")
        """
        course_id = await get_course_id(course_identifier)
        
        data = {
            "wiki_page": {
                "title": title,
                "body": body,
                "published": published,
                "front_page": front_page,
                "editing_roles": editing_roles
            }
        }
        
        response = await make_canvas_request("post", f"/courses/{course_id}/pages", data=data)
        
        if "error" in response:
            return f"Error creating page: {response['error']}"
        
        page_url = response.get("url", "")
        page_title = response.get("title", title)
        created_at = format_date(response.get("created_at"))
        published_status = "Published" if response.get("published", False) else "Unpublished"
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully created page in Course {course_display}:\n\n"
        result += f"Title: {page_title}\n"
        result += f"URL: {page_url}\n"
        result += f"Status: {published_status}\n"
        result += f"Created: {created_at}\n"
        
        if front_page:
            result += f"Set as front page: Yes\n"
        
        return result

    @mcp.tool(name="canvas_edit_page_content")
    @validate_params
    async def edit_page_content(course_identifier: Union[str, int],
                               page_url_or_id: str, 
                               new_content: str,
                               title: Optional[str] = None) -> str:
        """Edit the content of a specific page.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            page_url_or_id: The page URL or page ID
            new_content: The new HTML content for the page
            title: Optional new title for the page
        """
        course_id = await get_course_id(course_identifier)
        
        # Prepare the data for updating the page
        update_data = {
            "wiki_page": {
                "body": new_content
            }
        }
        
        if title:
            update_data["wiki_page"]["title"] = title
        
        # Update the page
        response = await make_canvas_request(
            "put", 
            f"/courses/{course_id}/pages/{page_url_or_id}",
            data=update_data
        )
        
        if "error" in response:
            return f"Error updating page: {response['error']}"
        
        page_title = response.get("title", "Unknown page")
        updated_at = format_date(response.get("updated_at"))
        course_display = await get_course_code(course_id) or course_identifier
        
        return f"Successfully updated page '{page_title}' in course {course_display}. Last updated: {updated_at}"

    @mcp.tool(name="canvas_unpublish_page")
    @validate_params
    async def unpublish_page(course_identifier: Union[str, int], page_url_or_id: str) -> str:
        """Unpublish a specific page in a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            page_url_or_id: The page URL or page ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Prepare the data for unpublishing the page
        update_data = {
            "wiki_page": {
                "published": False
            }
        }
        
        # Update the page to unpublish it
        response = await make_canvas_request(
            "put", 
            f"/courses/{course_id}/pages/{page_url_or_id}",
            data=update_data
        )
        
        if "error" in response:
            return f"Error unpublishing page: {response['error']}"
        
        page_title = response.get("title", "Unknown page")
        updated_at = format_date(response.get("updated_at"))
        course_display = await get_course_code(course_id) or course_identifier
        
        return f"Successfully unpublished page '{page_title}' in course {course_display}. Last updated: {updated_at}"

    @mcp.tool(name="canvas_publish_page")
    @validate_params
    async def publish_page(course_identifier: Union[str, int], page_url_or_id: str) -> str:
        """Publish a specific page in a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            page_url_or_id: The page URL or page ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Prepare the data for publishing the page
        update_data = {
            "wiki_page": {
                "published": True
            }
        }
        
        # Update the page to publish it
        response = await make_canvas_request(
            "put", 
            f"/courses/{course_id}/pages/{page_url_or_id}",
            data=update_data
        )
        
        if "error" in response:
            return f"Error publishing page: {response['error']}"
        
        page_title = response.get("title", "Unknown page")
        updated_at = format_date(response.get("updated_at"))
        course_display = await get_course_code(course_id) or course_identifier
        
        return f"Successfully published page '{page_title}' in course {course_display}. Last updated: {updated_at}"

    @mcp.tool(name="canvas_get_anon_status")
    async def get_anonymization_status() -> str:
        """Get current data anonymization status and statistics.
        
        Returns:
            Status information about data anonymization
        """
        from ..core.config import get_config
        from ..core.anonymization import get_anonymization_stats
        
        config = get_config()
        stats = get_anonymization_stats()
        
        result = "🔒 Data Anonymization Status:\n\n"
        
        if config.enable_data_anonymization:
            result += "✅ **ANONYMIZATION ENABLED** - Student data is protected\n\n"
            result += f"📊 Session Statistics:\n"
            result += f"  • Total unique students anonymized: {stats['total_anonymized_ids']}\n"
            result += f"  • Privacy protection: {stats['privacy_status']}\n"
            result += f"  • Debug logging: {'ON' if config.anonymization_debug else 'OFF'}\n\n"
            
            result += "🛡️ **FERPA Compliance**: Data anonymized before AI processing\n"
            result += "📍 **Data Location**: All processing happens locally on your machine\n"
            
        else:
            result += "⚠️ **ANONYMIZATION DISABLED** - Student data is NOT protected\n\n"
            result += "🚨 **PRIVACY RISK**: Real student names and data sent to AI\n"
            result += "⚖️ **COMPLIANCE**: May violate FERPA requirements\n\n"
            result += "💡 **Recommendation**: Enable anonymization in your .env file:\n"
            result += "   ENABLE_DATA_ANONYMIZATION=true\n"
        
        return result
    
    @mcp.tool(name="canvas_list_modules")
    @validate_params
    async def list_modules(course_identifier: Union[str, int],
                          include_items: bool = False) -> str:
        """List all modules in a Canvas course with their IDs and publishing status.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            include_items: Whether to include module items in the output
        """
        course_id = await get_course_id(course_identifier)
        
        params = {"per_page": 100}
        if include_items:
            params["include[]"] = ["items"]
        
        modules = await fetch_all_paginated_results(f"/courses/{course_id}/modules", params)
        
        if isinstance(modules, dict) and "error" in modules:
            return f"Error fetching modules: {modules['error']}"
        
        if not modules:
            return f"No modules found for course {course_identifier}."
        
        course_display = await get_course_code(course_id) or course_identifier
        result = f"Modules for Course {course_display}:\n\n"
        
        for module in modules:
            module_id = module.get("id")
            module_name = module.get("name", "Untitled module")
            position = module.get("position", "Unknown")
            published = module.get("published", False)
            state = module.get("state", "completed")
            items_count = module.get("items_count", 0)
            
            published_status = "Published" if published else "Unpublished"
            
            result += f"Module: {module_name}\n"
            result += f"ID: {module_id}\n"
            result += f"Position: {position}\n"
            result += f"Status: {published_status}\n"
            result += f"State: {state}\n"
            result += f"Items Count: {items_count}\n"
            
            if include_items and "items" in module:
                items = module["items"]
                if items:
                    result += f"Items:\n"
                    for item in items:
                        item_title = item.get("title", "Untitled")
                        item_type = item.get("type", "Unknown")
                        item_published = item.get("published", False)
                        item_status = "Published" if item_published else "Unpublished"
                        result += f"  - {item_title} ({item_type}) - {item_status}\n"
                else:
                    result += f"Items: None\n"
            
            result += "\n"
        
        return result

    @mcp.tool(name="canvas_create_module")
    @validate_params
    async def create_module(course_identifier: Union[str, int],
                          name: str,
                          position: Optional[int] = None,
                          require_sequential_progress: bool = False,
                          prerequisite_module_ids: Optional[list] = None,
                          publish_final_grade: bool = False,
                          unlock_at: Optional[str] = None,
                          published: bool = True) -> str:
        """Create a new module in a Canvas course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            name: The name of the new module
            position: The position of the module in the course (1 = first position)
            require_sequential_progress: Whether students must complete items in order
            prerequisite_module_ids: List of module IDs that must be completed first
            publish_final_grade: Whether to publish final grade upon completion
            unlock_at: When to unlock this module (ISO 8601 format)
            published: Whether the module should be published (default: True)
        """
        course_id = await get_course_id(course_identifier)
        
        data = {
            "module": {
                "name": name,
                "published": published,
                "require_sequential_progress": require_sequential_progress,
                "publish_final_grade": publish_final_grade
            }
        }
        
        if position is not None:
            data["module"]["position"] = position
        
        if prerequisite_module_ids:
            data["module"]["prerequisite_module_ids"] = prerequisite_module_ids
        
        if unlock_at:
            data["module"]["unlock_at"] = unlock_at
        
        response = await make_canvas_request("post", f"/courses/{course_id}/modules", data=data)
        
        if "error" in response:
            return f"Error creating module: {response['error']}"
        
        module_id = response.get("id")
        module_name = response.get("name", name)
        module_position = response.get("position")
        created_at = format_date(response.get("created_at"))
        published_status = "Published" if response.get("published", False) else "Unpublished"
        state = response.get("state", "completed")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully created module in Course {course_display}:\n\n"
        result += f"Module Name: {module_name}\n"
        result += f"Module ID: {module_id}\n"
        result += f"Position: {module_position}\n"
        result += f"Status: {published_status}\n"
        result += f"State: {state}\n"
        result += f"Created: {created_at}\n"
        
        if require_sequential_progress:
            result += f"Sequential Progress: Required\n"
        
        if prerequisite_module_ids:
            result += f"Prerequisites: {', '.join(map(str, prerequisite_module_ids))}\n"
        
        if unlock_at:
            result += f"Unlock Date: {format_date(unlock_at)}\n"
        
        return result

    @mcp.tool(name="canvas_unpublish_module")
    @validate_params
    async def unpublish_module(course_identifier: Union[str, int], module_id: Union[str, int]) -> str:
        """Unpublish a specific module in a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Prepare the data for unpublishing the module
        update_data = {
            "module": {
                "published": False
            }
        }
        
        # Update the module to unpublish it
        response = await make_canvas_request(
            "put", 
            f"/courses/{course_id}/modules/{module_id}",
            data=update_data
        )
        
        if "error" in response:
            return f"Error unpublishing module: {response['error']}"
        
        module_name = response.get("name", "Unknown module")
        module_position = response.get("position", "Unknown")
        updated_at = format_date(response.get("updated_at"))
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully unpublished module in Course {course_display}:\n\n"
        result += f"Module Name: {module_name}\n"
        result += f"Module ID: {module_id}\n"
        result += f"Position: {module_position}\n"
        result += f"Status: Unpublished\n"
        result += f"Last updated: {updated_at}\n"
        
        return result

    @mcp.tool(name="canvas_publish_module")
    @validate_params
    async def publish_module(course_identifier: Union[str, int], module_id: Union[str, int]) -> str:
        """Publish a specific module in a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Prepare the data for publishing the module
        update_data = {
            "module": {
                "published": True
            }
        }
        
        # Update the module to publish it
        response = await make_canvas_request(
            "put", 
            f"/courses/{course_id}/modules/{module_id}",
            data=update_data
        )
        
        if "error" in response:
            return f"Error publishing module: {response['error']}"
        
        module_name = response.get("name", "Unknown module")
        module_position = response.get("position", "Unknown")
        updated_at = format_date(response.get("updated_at"))
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully published module in Course {course_display}:\n\n"
        result += f"Module Name: {module_name}\n"
        result += f"Module ID: {module_id}\n"
        result += f"Position: {module_position}\n"
        result += f"Status: Published\n"
        result += f"Last updated: {updated_at}\n"
        
        return result

    @mcp.tool(name="canvas_bulk_unpub_modules")
    @validate_params
    async def bulk_unpublish_modules(course_identifier: Union[str, int],
                                   module_ids: Optional[list] = None,
                                   unpublish_all: bool = False) -> str:
        """Unpublish multiple modules at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_ids: List of module IDs to unpublish (e.g., [123, 456, 789])
            unpublish_all: If True, unpublish ALL modules in the course (overrides module_ids)
        """
        course_id = await get_course_id(course_identifier)
        
        if unpublish_all:
            # Get all modules first
            modules = await fetch_all_paginated_results(f"/courses/{course_id}/modules", {"per_page": 100})
            if isinstance(modules, dict) and "error" in modules:
                return f"Error fetching modules: {modules['error']}"
            
            module_ids = [module.get("id") for module in modules if module.get("published", False)]
            if not module_ids:
                return f"No published modules found to unpublish in course {course_identifier}."
        
        if not module_ids:
            return "No module IDs provided. Use module_ids parameter or set unpublish_all=true."
        
        # Convert to list of integers if needed
        try:
            module_ids = [int(mid) for mid in module_ids]
        except (ValueError, TypeError):
            return "Error: module_ids must be a list of integers."
        
        results = []
        errors = []
        
        for module_id in module_ids:
            update_data = {
                "module": {
                    "published": False
                }
            }
            
            response = await make_canvas_request(
                "put", 
                f"/courses/{course_id}/modules/{module_id}",
                data=update_data
            )
            
            if "error" in response:
                errors.append(f"Module {module_id}: {response['error']}")
            else:
                module_name = response.get("name", f"Module {module_id}")
                results.append(f"✅ {module_name} (ID: {module_id})")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Unpublish Results for Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully unpublished {len(results)} modules:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to unpublish {len(errors)} modules:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No modules were processed.\n"
        
        return result

    @mcp.tool(name="canvas_bulk_pub_modules")
    @validate_params
    async def bulk_publish_modules(course_identifier: Union[str, int],
                                 module_ids: Optional[list] = None,
                                 publish_all: bool = False) -> str:
        """Publish multiple modules at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_ids: List of module IDs to publish (e.g., [123, 456, 789])
            publish_all: If True, publish ALL modules in the course (overrides module_ids)
        """
        course_id = await get_course_id(course_identifier)
        
        if publish_all:
            # Get all modules first
            modules = await fetch_all_paginated_results(f"/courses/{course_id}/modules", {"per_page": 100})
            if isinstance(modules, dict) and "error" in modules:
                return f"Error fetching modules: {modules['error']}"
            
            module_ids = [module.get("id") for module in modules if not module.get("published", True)]
            if not module_ids:
                return f"No unpublished modules found to publish in course {course_identifier}."
        
        if not module_ids:
            return "No module IDs provided. Use module_ids parameter or set publish_all=true."
        
        # Convert to list of integers if needed
        try:
            module_ids = [int(mid) for mid in module_ids]
        except (ValueError, TypeError):
            return "Error: module_ids must be a list of integers."
        
        results = []
        errors = []
        
        for module_id in module_ids:
            update_data = {
                "module": {
                    "published": True
                }
            }
            
            response = await make_canvas_request(
                "put", 
                f"/courses/{course_id}/modules/{module_id}",
                data=update_data
            )
            
            if "error" in response:
                errors.append(f"Module {module_id}: {response['error']}")
            else:
                module_name = response.get("name", f"Module {module_id}")
                results.append(f"✅ {module_name} (ID: {module_id})")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Publish Results for Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully published {len(results)} modules:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to publish {len(errors)} modules:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No modules were processed.\n"
        
        return result

    @mcp.tool(name="canvas_list_module_items")
    @validate_params
    async def list_module_items(course_identifier: Union[str, int],
                               module_id: Union[str, int],
                               include_content_details: bool = True) -> str:
        """List items within a specific module, including pages.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
            include_content_details: Whether to include additional details about content items
        """
        course_id = await get_course_id(course_identifier)
        
        params = {"per_page": 100}
        if include_content_details:
            params["include[]"] = ["content_details"]
        
        items = await fetch_all_paginated_results(
            f"/courses/{course_id}/modules/{module_id}/items", params
        )
        
        if isinstance(items, dict) and "error" in items:
            return f"Error fetching module items: {items['error']}"
        
        if not items:
            return f"No items found in module {module_id}."
        
        # Get module details for context
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        course_display = await get_course_code(course_id) or course_identifier
        result = f"Module Items for '{module_name}' in Course {course_display}:\n\n"
        
        for item in items:
            item_id = item.get("id")
            title = item.get("title", "Untitled")
            item_type = item.get("type", "Unknown")
            content_id = item.get("content_id")
            url = item.get("url", "")
            external_url = item.get("external_url", "")
            published = item.get("published", False)
            position = item.get("position", "Unknown")
            indent = item.get("indent", 0)
            
            # Create visual indentation representation
            indent_visual = "  " * indent  # 2 spaces per indent level
            indent_indicator = f"[Indent: {indent}]" if indent > 0 else "[No Indent]"
            
            result += f"{indent_visual}📄 {title}\n"
            result += f"{indent_visual}   Type: {item_type}\n"
            result += f"{indent_visual}   ID: {item_id}\n"
            result += f"{indent_visual}   Position: {position}\n"
            result += f"{indent_visual}   Indentation: {indent_indicator}\n"
            if content_id:
                result += f"{indent_visual}   Content ID: {content_id}\n"
            if url:
                result += f"{indent_visual}   URL: {url}\n"
            if external_url:
                result += f"{indent_visual}   External URL: {external_url}\n"
            result += f"{indent_visual}   Published: {'Yes' if published else 'No'}\n\n"
        
        return result

    @mcp.tool(name="canvas_delete_module_item")
    @validate_params
    async def delete_module_item(course_identifier: Union[str, int],
                               module_id: Union[str, int], 
                               item_id: Union[str, int]) -> str:
        """Delete a specific item from a module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
            item_id: The module item ID to delete
        """
        course_id = await get_course_id(course_identifier)
        
        # First get the item details before deleting
        item_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}/items/{item_id}"
        )
        
        item_title = "Unknown item"
        item_type = "Unknown type"
        if "error" not in item_response:
            item_title = item_response.get("title", "Unknown item")
            item_type = item_response.get("type", "Unknown type")
        
        # Delete the module item
        response = await make_canvas_request(
            "delete", f"/courses/{course_id}/modules/{module_id}/items/{item_id}"
        )
        
        if "error" in response:
            return f"Error deleting module item: {response['error']}"
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully deleted module item from Course {course_display}:\n\n"
        result += f"Item: {item_title}\n"
        result += f"Type: {item_type}\n"
        result += f"Item ID: {item_id}\n"
        result += f"Module ID: {module_id}\n"
        
        return result

    @mcp.tool(name="canvas_bulk_del_mod_items")
    @validate_params
    async def bulk_delete_module_items(course_identifier: Union[str, int],
                                     module_id: Union[str, int],
                                     item_ids: Optional[list] = None,
                                     item_type_filter: Optional[str] = None,
                                     delete_all_items: bool = False) -> str:
        """Delete multiple items from a module at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
            item_ids: List of specific item IDs to delete (e.g., [123, 456, 789])
            item_type_filter: Delete only items of this type (e.g., "ExternalTool", "Assignment", "Page")
            delete_all_items: If True, delete ALL items in the module (overrides other parameters)
        """
        course_id = await get_course_id(course_identifier)
        
        # Get all items in the module first
        items = await fetch_all_paginated_results(
            f"/courses/{course_id}/modules/{module_id}/items", {"per_page": 100}
        )
        
        if isinstance(items, dict) and "error" in items:
            return f"Error fetching module items: {items['error']}"
        
        if not items:
            return f"No items found in module {module_id}."
        
        # Determine which items to delete
        items_to_delete = []
        
        if delete_all_items:
            items_to_delete = items
        elif item_type_filter:
            items_to_delete = [item for item in items if item.get("type") == item_type_filter]
        elif item_ids:
            # Convert to integers for comparison
            try:
                item_ids_int = [int(iid) for iid in item_ids]
                items_to_delete = [item for item in items if item.get("id") in item_ids_int]
            except (ValueError, TypeError):
                return "Error: item_ids must be a list of integers."
        else:
            return "No deletion criteria specified. Use item_ids, item_type_filter, or delete_all_items=true."
        
        if not items_to_delete:
            filter_desc = ""
            if item_type_filter:
                filter_desc = f" of type '{item_type_filter}'"
            elif item_ids:
                filter_desc = f" with specified IDs"
            return f"No items found{filter_desc} to delete in module {module_id}."
        
        # Delete items one by one
        results = []
        errors = []
        
        for item in items_to_delete:
            item_id = item.get("id")
            item_title = item.get("title", "Unknown item")
            item_type = item.get("type", "Unknown type")
            
            response = await make_canvas_request(
                "delete", f"/courses/{course_id}/modules/{module_id}/items/{item_id}"
            )
            
            if "error" in response:
                errors.append(f"Item '{item_title}' (ID: {item_id}): {response['error']}")
            else:
                results.append(f"✅ {item_title} ({item_type}, ID: {item_id})")
        
        # Get module details for context
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Delete Results for Module '{module_name}' in Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully deleted {len(results)} items:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to delete {len(errors)} items:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No items were processed.\n"
        
        return result

    @mcp.tool(name="canvas_del_ext_links_module")
    @validate_params
    async def delete_external_links_from_module(course_identifier: Union[str, int],
                                              module_id: Union[str, int]) -> str:
        """Delete all external links (ExternalTool items) from a specific module.
        
        This is a convenience function specifically for removing external links/tools from modules.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
        """
        return await bulk_delete_module_items(
            course_identifier=course_identifier,
            module_id=module_id,
            item_type_filter="ExternalTool"
        )

    @mcp.tool(name="canvas_add_item_to_module")
    @validate_params
    async def add_item_to_module(course_identifier: Union[str, int],
                               module_id: Union[str, int],
                               item_type: str,
                               content_id: Optional[Union[str, int]] = None,
                               title: Optional[str] = None,
                               url: Optional[str] = None,
                               external_url: Optional[str] = None,
                               position: Optional[int] = None,
                               indent: Optional[int] = None,
                               new_tab: Optional[bool] = None) -> str:
        """Add an item to a Canvas module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add the item to
            item_type: Type of item ('Assignment', 'Quiz', 'File', 'Page', 'Discussion', 'ExternalUrl', 'ExternalTool', 'SubHeader')
            content_id: The Canvas ID of the content (for Assignment, Quiz, File, Page, Discussion)
            title: Display title for the item (required for SubHeader, ExternalUrl, ExternalTool)
            url: Canvas URL for Page items (page slug/url)
            external_url: External URL for ExternalUrl items
            position: Position in the module (1 = first)
            indent: Indentation level (0-3)
            new_tab: Whether external links should open in new tab
        """
        course_id = await get_course_id(course_identifier)
        
        # Validate item_type
        valid_types = ['Assignment', 'Quiz', 'File', 'Page', 'Discussion', 'ExternalUrl', 'ExternalTool', 'SubHeader']
        if item_type not in valid_types:
            return f"Error: item_type must be one of: {', '.join(valid_types)}"
        
        # Build the module item data
        item_data = {
            "module_item": {
                "type": item_type
            }
        }
        
        # Set content_id for content-based items (except Page which uses page_url)
        if item_type in ['Assignment', 'Quiz', 'File', 'Discussion']:
            if not content_id:
                return f"Error: content_id is required for {item_type} items"
            item_data["module_item"]["content_id"] = str(content_id)
        
        # Page items use page_url instead of content_id
        if item_type == 'Page':
            if not url:
                return "Error: url (page URL/slug) is required for Page items"
            item_data["module_item"]["page_url"] = url
        
        # Set title (required for some types)
        if title:
            item_data["module_item"]["title"] = title
        elif item_type in ['SubHeader', 'ExternalUrl', 'ExternalTool']:
            return f"Error: title is required for {item_type} items"
        
        # Set external URL
        if item_type == 'ExternalUrl':
            if not external_url:
                return "Error: external_url is required for ExternalUrl items"
            item_data["module_item"]["external_url"] = external_url
        
        # Set optional parameters
        if position is not None:
            item_data["module_item"]["position"] = position
        
        if indent is not None:
            if indent < 0 or indent > 3:
                return "Error: indent must be between 0 and 3"
            item_data["module_item"]["indent"] = indent
        
        if new_tab is not None:
            item_data["module_item"]["new_tab"] = new_tab
        
        # Create the module item
        response = await make_canvas_request(
            "post", 
            f"/courses/{course_id}/modules/{module_id}/items",
            data=item_data
        )
        
        if "error" in response:
            return f"Error adding item to module: {response['error']}"
        
        # Get module details for context
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        item_id = response.get("id")
        item_title = response.get("title", title or "Untitled")
        item_position = response.get("position", "Unknown")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully added item to Module '{module_name}' in Course {course_display}:\n\n"
        result += f"Item: {item_title}\n"
        result += f"Type: {item_type}\n"
        result += f"Item ID: {item_id}\n"
        result += f"Position: {item_position}\n"
        
        if content_id:
            result += f"Content ID: {content_id}\n"
        if url and item_type == 'Page':
            result += f"Page URL: {url}\n"
        if external_url:
            result += f"External URL: {external_url}\n"
        if indent is not None:
            result += f"Indent Level: {indent}\n"
        
        return result

    @mcp.tool(name="canvas_add_page_to_module")
    @validate_params
    async def add_page_to_module(course_identifier: Union[str, int],
                               module_id: Union[str, int],
                               page_url: str,
                               title: Optional[str] = None,
                               position: Optional[int] = None,
                               indent: Optional[int] = None) -> str:
        """Add a page to a Canvas module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add the page to
            page_url: The Canvas page URL/slug
            title: Display title for the page (optional, uses page title if not provided)
            position: Position in the module (1 = first)
            indent: Indentation level (0-3)
        """
        return await add_item_to_module(
            course_identifier=course_identifier,
            module_id=module_id,
            item_type="Page",
            url=page_url,
            title=title,
            position=position,
            indent=indent
        )

    @mcp.tool(name="canvas_add_assign_to_module")
    @validate_params
    async def add_assignment_to_module(course_identifier: Union[str, int],
                                     module_id: Union[str, int],
                                     assignment_id: Union[str, int],
                                     title: Optional[str] = None,
                                     position: Optional[int] = None,
                                     indent: Optional[int] = None) -> str:
        """Add an assignment to a Canvas module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add the assignment to
            assignment_id: The Canvas assignment ID
            title: Display title for the assignment (optional, uses assignment title if not provided)
            position: Position in the module (1 = first)
            indent: Indentation level (0-3)
        """
        return await add_item_to_module(
            course_identifier=course_identifier,
            module_id=module_id,
            item_type="Assignment",
            content_id=assignment_id,
            title=title,
            position=position,
            indent=indent
        )

    @mcp.tool(name="canvas_add_quiz_to_module")
    @validate_params
    async def add_quiz_to_module(course_identifier: Union[str, int],
                               module_id: Union[str, int],
                               quiz_id: Union[str, int],
                               title: Optional[str] = None,
                               position: Optional[int] = None,
                               indent: Optional[int] = None) -> str:
        """Add a quiz to a Canvas module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add the quiz to
            quiz_id: The Canvas quiz ID
            title: Display title for the quiz (optional, uses quiz title if not provided)
            position: Position in the module (1 = first)
            indent: Indentation level (0-3)
        """
        return await add_item_to_module(
            course_identifier=course_identifier,
            module_id=module_id,
            item_type="Quiz",
            content_id=quiz_id,
            title=title,
            position=position,
            indent=indent
        )

    @mcp.tool(name="canvas_add_ext_link_module")
    @validate_params
    async def add_external_link_to_module(course_identifier: Union[str, int],
                                        module_id: Union[str, int],
                                        url: str,
                                        title: str,
                                        position: Optional[int] = None,
                                        indent: Optional[int] = None,
                                        new_tab: bool = True) -> str:
        """Add an external link to a Canvas module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add the link to
            url: The external URL to link to
            title: Display title for the link
            position: Position in the module (1 = first)
            indent: Indentation level (0-3)
            new_tab: Whether the link should open in a new tab (default: True)
        """
        return await add_item_to_module(
            course_identifier=course_identifier,
            module_id=module_id,
            item_type="ExternalUrl",
            external_url=url,
            title=title,
            position=position,
            indent=indent,
            new_tab=new_tab
        )

    @mcp.tool(name="canvas_add_subheader_module")
    @validate_params
    async def add_subheader_to_module(course_identifier: Union[str, int],
                                    module_id: Union[str, int],
                                    title: str,
                                    position: Optional[int] = None,
                                    indent: Optional[int] = None) -> str:
        """Add a subheader (text divider) to a Canvas module.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add the subheader to
            title: The subheader text
            position: Position in the module (1 = first)
            indent: Indentation level (0-3)
        """
        return await add_item_to_module(
            course_identifier=course_identifier,
            module_id=module_id,
            item_type="SubHeader",
            title=title,
            position=position,
            indent=indent
        )

    @mcp.tool(name="canvas_bulk_add_mod_items")
    @validate_params
    async def bulk_add_items_to_module(course_identifier: Union[str, int],
                                     module_id: Union[str, int],
                                     items: list) -> str:
        """Add multiple items to a Canvas module at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to add items to
            items: List of item dictionaries with appropriate keys for each type:
                   - Assignment/Quiz/File/Discussion: content_id, title (optional), position, indent
                   - Page: url or page_url (the page slug), title (optional), position, indent
                   - ExternalUrl: external_url, title (required), position, indent, new_tab
                   - SubHeader: title (required), position, indent
                   Example: [
                       {"type": "Assignment", "content_id": 123, "title": "Homework 1"},
                       {"type": "Page", "url": "intro-page", "title": "Introduction"},
                       {"type": "ExternalUrl", "external_url": "https://example.com", "title": "External Resource"}
                   ]
        """
        course_id = await get_course_id(course_identifier)
        
        if not items:
            return "No items provided to add to module."
        
        if not isinstance(items, list):
            return "Error: items must be a list of item dictionaries."
        
        # Get module details for context
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        results = []
        errors = []
        
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"Item {i+1}: Must be a dictionary")
                continue
            
            item_type = item.get("type")
            if not item_type:
                errors.append(f"Item {i+1}: Missing 'type' field")
                continue
            
            try:
                # Build parameters for add_item_to_module
                params = {
                    "course_identifier": course_identifier,
                    "module_id": module_id,
                    "item_type": item_type
                }
                
                # Add optional parameters if present
                # For Page items, ensure we use 'url' instead of 'content_id'
                if item_type == 'Page':
                    if 'page_url' in item:
                        params['url'] = item['page_url']
                    elif 'url' in item:
                        params['url'] = item['url']
                    # Don't pass content_id for Page items
                    for key in ["title", "position", "indent", "new_tab"]:
                        if key in item:
                            params[key] = item[key]
                else:
                    for key in ["content_id", "title", "url", "external_url", "position", "indent", "new_tab"]:
                        if key in item:
                            params[key] = item[key]
                
                # Call the main add function
                result = await add_item_to_module(**params)
                
                if result.startswith("Error"):
                    errors.append(f"Item {i+1} ({item_type}): {result}")
                else:
                    item_title = item.get("title", f"{item_type} item")
                    results.append(f"✅ {item_title} ({item_type})")
                    
            except Exception as e:
                errors.append(f"Item {i+1} ({item_type}): {str(e)}")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Add Results for Module '{module_name}' in Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully added {len(results)} items:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to add {len(errors)} items:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No items were processed.\n"
        
        return result

    @mcp.tool(name="canvas_update_mod_indent")
    @validate_params
    async def update_module_item_indent(course_identifier: Union[str, int],
                                      module_id: Union[str, int],
                                      item_id: Union[str, int],
                                      indent_level: int) -> str:
        """Update the indentation level of a module item.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
            item_id: The module item ID to update
            indent_level: New indentation level (0-3, where 0 is no indent)
        """
        course_id = await get_course_id(course_identifier)
        
        # Validate indent level
        if indent_level < 0 or indent_level > 3:
            return "Error: indent_level must be between 0 and 3"
        
        # Get current item details
        item_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}/items/{item_id}"
        )
        
        if "error" in item_response:
            return f"Error fetching item: {item_response['error']}"
        
        item_title = item_response.get("title", "Unknown item")
        current_indent = item_response.get("indent", 0)
        
        # Update the item with new indent level
        update_data = {
            "module_item": {
                "indent": indent_level
            }
        }
        
        response = await make_canvas_request(
            "put", 
            f"/courses/{course_id}/modules/{module_id}/items/{item_id}",
            data=update_data
        )
        
        if "error" in response:
            return f"Error updating item indentation: {response['error']}"
        
        # Get module name for context
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully updated indentation for item in Module '{module_name}' in Course {course_display}:\n\n"
        result += f"Item: {item_title}\n"
        result += f"Item ID: {item_id}\n"
        result += f"Previous Indent: {current_indent}\n"
        result += f"New Indent: {indent_level}\n"
        
        # Visual representation
        old_visual = "  " * current_indent + "📄 " + item_title
        new_visual = "  " * indent_level + "📄 " + item_title
        
        result += f"\nVisual Change:\n"
        result += f"Before: {old_visual}\n"
        result += f"After:  {new_visual}\n"
        
        return result

    @mcp.tool(name="canvas_bulk_update_indent")
    @validate_params
    async def bulk_update_indent(course_identifier: Union[str, int],
                               module_id: Union[str, int],
                               indent_updates: list) -> str:
        """Update indentation levels for multiple module items at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
            indent_updates: List of dictionaries with 'item_id' and 'indent_level' keys
                           Example: [{"item_id": 123, "indent_level": 1}, {"item_id": 456, "indent_level": 2}]
        """
        course_id = await get_course_id(course_identifier)
        
        if not indent_updates:
            return "No indent updates provided."
        
        if not isinstance(indent_updates, list):
            return "Error: indent_updates must be a list of dictionaries."
        
        # Get module name for context
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        results = []
        errors = []
        
        for i, update in enumerate(indent_updates):
            if not isinstance(update, dict):
                errors.append(f"Update {i+1}: Must be a dictionary")
                continue
            
            item_id = update.get("item_id")
            indent_level = update.get("indent_level")
            
            if item_id is None:
                errors.append(f"Update {i+1}: Missing 'item_id'")
                continue
            
            if indent_level is None:
                errors.append(f"Update {i+1}: Missing 'indent_level'")
                continue
            
            if indent_level < 0 or indent_level > 3:
                errors.append(f"Update {i+1}: indent_level must be between 0 and 3")
                continue
            
            # Get current item details
            item_response = await make_canvas_request(
                "get", f"/courses/{course_id}/modules/{module_id}/items/{item_id}"
            )
            
            if "error" in item_response:
                errors.append(f"Item {item_id}: {item_response['error']}")
                continue
            
            item_title = item_response.get("title", "Unknown item")
            
            # Update the item
            update_data = {
                "module_item": {
                    "indent": indent_level
                }
            }
            
            response = await make_canvas_request(
                "put", 
                f"/courses/{course_id}/modules/{module_id}/items/{item_id}",
                data=update_data
            )
            
            if "error" in response:
                errors.append(f"Item {item_id} ({item_title}): {response['error']}")
            else:
                visual = "  " * indent_level + "📄 " + item_title
                results.append(f"✅ {item_title} (ID: {item_id}) → Indent: {indent_level}\n   {visual}")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Indent Update Results for Module '{module_name}' in Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully updated {len(results)} items:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to update {len(errors)} items:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No items were processed.\n"
        
        return result

    @mcp.tool(name="canvas_get_mod_tree")
    @validate_params
    async def get_module_structure_tree(course_identifier: Union[str, int],
                                      module_id: Union[str, int]) -> str:
        """Display module items in a visual tree structure showing indentation hierarchy.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Get module items
        params = {"per_page": 100}
        items = await fetch_all_paginated_results(
            f"/courses/{course_id}/modules/{module_id}/items", params
        )
        
        if isinstance(items, dict) and "error" in items:
            return f"Error fetching module items: {items['error']}"
        
        if not items:
            return f"No items found in module {module_id}."
        
        # Get module details
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        
        module_name = "Unknown Module"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown Module")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"📚 Module Structure Tree for '{module_name}' in Course {course_display}:\n\n"
        
        # Sort items by position
        sorted_items = sorted(items, key=lambda x: x.get("position", 0))
        
        for item in sorted_items:
            title = item.get("title", "Untitled")
            item_type = item.get("type", "Unknown")
            indent = item.get("indent", 0)
            position = item.get("position", "?")
            published = item.get("published", False)
            item_id = item.get("id")
            
            # Create tree structure with Unicode characters
            if indent == 0:
                prefix = "├── "
            elif indent == 1:
                prefix = "│   ├── "
            elif indent == 2:
                prefix = "│   │   ├── "
            elif indent == 3:
                prefix = "│   │   │   ├── "
            else:
                prefix = "│   " * indent + "├── "
            
            # Choose emoji based on type
            type_emoji = {
                "Assignment": "📝",
                "Quiz": "❓",
                "Page": "📄",
                "Discussion": "💬",
                "ExternalUrl": "🔗",
                "ExternalTool": "🔧",
                "SubHeader": "📋",
                "File": "📎"
            }.get(item_type, "📄")
            
            status_indicator = "✅" if published else "⭕"
            
            result += f"{prefix}{type_emoji} {title} {status_indicator}\n"
            result += f"{'│   ' * (indent + 1)}    📍 Position: {position} | 🆔 ID: {item_id} | 📂 Type: {item_type}\n"
        
        result += "\n🔍 Legend:\n"
        result += "├── Tree structure shows hierarchy\n"
        result += "✅ Published content\n"
        result += "⭕ Unpublished content\n"
        result += "📝 Assignment  ❓ Quiz  📄 Page  💬 Discussion\n"
        result += "🔗 External Link  🔧 External Tool  📋 SubHeader  📎 File\n"
        
        return result

    @mcp.tool(name="canvas_list_groups")
    @validate_params
    async def list_groups(course_identifier: Union[str, int]) -> str:
        """List all groups and their members for a specific course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Get all groups in the course
        groups = await fetch_all_paginated_results(
            f"/courses/{course_id}/groups", {"per_page": 100}
        )
        
        if isinstance(groups, dict) and "error" in groups:
            return f"Error fetching groups: {groups['error']}"
        
        if not groups:
            return f"No groups found for course {course_identifier}."
        
        # Format the output
        course_display = await get_course_code(course_id) or course_identifier
        output = f"Groups for Course {course_display}:\n\n"
        
        for group in groups:
            group_id = group.get("id")
            group_name = group.get("name", "Unnamed group")
            group_category = group.get("group_category_id", "Uncategorized")
            member_count = group.get("members_count", 0)
            
            output += f"Group: {group_name}\n"
            output += f"ID: {group_id}\n"
            output += f"Category ID: {group_category}\n"
            output += f"Member Count: {member_count}\n"
            
            # Get members for this group
            members = await fetch_all_paginated_results(
                f"/groups/{group_id}/users", {"per_page": 100}
            )
            
            if isinstance(members, dict) and "error" in members:
                output += f"Error fetching members: {members['error']}\n"
            elif not members:
                output += "No members in this group.\n"
            else:
                # Anonymize member data to protect student privacy
                try:
                    members = anonymize_response_data(members, data_type="users")
                except Exception as e:
                    return f"Error: Failed to anonymize group member data: {str(e)}"
                output += "Members:\n"
                for member in members:
                    member_id = member.get("id")
                    member_name = member.get("name", "Unnamed user")
                    member_email = member.get("email", "No email")
                    output += f"  - {member_name} (ID: {member_id}, Email: {member_email})\n"
            
            output += "\n"
        
        return output

    # ===== USER TOOLS =====
    
    @mcp.tool(name="canvas_list_users")
    async def list_users(course_identifier: str) -> str:
        """List users enrolled in a specific course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
        """
        course_id = await get_course_id(course_identifier)
        
        params = {
            "include[]": ["enrollments", "email"],
            "per_page": 100
        }
        
        users = await fetch_all_paginated_results(f"/courses/{course_id}/users", params)
        
        if isinstance(users, dict) and "error" in users:
            return f"Error fetching users: {users['error']}"
        
        if not users:
            return f"No users found for course {course_identifier}."
        
        # Anonymize user data to protect student privacy
        try:
            users = anonymize_response_data(users, data_type="users")
        except Exception as e:
            return f"Error: Failed to anonymize user data: {str(e)}"
        
        users_info = []
        for user in users:
            user_id = user.get("id")
            name = user.get("name", "Unknown")
            email = user.get("email", "No email")
            
            # Get enrollment info
            enrollments = user.get("enrollments", [])
            roles = [enrollment.get("role", "Student") for enrollment in enrollments]
            role_list = ", ".join(set(roles)) if roles else "Student"
            
            users_info.append(
                f"ID: {user_id}\nName: {name}\nEmail: {email}\nRoles: {role_list}\n"
            )
        
        course_display = await get_course_code(course_id) or course_identifier
        return f"Users in Course {course_display}:\n\n" + "\n".join(users_info)

    # ===== ANALYTICS TOOLS =====
    
    @mcp.tool(name="canvas_get_student_analytics")
    async def get_student_analytics(course_identifier: str,
                                  current_only: bool = True,
                                  include_participation: bool = True,
                                  include_assignment_stats: bool = True,
                                  include_access_stats: bool = True) -> str:
        """Get detailed analytics about student activity, participation, and progress in a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            current_only: Whether to include only assignments due on or before today
            include_participation: Whether to include participation data (discussions, submissions)
            include_assignment_stats: Whether to include assignment completion statistics
            include_access_stats: Whether to include course access statistics
        """
        course_id = await get_course_id(course_identifier)
        
        # Get basic course info
        course_response = await make_canvas_request("get", f"/courses/{course_id}")
        if "error" in course_response:
            return f"Error fetching course: {course_response['error']}"
        
        course_name = course_response.get("name", "Unknown Course")
        
        # Get students
        students = await fetch_all_paginated_results(
            f"/courses/{course_id}/users", 
            {"enrollment_type[]": "student", "per_page": 100}
        )
        
        if isinstance(students, dict) and "error" in students:
            return f"Error fetching students: {students['error']}"
        
        # Anonymize student data to protect privacy
        try:
            students = anonymize_response_data(students, data_type="users")
        except Exception as e:
            return f"Error: Failed to anonymize student data: {str(e)}"
        
        # Get assignments
        assignments = await fetch_all_paginated_results(
            f"/courses/{course_id}/assignments", 
            {"per_page": 100}
        )
        
        if isinstance(assignments, dict) and "error" in assignments:
            assignments = []
        
        course_display = await get_course_code(course_id) or course_identifier
        output = f"Student Analytics for Course {course_display} ({course_name})\n\n"
        
        output += f"Total Students: {len(students)}\n"
        output += f"Total Assignments: {len(assignments)}\n\n"
        
        if include_assignment_stats and assignments:
            # Calculate assignment completion stats
            published_assignments = [a for a in assignments if a.get("published", False)]
            total_points = sum(a.get("points_possible", 0) for a in published_assignments)
            
            output += f"Published Assignments: {len(published_assignments)}\n"
            output += f"Total Points Available: {total_points}\n\n"
        
        output += "This analytics feature provides basic course statistics.\n"
        output += "For detailed individual student analytics, use specific assignment analytics tools."
        
        return output

    @mcp.tool(name="canvas_delete_module")
    @validate_params
    async def delete_module(course_identifier: Union[str, int], module_id: Union[str, int]) -> str:
        """Delete a specific module from a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_id: The module ID to delete
        """
        course_id = await get_course_id(course_identifier)
        
        # First get the module details before deleting
        module_response = await make_canvas_request(
            "get", f"/courses/{course_id}/modules/{module_id}"
        )
        
        module_name = "Unknown module"
        module_position = "Unknown"
        if "error" not in module_response:
            module_name = module_response.get("name", "Unknown module")
            module_position = module_response.get("position", "Unknown")
        
        # Delete the module
        response = await make_canvas_request(
            "delete", f"/courses/{course_id}/modules/{module_id}"
        )
        
        if "error" in response:
            return f"Error deleting module: {response['error']}"
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully deleted module from Course {course_display}:\n\n"
        result += f"Module Name: {module_name}\n"
        result += f"Module ID: {module_id}\n"
        result += f"Position: {module_position}\n"
        
        return result

    @mcp.tool(name="canvas_bulk_delete_modules")
    @validate_params
    async def bulk_delete_modules(course_identifier: Union[str, int],
                                module_ids: Optional[list] = None,
                                delete_all_modules: bool = False) -> str:
        """Delete multiple modules at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            module_ids: List of module IDs to delete (e.g., [123, 456, 789])
            delete_all_modules: If True, delete ALL modules in the course (overrides module_ids)
        """
        course_id = await get_course_id(course_identifier)
        
        if delete_all_modules:
            # Get all modules first
            modules = await fetch_all_paginated_results(f"/courses/{course_id}/modules", {"per_page": 100})
            if isinstance(modules, dict) and "error" in modules:
                return f"Error fetching modules: {modules['error']}"
            
            module_ids = [module.get("id") for module in modules]
            if not module_ids:
                return f"No modules found to delete in course {course_identifier}."
        
        if not module_ids:
            return "No module IDs provided. Use module_ids parameter or set delete_all_modules=true."
        
        # Convert to list of integers if needed
        try:
            module_ids = [int(mid) for mid in module_ids]
        except (ValueError, TypeError):
            return "Error: module_ids must be a list of integers."
        
        results = []
        errors = []
        
        for module_id in module_ids:
            # Get module details before deleting
            module_response = await make_canvas_request(
                "get", f"/courses/{course_id}/modules/{module_id}"
            )
            
            module_name = f"Module {module_id}"
            if "error" not in module_response:
                module_name = module_response.get("name", f"Module {module_id}")
            
            # Delete the module
            response = await make_canvas_request(
                "delete", f"/courses/{course_id}/modules/{module_id}"
            )
            
            if "error" in response:
                errors.append(f"Module {module_id} ({module_name}): {response['error']}")
            else:
                results.append(f"✅ {module_name} (ID: {module_id})")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Delete Results for Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully deleted {len(results)} modules:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to delete {len(errors)} modules:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No modules were processed.\n"
        
        return result

    @mcp.tool(name="canvas_create_anon_map")
    @validate_params
    async def create_student_anonymization_map(course_identifier: Union[str, int]) -> str:
        """Create a local CSV file mapping real student data to anonymous IDs for a course.
        
        This tool generates a de-anonymization key that allows faculty to identify students
        from their anonymous IDs. The file is saved locally and should be kept secure.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
        """
        import csv
        import os
        from pathlib import Path
        from ..core.anonymization import generate_anonymous_id
        
        course_id = await get_course_id(course_identifier)
        
        # Get all students in the course
        params = {
            "enrollment_type[]": "student",
            "include[]": ["email"],
            "per_page": 100
        }
        
        students = await fetch_all_paginated_results(
            f"/courses/{course_id}/users", params
        )
        
        if isinstance(students, dict) and "error" in students:
            return f"Error fetching students: {students['error']}"
        
        if not students:
            return f"No students found for course {course_identifier}."
        
        # Create local_maps directory if it doesn't exist
        maps_dir = Path("local_maps")
        maps_dir.mkdir(exist_ok=True)
        
        # Generate filename with course identifier
        course_display = await get_course_code(course_id) or str(course_identifier)
        safe_course_name = "".join(c for c in course_display if c.isalnum() or c in ("-", "_"))
        filename = f"anonymization_map_{safe_course_name}.csv"
        filepath = maps_dir / filename
        
        # Create mapping data
        mapping_data = []
        for student in students:
            real_id = student.get("id")
            real_name = student.get("name", "Unknown")
            real_email = student.get("email", "No email")
            
            # Generate the same anonymous ID that would be used by the anonymization system
            anonymous_id = generate_anonymous_id(real_id, prefix="Student")
            
            mapping_data.append({
                "real_name": real_name,
                "real_id": real_id,
                "real_email": real_email,
                "anonymous_id": anonymous_id
            })
        
        # Write to CSV file
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["real_name", "real_id", "real_email", "anonymous_id"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(mapping_data)
            
            result = f"✅ Student anonymization map created successfully!\n\n"
            result += f"📁 File location: {filepath}\n"
            result += f"👥 Students mapped: {len(mapping_data)}\n"
            result += f"🏫 Course: {course_display}\n\n"
            result += f"⚠️ **SECURITY WARNING:**\n"
            result += f"This file contains sensitive student information and should be:\n"
            result += f"• Kept secure and not shared\n"
            result += f"• Deleted when no longer needed\n"
            result += f"• Never committed to version control\n\n"
            result += f"📋 File format: CSV with columns real_name, real_id, real_email, anonymous_id\n"
            result += f"🔍 Use this file to identify students from their anonymous IDs in tool outputs."
            
            return result
            
        except Exception as e:
            return f"Error creating anonymization map: {str(e)}"