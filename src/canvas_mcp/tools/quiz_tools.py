"""Quiz-related MCP tools for Canvas API."""

from typing import Union, Optional, List, Dict, Any
from fastmcp import FastMCP

from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.cache import get_course_id, get_course_code
from ..core.validation import validate_params
from ..core.dates import format_date


def register_quiz_tools(mcp: FastMCP):
    """Register all quiz-related MCP tools."""
    
    @mcp.tool(name="canvas_list_quizzes")
    @validate_params
    async def list_quizzes(course_identifier: Union[str, int]) -> str:
        """List all quizzes in a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
        """
        course_id = await get_course_id(course_identifier)
        
        params = {"per_page": 100}
        quizzes = await fetch_all_paginated_results(f"/courses/{course_id}/quizzes", params)
        
        if isinstance(quizzes, dict) and "error" in quizzes:
            return f"Error fetching quizzes: {quizzes['error']}"
        
        if not quizzes:
            return f"No quizzes found for course {course_identifier}."
        
        quizzes_info = []
        for quiz in quizzes:
            quiz_id = quiz.get("id")
            title = quiz.get("title", "Untitled quiz")
            published = quiz.get("published", False)
            points = quiz.get("points_possible", 0)
            question_count = quiz.get("question_count", 0)
            due_at = format_date(quiz.get("due_at"))
            
            status = "Published" if published else "Unpublished"
            
            quizzes_info.append(
                f"ID: {quiz_id}\nTitle: {title}\nStatus: {status}\nQuestions: {question_count}\nPoints: {points}\nDue: {due_at}\n"
            )
        
        course_display = await get_course_code(course_id) or course_identifier
        return f"Quizzes for Course {course_display}:\n\n" + "\n".join(quizzes_info)

    @mcp.tool(name="canvas_create_quiz")
    @validate_params
    async def create_quiz(course_identifier: Union[str, int],
                         title: str,
                         description: Optional[str] = None,
                         quiz_type: str = "assignment",
                         points_possible: Optional[float] = None,
                         due_at: Optional[str] = None,
                         unlock_at: Optional[str] = None,
                         lock_at: Optional[str] = None,
                         time_limit: Optional[int] = None,
                         allowed_attempts: int = 1,
                         scoring_policy: str = "keep_highest",
                         shuffle_answers: bool = True,
                         show_correct_answers: bool = True,
                         show_correct_answers_last_attempt: bool = False,
                         show_correct_answers_at: Optional[str] = None,
                         hide_correct_answers_at: Optional[str] = None,
                         one_question_at_a_time: bool = False,
                         cant_go_back: bool = False,
                         access_code: Optional[str] = None,
                         ip_filter: Optional[str] = None,
                         published: bool = False) -> str:
        """Create a new quiz in Canvas.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            title: The quiz title
            description: Quiz description/instructions
            quiz_type: Type of quiz ('assignment', 'practice_quiz', 'graded_survey', 'survey')
            points_possible: Total points for the quiz
            due_at: Due date (ISO 8601 format)
            unlock_at: When quiz becomes available (ISO 8601 format)
            lock_at: When quiz is locked (ISO 8601 format)
            time_limit: Time limit in minutes
            allowed_attempts: Number of attempts allowed (1 for single attempt)
            scoring_policy: How to score multiple attempts ('keep_highest', 'keep_latest', 'keep_average')
            shuffle_answers: Whether to shuffle answer choices
            show_correct_answers: Whether to show correct answers after submission
            show_correct_answers_last_attempt: Show answers only after last attempt
            show_correct_answers_at: When to show correct answers (ISO 8601 format)
            hide_correct_answers_at: When to hide correct answers (ISO 8601 format)
            one_question_at_a_time: Show one question at a time
            cant_go_back: Prevent going back to previous questions
            access_code: Access code required to take quiz
            ip_filter: IP address filter for quiz access
            published: Whether to publish the quiz immediately
        """
        course_id = await get_course_id(course_identifier)
        
        # Build quiz data
        quiz_data = {
            "quiz": {
                "title": title,
                "quiz_type": quiz_type,
                "allowed_attempts": allowed_attempts,
                "scoring_policy": scoring_policy,
                "shuffle_answers": shuffle_answers,
                "show_correct_answers": show_correct_answers,
                "show_correct_answers_last_attempt": show_correct_answers_last_attempt,
                "one_question_at_a_time": one_question_at_a_time,
                "cant_go_back": cant_go_back,
                "published": published
            }
        }
        
        # Add optional fields
        if description:
            quiz_data["quiz"]["description"] = description
        if points_possible is not None:
            quiz_data["quiz"]["points_possible"] = points_possible
        if due_at:
            quiz_data["quiz"]["due_at"] = due_at
        if unlock_at:
            quiz_data["quiz"]["unlock_at"] = unlock_at
        if lock_at:
            quiz_data["quiz"]["lock_at"] = lock_at
        if time_limit:
            quiz_data["quiz"]["time_limit"] = time_limit
        if show_correct_answers_at:
            quiz_data["quiz"]["show_correct_answers_at"] = show_correct_answers_at
        if hide_correct_answers_at:
            quiz_data["quiz"]["hide_correct_answers_at"] = hide_correct_answers_at
        if access_code:
            quiz_data["quiz"]["access_code"] = access_code
        if ip_filter:
            quiz_data["quiz"]["ip_filter"] = ip_filter
        
        # Create the quiz
        response = await make_canvas_request(
            "post", f"/courses/{course_id}/quizzes", data=quiz_data
        )
        
        if "error" in response:
            return f"Error creating quiz: {response['error']}"
        
        quiz_id = response.get("id")
        quiz_title = response.get("title", title)
        quiz_url = response.get("html_url", "")
        created_at = format_date(response.get("created_at"))
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully created quiz in Course {course_display}:\n\n"
        result += f"Quiz: {quiz_title}\n"
        result += f"Quiz ID: {quiz_id}\n"
        result += f"Type: {quiz_type}\n"
        result += f"Status: {'Published' if published else 'Unpublished'}\n"
        result += f"Created: {created_at}\n"
        if quiz_url:
            result += f"URL: {quiz_url}\n"
        
        return result

    @mcp.tool(name="canvas_add_quiz_question")
    @validate_params
    async def add_quiz_question(course_identifier: Union[str, int],
                              quiz_id: Union[str, int],
                              question_name: str,
                              question_text: str,
                              question_type: str,
                              points_possible: float = 1.0,
                              answers: Optional[List[Dict[str, Any]]] = None,
                              correct_comments: Optional[str] = None,
                              incorrect_comments: Optional[str] = None,
                              neutral_comments: Optional[str] = None) -> str:
        """Add a question to a Canvas quiz.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            quiz_id: The Canvas quiz ID
            question_name: Brief name for the question
            question_text: The actual question text (supports HTML)
            question_type: Type of question ('multiple_choice_question', 'true_false_question', 
                          'short_answer_question', 'fill_in_multiple_blanks_question', 
                          'multiple_answers_question', 'multiple_dropdowns_question',
                          'matching_question', 'numerical_question', 'calculated_question',
                          'essay_question', 'text_only_question')
            points_possible: Points for this question
            answers: List of answer dictionaries with 'answer_text', 'answer_weight', etc.
            correct_comments: Feedback for correct answers
            incorrect_comments: Feedback for incorrect answers  
            neutral_comments: General feedback
        """
        course_id = await get_course_id(course_identifier)
        
        # Build question data
        question_data = {
            "question": {
                "question_name": question_name,
                "question_text": question_text,
                "question_type": question_type,
                "points_possible": points_possible
            }
        }
        
        # Add answers if provided
        if answers:
            question_data["question"]["answers"] = answers
        
        # Add comments if provided
        if correct_comments:
            question_data["question"]["correct_comments"] = correct_comments
        if incorrect_comments:
            question_data["question"]["incorrect_comments"] = incorrect_comments
        if neutral_comments:
            question_data["question"]["neutral_comments"] = neutral_comments
        
        # Create the question
        response = await make_canvas_request(
            "post", f"/courses/{course_id}/quizzes/{quiz_id}/questions", data=question_data
        )
        
        if "error" in response:
            return f"Error adding question to quiz: {response['error']}"
        
        question_id = response.get("id")
        question_name_result = response.get("question_name", question_name)
        question_type_result = response.get("question_type", question_type)
        points = response.get("points_possible", points_possible)
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully added question to Quiz {quiz_id} in Course {course_display}:\n\n"
        result += f"Question: {question_name_result}\n"
        result += f"Question ID: {question_id}\n"
        result += f"Type: {question_type_result}\n"
        result += f"Points: {points}\n"
        
        return result

    @mcp.tool(name="canvas_import_quiz_markdown")
    @validate_params
    async def import_quiz_from_markdown(course_identifier: Union[str, int],
                                      markdown_content: str,
                                      quiz_title: Optional[str] = None) -> str:
        """Import a quiz from markdown format.
        
        Supports the enhanced markdown quiz format used in the Canvas project.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            markdown_content: The markdown quiz content
            quiz_title: Optional title override (uses title from markdown if not provided)
        """
        course_id = await get_course_id(course_identifier)
        
        # Parse the markdown content
        try:
            quiz_data = parse_markdown_quiz(markdown_content)
        except Exception as e:
            return f"Error parsing markdown quiz: {str(e)}"
        
        # Use provided title or extract from markdown
        title = quiz_title or quiz_data.get("title", "Imported Quiz")
        
        # Create the quiz first
        quiz_creation_data = {
            "quiz": {
                "title": title,
                "description": quiz_data.get("description", ""),
                "quiz_type": quiz_data.get("quiz_type", "assignment"),
                "points_possible": quiz_data.get("points_possible"),
                "time_limit": quiz_data.get("time_limit"),
                "allowed_attempts": quiz_data.get("allowed_attempts", 1),
                "shuffle_answers": quiz_data.get("shuffle_answers", True),
                "show_correct_answers": quiz_data.get("show_correct_answers", True),
                "one_question_at_a_time": quiz_data.get("one_question_at_a_time", False),
                "published": False  # Keep unpublished until all questions are added
            }
        }
        
        # Remove None values
        quiz_creation_data["quiz"] = {k: v for k, v in quiz_creation_data["quiz"].items() if v is not None}
        
        # Create the quiz
        quiz_response = await make_canvas_request(
            "post", f"/courses/{course_id}/quizzes", data=quiz_creation_data
        )
        
        if "error" in quiz_response:
            return f"Error creating quiz: {quiz_response['error']}"
        
        quiz_id = quiz_response.get("id")
        
        # Add questions to the quiz
        questions_added = 0
        questions_failed = 0
        error_messages = []
        
        for question in quiz_data.get("questions", []):
            question_response = await make_canvas_request(
                "post", f"/courses/{course_id}/quizzes/{quiz_id}/questions", data={"question": question}
            )
            
            if "error" in question_response:
                questions_failed += 1
                error_messages.append(f"Question '{question.get('question_name', 'Unknown')}': {question_response['error']}")
            else:
                questions_added += 1
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Quiz import results for Course {course_display}:\n\n"
        result += f"Quiz: {title}\n"
        result += f"Quiz ID: {quiz_id}\n"
        result += f"Questions added: {questions_added}\n"
        result += f"Questions failed: {questions_failed}\n"
        
        if error_messages:
            result += "\nErrors encountered:\n"
            for error in error_messages[:5]:  # Show first 5 errors
                result += f"- {error}\n"
            if len(error_messages) > 5:
                result += f"... and {len(error_messages) - 5} more errors\n"
        
        result += f"\nNote: Quiz created as unpublished. Use Canvas interface to review and publish."
        
        return result

    @mcp.tool(name="canvas_delete_quiz")
    @validate_params
    async def delete_quiz(course_identifier: Union[str, int],
                         quiz_id: Union[str, int]) -> str:
        """Delete a specific quiz from a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            quiz_id: The Canvas quiz ID to delete
        """
        course_id = await get_course_id(course_identifier)
        
        # First get the quiz details before deleting
        quiz_response = await make_canvas_request(
            "get", f"/courses/{course_id}/quizzes/{quiz_id}"
        )
        
        quiz_title = "Unknown quiz"
        points_possible = 0
        question_count = 0
        if "error" not in quiz_response:
            quiz_title = quiz_response.get("title", "Unknown quiz")
            points_possible = quiz_response.get("points_possible", 0)
            question_count = quiz_response.get("question_count", 0)
        
        # Delete the quiz
        response = await make_canvas_request(
            "delete", f"/courses/{course_id}/quizzes/{quiz_id}"
        )
        
        if "error" in response:
            return f"Error deleting quiz: {response['error']}"
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully deleted quiz from Course {course_display}:\n\n"
        result += f"Quiz: {quiz_title}\n"
        result += f"Quiz ID: {quiz_id}\n"
        result += f"Questions: {question_count}\n"
        result += f"Points: {points_possible}\n"
        
        return result

    @mcp.tool(name="canvas_bulk_delete_quizzes")
    @validate_params
    async def bulk_delete_quizzes(course_identifier: Union[str, int],
                                 quiz_ids: List[Union[str, int]]) -> str:
        """Delete multiple quizzes from a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            quiz_ids: List of Canvas quiz IDs to delete
        """
        course_id = await get_course_id(course_identifier)
        
        if not quiz_ids:
            return "No quiz IDs provided for deletion."
        
        results = []
        deleted_count = 0
        failed_count = 0
        
        for quiz_id in quiz_ids:
            # Get quiz details first
            quiz_response = await make_canvas_request(
                "get", f"/courses/{course_id}/quizzes/{quiz_id}"
            )
            
            quiz_title = "Unknown quiz"
            if "error" not in quiz_response:
                quiz_title = quiz_response.get("title", "Unknown quiz")
            
            # Delete the quiz
            delete_response = await make_canvas_request(
                "delete", f"/courses/{course_id}/quizzes/{quiz_id}"
            )
            
            if "error" in delete_response:
                failed_count += 1
                results.append(f"❌ Failed to delete '{quiz_title}' (ID: {quiz_id}): {delete_response['error']}")
            else:
                deleted_count += 1
                results.append(f"✅ Deleted '{quiz_title}' (ID: {quiz_id})")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        summary = f"Bulk quiz deletion results for Course {course_display}:\n\n"
        summary += f"Total quizzes processed: {len(quiz_ids)}\n"
        summary += f"Successfully deleted: {deleted_count}\n"
        summary += f"Failed to delete: {failed_count}\n\n"
        
        if results:
            summary += "Details:\n" + "\n".join(results)
        
        return summary

    @mcp.tool(name="canvas_rename_quiz")
    @validate_params
    async def rename_quiz(course_identifier: Union[str, int],
                         quiz_id: Union[str, int],
                         new_title: str) -> str:
        """Rename a quiz in Canvas.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            quiz_id: The Canvas quiz ID to rename
            new_title: The new title for the quiz
        """
        course_id = await get_course_id(course_identifier)
        
        # First get the current quiz details
        quiz_response = await make_canvas_request(
            "get", f"/courses/{course_id}/quizzes/{quiz_id}"
        )
        
        if "error" in quiz_response:
            return f"Error fetching quiz: {quiz_response['error']}"
        
        old_title = quiz_response.get("title", "Unknown quiz")
        
        # Update the quiz with new title
        update_data = {
            "quiz": {
                "title": new_title
            }
        }
        
        response = await make_canvas_request(
            "put", f"/courses/{course_id}/quizzes/{quiz_id}", data=update_data
        )
        
        if "error" in response:
            return f"Error renaming quiz: {response['error']}"
        
        updated_title = response.get("title", new_title)
        quiz_url = response.get("html_url", "")
        updated_at = format_date(response.get("updated_at"))
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully renamed quiz in Course {course_display}:\n\n"
        result += f"Old title: {old_title}\n"
        result += f"New title: {updated_title}\n"
        result += f"Quiz ID: {quiz_id}\n"
        result += f"Updated: {updated_at}\n"
        if quiz_url:
            result += f"URL: {quiz_url}\n"
        
        return result

    @mcp.tool(name="canvas_update_quiz")
    @validate_params
    async def update_quiz(course_identifier: Union[str, int],
                         quiz_id: Union[str, int],
                         title: Optional[str] = None,
                         description: Optional[str] = None,
                         due_at: Optional[str] = None,
                         unlock_at: Optional[str] = None,
                         lock_at: Optional[str] = None,
                         time_limit: Optional[int] = None,
                         allowed_attempts: Optional[int] = None,
                         points_possible: Optional[float] = None,
                         published: Optional[bool] = None) -> str:
        """Update quiz properties in Canvas.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            quiz_id: The Canvas quiz ID to update
            title: New quiz title
            description: New quiz description/instructions
            due_at: New due date (ISO 8601 format, e.g., "2024-12-31T23:59:59Z")
            unlock_at: When quiz becomes available (ISO 8601 format)
            lock_at: When quiz is locked (ISO 8601 format)
            time_limit: Time limit in minutes
            allowed_attempts: Number of attempts allowed
            points_possible: Total points for the quiz
            published: Whether to publish/unpublish the quiz
        """
        course_id = await get_course_id(course_identifier)
        
        # First get the current quiz details
        quiz_response = await make_canvas_request(
            "get", f"/courses/{course_id}/quizzes/{quiz_id}"
        )
        
        if "error" in quiz_response:
            return f"Error fetching quiz: {quiz_response['error']}"
        
        # Build update data with only provided fields
        update_data = {"quiz": {}}
        changes = []
        
        if title is not None:
            update_data["quiz"]["title"] = title
            changes.append(f"Title: '{quiz_response.get('title', 'Unknown')}' → '{title}'")
        
        if description is not None:
            update_data["quiz"]["description"] = description
            changes.append("Description updated")
        
        if due_at is not None:
            update_data["quiz"]["due_at"] = due_at
            old_due = format_date(quiz_response.get("due_at"))
            new_due = format_date(due_at) if due_at else "No due date"
            changes.append(f"Due date: {old_due} → {new_due}")
        
        if unlock_at is not None:
            update_data["quiz"]["unlock_at"] = unlock_at
            old_unlock = format_date(quiz_response.get("unlock_at"))
            new_unlock = format_date(unlock_at) if unlock_at else "No unlock date"
            changes.append(f"Unlock date: {old_unlock} → {new_unlock}")
        
        if lock_at is not None:
            update_data["quiz"]["lock_at"] = lock_at
            old_lock = format_date(quiz_response.get("lock_at"))
            new_lock = format_date(lock_at) if lock_at else "No lock date"
            changes.append(f"Lock date: {old_lock} → {new_lock}")
        
        if time_limit is not None:
            update_data["quiz"]["time_limit"] = time_limit
            old_limit = quiz_response.get("time_limit", "No limit")
            new_limit = f"{time_limit} minutes" if time_limit else "No limit"
            changes.append(f"Time limit: {old_limit} → {new_limit}")
        
        if allowed_attempts is not None:
            update_data["quiz"]["allowed_attempts"] = allowed_attempts
            old_attempts = quiz_response.get("allowed_attempts", 1)
            changes.append(f"Allowed attempts: {old_attempts} → {allowed_attempts}")
        
        if points_possible is not None:
            update_data["quiz"]["points_possible"] = points_possible
            old_points = quiz_response.get("points_possible", 0)
            changes.append(f"Points possible: {old_points} → {points_possible}")
        
        if published is not None:
            update_data["quiz"]["published"] = published
            old_published = quiz_response.get("published", False)
            old_status = "Published" if old_published else "Unpublished"
            new_status = "Published" if published else "Unpublished"
            changes.append(f"Status: {old_status} → {new_status}")
        
        # Check if any updates were provided
        if not update_data["quiz"]:
            return "No updates provided. Please specify at least one field to update."
        
        # Update the quiz
        response = await make_canvas_request(
            "put", f"/courses/{course_id}/quizzes/{quiz_id}", data=update_data
        )
        
        if "error" in response:
            return f"Error updating quiz: {response['error']}"
        
        quiz_title = response.get("title", "Unknown quiz")
        quiz_url = response.get("html_url", "")
        updated_at = format_date(response.get("updated_at"))
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully updated quiz in Course {course_display}:\n\n"
        result += f"Quiz: {quiz_title}\n"
        result += f"Quiz ID: {quiz_id}\n"
        result += f"Updated: {updated_at}\n"
        if quiz_url:
            result += f"URL: {quiz_url}\n"
        
        if changes:
            result += f"\nChanges made:\n"
            for change in changes:
                result += f"• {change}\n"
        
        return result


def parse_markdown_quiz(markdown_content: str) -> Dict[str, Any]:
    """Parse markdown quiz content into Canvas API format."""
    import yaml
    import re
    
    # Split YAML frontmatter and content
    parts = markdown_content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid markdown format: missing YAML frontmatter")
    
    # Parse YAML metadata
    try:
        quiz_metadata = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")
    
    content = parts[2].strip()
    
    # Parse questions from content
    questions = []
    question_blocks = re.split(r'\n(?=##\s+Question\s+\d+)', content)
    
    for block in question_blocks:
        if not block.strip() or not block.startswith('##'):
            continue
            
        question = parse_question_block(block)
        if question:
            questions.append(question)
    
    # Build quiz data
    quiz_data = {
        "title": quiz_metadata.get("title"),
        "description": quiz_metadata.get("description"),
        "quiz_type": quiz_metadata.get("quiz_type", "assignment"),
        "points_possible": quiz_metadata.get("points_possible"),
        "time_limit": quiz_metadata.get("time_limit"),
        "allowed_attempts": quiz_metadata.get("allowed_attempts", 1),
        "shuffle_answers": quiz_metadata.get("shuffle_answers", True),
        "show_correct_answers": quiz_metadata.get("show_correct_answers", True),
        "one_question_at_a_time": quiz_metadata.get("one_question_at_a_time", False),
        "questions": questions
    }
    
    return quiz_data


def parse_question_block(block: str) -> Optional[Dict[str, Any]]:
    """Parse an individual question block from markdown."""
    import re
    import yaml
    
    lines = block.strip().split('\n')
    if not lines:
        return None
    
    # Extract question title
    title_match = re.match(r'^##\s+Question\s+\d+(?::\s*(.+))?', lines[0])
    if not title_match:
        return None
    
    question_name = title_match.group(1) or "Question"
    
    # Find YAML frontmatter for question
    yaml_start = -1
    yaml_end = -1
    
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == '```yaml':
            yaml_start = i + 1
        elif line.strip() == '```' and yaml_start != -1:
            yaml_end = i
            break
    
    if yaml_start == -1 or yaml_end == -1:
        return None
    
    # Parse question metadata
    try:
        yaml_content = '\n'.join(lines[yaml_start:yaml_end])
        question_metadata = yaml.safe_load(yaml_content)
    except yaml.YAMLError:
        return None
    
    # Extract question text (after YAML block)
    question_text_lines = []
    in_question_text = False
    
    for line in lines[yaml_end + 1:]:
        if line.startswith('**Question:**'):
            in_question_text = True
            # Extract text after "**Question:**"
            question_text_lines.append(line.replace('**Question:**', '').strip())
        elif in_question_text and (line.startswith('**') or line.startswith('###')):
            break
        elif in_question_text:
            question_text_lines.append(line)
    
    question_text = '\n'.join(question_text_lines).strip()
    
    # Build question data
    question_data = {
        "question_name": question_name,
        "question_text": question_text,
        "question_type": question_metadata.get("type", "multiple_choice_question"),
        "points_possible": question_metadata.get("points", 1.0)
    }
    
    # Parse answers based on question type
    if question_metadata.get("answers"):
        answers = []
        for answer in question_metadata["answers"]:
            if isinstance(answer, str):
                # Simple format: "*Correct answer" or "Wrong answer"
                is_correct = answer.startswith('*')
                answer_text = answer.lstrip('*').strip()
                answers.append({
                    "answer_text": answer_text,
                    "answer_weight": 100 if is_correct else 0
                })
            elif isinstance(answer, dict):
                # Complex format with weights, comments, etc.
                answers.append(answer)
        
        question_data["answers"] = answers
    
    # Add feedback if provided
    if question_metadata.get("correct_feedback"):
        question_data["correct_comments"] = question_metadata["correct_feedback"]
    if question_metadata.get("incorrect_feedback"):
        question_data["incorrect_comments"] = question_metadata["incorrect_feedback"]
    
    return question_data