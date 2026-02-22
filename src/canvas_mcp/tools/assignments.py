"""Assignment-related MCP tools for Canvas API."""

import datetime
from statistics import mean, median, stdev
from typing import Optional, Union
from fastmcp import FastMCP

from ..core.client import fetch_all_paginated_results, make_canvas_request
from ..core.cache import get_course_id, get_course_code
from ..core.validation import validate_params
from ..core.dates import format_date, truncate_text
from ..core.anonymization import anonymize_response_data


def register_assignment_tools(mcp: FastMCP):
    """Register all assignment-related MCP tools."""
    
    @mcp.tool(name="canvas_list_assignments")
    @validate_params
    async def list_assignments(course_identifier: Union[str, int]) -> str:
        """List assignments for a specific course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
        """
        course_id = await get_course_id(course_identifier)
        
        params = {
            "per_page": 100,
            "include[]": ["all_dates", "submission"]
        }
        
        all_assignments = await fetch_all_paginated_results(f"/courses/{course_id}/assignments", params)
        
        if isinstance(all_assignments, dict) and "error" in all_assignments:
            return f"Error fetching assignments: {all_assignments['error']}"
        
        if not all_assignments:
            return f"No assignments found for course {course_identifier}."
        
        assignments_info = []
        for assignment in all_assignments:
            assignment_id = assignment.get("id")
            name = assignment.get("name", "Unnamed assignment")
            due_at = assignment.get("due_at", "No due date")
            points = assignment.get("points_possible", 0)
            
            assignments_info.append(
                f"ID: {assignment_id}\nName: {name}\nDue: {due_at}\nPoints: {points}\n"
            )
        
        # Try to get the course code for display
        course_display = await get_course_code(course_id) or course_identifier
        return f"Assignments for Course {course_display}:\n\n" + "\n".join(assignments_info)

    @mcp.tool(name="canvas_get_assignment_details")
    @validate_params
    async def get_assignment_details(course_identifier: Union[str, int], assignment_id: Union[str, int]) -> str:
        """Get detailed information about a specific assignment.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Ensure assignment_id is a string
        assignment_id_str = str(assignment_id)
        
        response = await make_canvas_request(
            "get", f"/courses/{course_id}/assignments/{assignment_id_str}"
        )
        
        if "error" in response:
            return f"Error fetching assignment details: {response['error']}"
        
        details = [
            f"Name: {response.get('name', 'N/A')}",
            f"Description: {truncate_text(response.get('description', 'N/A'), 300)}",
            f"Due Date: {format_date(response.get('due_at'))}",
            f"Points Possible: {response.get('points_possible', 'N/A')}",
            f"Submission Types: {', '.join(response.get('submission_types', ['N/A']))}",
            f"Published: {response.get('published', False)}",
            f"Locked: {response.get('locked_for_user', False)}"
        ]
        
        # Try to get the course code for display
        course_display = await get_course_code(course_id) or course_identifier
        return f"Assignment Details for ID {assignment_id} in course {course_display}:\n\n" + "\n".join(details)

    @mcp.tool(name="canvas_update_assignment")
    @validate_params
    async def update_assignment(
        course_identifier: Union[str, int],
        assignment_id: Union[str, int],
        name: Optional[str] = None,
        description: Optional[str] = None,
        due_at: Optional[str] = None,
        unlock_at: Optional[str] = None,
        lock_at: Optional[str] = None,
        points_possible: Optional[float] = None,
        grading_type: Optional[str] = None,
        submission_types: Optional[list] = None,
        allowed_extensions: Optional[list] = None,
        published: Optional[bool] = None,
        omit_from_final_grade: Optional[bool] = None,
        allowed_attempts: Optional[int] = None
    ) -> str:
        """Update properties of an existing assignment.

        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID to update
            name: New assignment name
            description: New HTML description
            due_at: Due date (ISO 8601 format, e.g., "2025-12-31T23:59:59Z")
            unlock_at: Availability date (ISO 8601 format)
            lock_at: Lock date (ISO 8601 format)
            points_possible: Maximum points
            grading_type: One of: "points", "percent", "letter_grade", "gpa_scale", "pass_fail"
            submission_types: List of allowed types (e.g., ["online_text_entry", "online_upload"])
            allowed_extensions: List of allowed file extensions (e.g., ["pdf", "docx"])
            published: Publish (True) or unpublish (False) the assignment
            omit_from_final_grade: Exclude from final grade calculation
            allowed_attempts: Number of submission attempts (-1 for unlimited)
        """
        course_id = await get_course_id(course_identifier)
        assignment_id_str = str(assignment_id)

        # Build the update payload with only non-None parameters
        assignment_data = {}

        if name is not None:
            assignment_data["name"] = name

        if description is not None:
            assignment_data["description"] = description

        if due_at is not None:
            assignment_data["due_at"] = due_at

        if unlock_at is not None:
            assignment_data["unlock_at"] = unlock_at

        if lock_at is not None:
            assignment_data["lock_at"] = lock_at

        if points_possible is not None:
            assignment_data["points_possible"] = points_possible

        if grading_type is not None:
            # Validate grading_type
            valid_grading_types = ["points", "percent", "letter_grade", "gpa_scale", "pass_fail", "not_graded"]
            if grading_type not in valid_grading_types:
                return f"Error: Invalid grading_type '{grading_type}'. Must be one of: {', '.join(valid_grading_types)}"
            assignment_data["grading_type"] = grading_type

        if submission_types is not None:
            # Validate submission types
            valid_submission_types = [
                "online_text_entry", "online_url", "online_upload", "media_recording",
                "student_annotation", "online_quiz", "external_tool", "none", "on_paper"
            ]
            for sub_type in submission_types:
                if sub_type not in valid_submission_types:
                    return f"Error: Invalid submission type '{sub_type}'. Valid types: {', '.join(valid_submission_types)}"
            assignment_data["submission_types"] = submission_types

        if allowed_extensions is not None:
            assignment_data["allowed_extensions"] = allowed_extensions

        if published is not None:
            assignment_data["published"] = published

        if omit_from_final_grade is not None:
            assignment_data["omit_from_final_grade"] = omit_from_final_grade

        if allowed_attempts is not None:
            assignment_data["allowed_attempts"] = allowed_attempts

        # Check if any parameters were provided
        if not assignment_data:
            return "Error: No update parameters provided. At least one field must be specified to update."

        # Get current assignment details for comparison
        current_assignment = await make_canvas_request(
            "get", f"/courses/{course_id}/assignments/{assignment_id_str}"
        )

        if "error" in current_assignment:
            return f"Error fetching current assignment: {current_assignment['error']}"

        # Make the update request
        response = await make_canvas_request(
            "put",
            f"/courses/{course_id}/assignments/{assignment_id_str}",
            data={"assignment": assignment_data}
        )

        if "error" in response:
            return f"Error updating assignment: {response['error']}"

        # Format the success message with details of what was updated
        course_display = await get_course_code(course_id) or course_identifier
        result = f"Successfully updated assignment in Course {course_display}:\n\n"
        result += f"Assignment: {response.get('name', 'N/A')}\n"
        result += f"Assignment ID: {assignment_id}\n\n"
        result += "Updated fields:\n"

        # Show what was updated
        if name is not None:
            result += f"  Name: '{current_assignment.get('name')}' → '{response.get('name')}'\n"

        if description is not None:
            old_desc = truncate_text(current_assignment.get('description', 'N/A'), 50)
            new_desc = truncate_text(response.get('description', 'N/A'), 50)
            result += f"  Description: Updated (preview: {new_desc})\n"

        if due_at is not None:
            result += f"  Due Date: {format_date(current_assignment.get('due_at'))} → {format_date(response.get('due_at'))}\n"

        if unlock_at is not None:
            result += f"  Unlock Date: {format_date(current_assignment.get('unlock_at'))} → {format_date(response.get('unlock_at'))}\n"

        if lock_at is not None:
            result += f"  Lock Date: {format_date(current_assignment.get('lock_at'))} → {format_date(response.get('lock_at'))}\n"

        if points_possible is not None:
            result += f"  Points Possible: {current_assignment.get('points_possible')} → {response.get('points_possible')}\n"

        if grading_type is not None:
            result += f"  Grading Type: {current_assignment.get('grading_type')} → {response.get('grading_type')}\n"

        if submission_types is not None:
            old_types = ', '.join(current_assignment.get('submission_types', []))
            new_types = ', '.join(response.get('submission_types', []))
            result += f"  Submission Types: {old_types} → {new_types}\n"

        if allowed_extensions is not None:
            old_ext = ', '.join(current_assignment.get('allowed_extensions', [])) or 'None'
            new_ext = ', '.join(response.get('allowed_extensions', [])) or 'None'
            result += f"  Allowed Extensions: {old_ext} → {new_ext}\n"

        if published is not None:
            result += f"  Published: {current_assignment.get('published')} → {response.get('published')}\n"

        if omit_from_final_grade is not None:
            result += f"  Omit from Final Grade: {current_assignment.get('omit_from_final_grade')} → {response.get('omit_from_final_grade')}\n"

        if allowed_attempts is not None:
            old_attempts = current_assignment.get('allowed_attempts', 1)
            new_attempts = response.get('allowed_attempts', 1)
            old_display = "Unlimited" if old_attempts == -1 else str(old_attempts)
            new_display = "Unlimited" if new_attempts == -1 else str(new_attempts)
            result += f"  Allowed Attempts: {old_display} → {new_display}\n"

        return result

    @mcp.tool(name="canvas_assign_peer_review")
    async def assign_peer_review(course_identifier: str, assignment_id: str, reviewer_id: str, reviewee_id: str) -> str:
        """Manually assign a peer review to a student for a specific assignment.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID
            reviewer_id: The Canvas user ID of the student who will do the review
            reviewee_id: The Canvas user ID of the student whose submission will be reviewed
        """
        course_id = await get_course_id(course_identifier)
        
        # First, we need to get the submission ID for the reviewee
        submissions = await make_canvas_request(
            "get", 
            f"/courses/{course_id}/assignments/{assignment_id}/submissions",
            params={"per_page": 100}
        )
        
        if "error" in submissions:
            return f"Error fetching submissions: {submissions['error']}"
        
        # Find the submission for the reviewee
        reviewee_submission = None
        for submission in submissions:
            if str(submission.get("user_id")) == str(reviewee_id):
                reviewee_submission = submission
                break
        
        # If no submission exists, we need to create a placeholder submission
        if not reviewee_submission:
            # Create a placeholder submission for the reviewee
            placeholder_data = {
                "submission": {
                    "user_id": reviewee_id,
                    "submission_type": "online_text_entry",
                    "body": "Placeholder submission for peer review"
                }
            }
            
            reviewee_submission = await make_canvas_request(
                "post",
                f"/courses/{course_id}/assignments/{assignment_id}/submissions",
                data=placeholder_data
            )
            
            if "error" in reviewee_submission:
                return f"Error creating placeholder submission: {reviewee_submission['error']}"
        
        # Now assign the peer review using the submission ID
        submission_id = reviewee_submission.get("id")
        
        # Data for the peer review assignment
        data = {
            "user_id": reviewer_id  # The user who will do the review
        }
        
        # Make the API request to create the peer review
        response = await make_canvas_request(
            "post", 
            f"/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/peer_reviews",
            data=data
        )
        
        if "error" in response:
            return f"Error assigning peer review: {response['error']}"
        
        # Try to get the course code for display
        course_display = await get_course_code(course_id) or course_identifier
        
        return f"Successfully assigned peer review in course {course_display}:\n" + \
               f"Assignment ID: {assignment_id}\n" + \
               f"Reviewer ID: {reviewer_id}\n" + \
               f"Reviewee ID: {reviewee_id}\n" + \
               f"Submission ID: {submission_id}"

    @mcp.tool(name="canvas_list_peer_reviews")
    async def list_peer_reviews(course_identifier: str, assignment_id: str) -> str:
        """List all peer review assignments for a specific assignment.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Get all submissions for this assignment
        submissions = await fetch_all_paginated_results(
            f"/courses/{course_id}/assignments/{assignment_id}/submissions",
            {"include[]": "submission_comments", "per_page": 100}
        )
        
        if isinstance(submissions, dict) and "error" in submissions:
            return f"Error fetching submissions: {submissions['error']}"
        
        if not submissions:
            return f"No submissions found for assignment {assignment_id}."
        
        # Anonymize submission data to protect student privacy
        try:
            submissions = anonymize_response_data(submissions, data_type="submissions")
        except Exception as e:
            return f"Error: Failed to anonymize submission data: {str(e)}"

        # Get all users in the course for name lookups
        users = await fetch_all_paginated_results(
            f"/courses/{course_id}/users",
            {"per_page": 100}
        )

        if isinstance(users, dict) and "error" in users:
            return f"Error fetching users: {users['error']}"

        # Anonymize user data to protect student privacy
        try:
            users = anonymize_response_data(users, data_type="users")
        except Exception as e:
            return f"Error: Failed to anonymize user data: {str(e)}"
        
        # Create a mapping of user IDs to names
        user_map = {}
        for user in users:
            user_id = str(user.get("id"))
            user_name = user.get("name", "Unknown")
            user_map[user_id] = user_name
        
        # Collect peer review data
        peer_reviews_by_submission = {}
        
        for submission in submissions:
            submission_id = submission.get("id")
            user_id = str(submission.get("user_id"))
            user_name = user_map.get(user_id, f"User {user_id}")
            
            # Get peer reviews for this submission
            peer_reviews = await make_canvas_request(
                "get",
                f"/courses/{course_id}/assignments/{assignment_id}/submissions/{submission_id}/peer_reviews"
            )
            
            if "error" in peer_reviews:
                continue  # Skip if error
            
            if peer_reviews:
                peer_reviews_by_submission[submission_id] = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "peer_reviews": peer_reviews
                }
        
        # Format the output
        course_display = await get_course_code(course_id) or course_identifier
        output = f"Peer Reviews for Assignment {assignment_id} in course {course_display}:\n\n"
        
        if not peer_reviews_by_submission:
            output += "No peer reviews found for this assignment."
            return output
        
        # Display peer reviews grouped by reviewee
        for submission_id, data in peer_reviews_by_submission.items():
            reviewee_name = data["user_name"]
            reviewee_id = data["user_id"]
            reviews = data["peer_reviews"]
            
            output += f"Reviews for {reviewee_name} (ID: {reviewee_id}):\n"
            
            if not reviews:
                output += "  No peer reviews assigned.\n\n"
                continue
            
            for review in reviews:
                reviewer_id = str(review.get("user_id"))
                reviewer_name = user_map.get(reviewer_id, f"User {reviewer_id}")
                workflow_state = review.get("workflow_state", "Unknown")
                
                output += f"  Reviewer: {reviewer_name} (ID: {reviewer_id})\n"
                output += f"  Status: {workflow_state}\n"
                
                # Add assessment details if available
                if "assessment" in review and review["assessment"]:
                    assessment = review["assessment"]
                    score = assessment.get("score")
                    if score is not None:
                        output += f"  Score: {score}\n"
                
                output += "\n"
        
        return output

    @mcp.tool(name="canvas_list_submissions")
    @validate_params
    async def list_submissions(course_identifier: Union[str, int], assignment_id: Union[str, int]) -> str:
        """List submissions for a specific assignment.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Ensure assignment_id is a string
        assignment_id_str = str(assignment_id)
        
        params = {
            "per_page": 100
        }
        
        submissions = await fetch_all_paginated_results(
            f"/courses/{course_id}/assignments/{assignment_id_str}/submissions", params
        )
        
        if isinstance(submissions, dict) and "error" in submissions:
            return f"Error fetching submissions: {submissions['error']}"
        
        if not submissions:
            return f"No submissions found for assignment {assignment_id}."
        
        # Anonymize submission data to protect student privacy
        try:
            submissions = anonymize_response_data(submissions, data_type="submissions")
        except Exception as e:
            return f"Error: Failed to anonymize submission data: {str(e)}"
        
        submissions_info = []
        for submission in submissions:
            user_id = submission.get("user_id")
            submitted_at = submission.get("submitted_at", "Not submitted")
            score = submission.get("score", "Not graded")
            grade = submission.get("grade", "Not graded")
            
            submissions_info.append(
                f"User ID: {user_id}\nSubmitted: {submitted_at}\nScore: {score}\nGrade: {grade}\n"
            )
        
        # Try to get the course code for display
        course_display = await get_course_code(course_id) or course_identifier
        return f"Submissions for Assignment {assignment_id} in course {course_display}:\n\n" + "\n".join(submissions_info)

    @mcp.tool(name="canvas_get_assignment_analytics")
    @validate_params
    async def get_assignment_analytics(course_identifier: Union[str, int], assignment_id: Union[str, int]) -> str:
        """Get detailed analytics about student performance on a specific assignment.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID
        """
        course_id = await get_course_id(course_identifier)
        
        # Ensure assignment_id is a string
        assignment_id_str = str(assignment_id)
        
        # Get assignment details
        assignment = await make_canvas_request(
            "get", f"/courses/{course_id}/assignments/{assignment_id_str}"
        )
        
        if isinstance(assignment, dict) and "error" in assignment:
            return f"Error fetching assignment: {assignment['error']}"
        
        # Get all students in the course
        params = {
            "enrollment_type[]": "student",
            "per_page": 100
        }
        
        students = await fetch_all_paginated_results(
            f"/courses/{course_id}/users", params
        )
        
        if isinstance(students, dict) and "error" in students:
            return f"Error fetching students: {students['error']}"
        
        if not students:
            return f"No students found for course {course_identifier}."
        
        # Anonymize student data to protect privacy
        try:
            students = anonymize_response_data(students, data_type="users")
        except Exception as e:
            return f"Error: Failed to anonymize student data: {str(e)}"
        
        # Get submissions for this assignment
        submissions = await fetch_all_paginated_results(
            f"/courses/{course_id}/assignments/{assignment_id}/submissions", 
            {"per_page": 100, "include[]": ["user"]}
        )
        
        if isinstance(submissions, dict) and "error" in submissions:
            return f"Error fetching submissions: {submissions['error']}"
        
        # Anonymize submission data to protect student privacy
        try:
            submissions = anonymize_response_data(submissions, data_type="submissions")
        except Exception as e:
            return f"Error: Failed to anonymize submission data: {str(e)}"
        
        # Extract assignment details
        assignment_name = assignment.get("name", "Unknown Assignment")
        assignment_description = assignment.get("description", "No description")
        due_date = assignment.get("due_at")
        points_possible = assignment.get("points_possible", 0)
        is_published = assignment.get("published", False)
        
        # Format the due date
        due_date_str = "No due date"
        if due_date:
            try:
                due_date_obj = datetime.datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                due_date_str = due_date_obj.strftime("%Y-%m-%d %H:%M")
                now = datetime.datetime.now(datetime.timezone.utc)
                is_past_due = due_date_obj < now
            except (ValueError, AttributeError):
                due_date_str = due_date
                is_past_due = False
        else:
            is_past_due = False
        
        # Process submissions
        submission_stats = {
            "total_students": len(students),
            "submitted_count": 0,
            "missing_count": 0,
            "late_count": 0,
            "graded_count": 0,
            "excused_count": 0,
            "scores": [],
            "status_counts": {
                "submitted": 0,
                "unsubmitted": 0,
                "graded": 0,
                "pending_review": 0
            }
        }
        
        # Student status tracking
        student_status = []
        missing_students = []
        low_scoring_students = []
        high_scoring_students = []
        
        # Track which students have submissions
        student_ids_with_submissions = set()
        
        for submission in submissions:
            student_id = submission.get("user_id")
            student_ids_with_submissions.add(student_id)
            
            # Find student name
            student_name = "Unknown"
            for student in students:
                if student.get("id") == student_id:
                    student_name = student.get("name", "Unknown")
                    break
            
            # Process submission data
            score = submission.get("score")
            is_submitted = submission.get("submitted_at") is not None
            is_late = submission.get("late", False)
            is_missing = submission.get("missing", False)
            is_excused = submission.get("excused", False)
            is_graded = score is not None
            status = submission.get("workflow_state", "unsubmitted")
            submitted_at = submission.get("submitted_at")
            
            if submitted_at:
                try:
                    submitted_at = datetime.datetime.fromisoformat(
                        submitted_at.replace('Z', '+00:00')
                    ).strftime("%Y-%m-%d %H:%M")
                except (ValueError, AttributeError):
                    pass
            
            # Update statistics
            if is_submitted:
                submission_stats["submitted_count"] += 1
            if is_late:
                submission_stats["late_count"] += 1
            if is_missing:
                submission_stats["missing_count"] += 1
                missing_students.append(student_name)
            if is_excused:
                submission_stats["excused_count"] += 1
            if is_graded:
                submission_stats["graded_count"] += 1
                submission_stats["scores"].append(score)
                
                # Track high/low scoring students
                if points_possible > 0:
                    percentage = (score / points_possible) * 100
                    if percentage < 70:
                        low_scoring_students.append((student_name, score, percentage))
                    if percentage > 90:
                        high_scoring_students.append((student_name, score, percentage))
            
            # Update status counts
            if status in submission_stats["status_counts"]:
                submission_stats["status_counts"][status] += 1
            
            # Add to student status
            student_status.append({
                "name": student_name,
                "submitted": is_submitted,
                "submitted_at": submitted_at,
                "late": is_late,
                "missing": is_missing,
                "excused": is_excused,
                "score": score,
                "status": status
            })
        
        # Find students with no submissions
        for student in students:
            if student.get("id") not in student_ids_with_submissions:
                student_name = student.get("name", "Unknown")
                missing_students.append(student_name)
                
                # Add to student status
                student_status.append({
                    "name": student_name,
                    "submitted": False,
                    "submitted_at": None,
                    "late": False,
                    "missing": True,
                    "excused": False,
                    "score": None,
                    "status": "unsubmitted"
                })
        
        # Compute grade statistics
        scores = submission_stats["scores"]
        avg_score = mean(scores) if scores else 0
        median_score = median(scores) if scores else 0
        
        try:
            std_dev = stdev(scores) if len(scores) > 1 else 0
        except Exception:
            std_dev = 0
        
        if points_possible > 0:
            avg_percentage = (avg_score / points_possible) * 100
        else:
            avg_percentage = 0
        
        # Format the output
        course_display = await get_course_code(course_id) or course_identifier
        output = f"Assignment Analytics for '{assignment_name}' in Course {course_display}\n\n"
        
        # Assignment details
        output += "Assignment Details:\n"
        output += f"  Due: {due_date_str}"
        if is_past_due:
            output += " (Past Due)"
        output += "\n"
        
        output += f"  Points Possible: {points_possible}\n"
        output += f"  Published: {'Yes' if is_published else 'No'}\n\n"
        
        # Submission statistics
        output += "Submission Statistics:\n"
        total_students = submission_stats["total_students"]
        submitted = submission_stats["submitted_count"]
        graded = submission_stats["graded_count"]
        missing = submission_stats["missing_count"] + (total_students - len(submissions))
        late = submission_stats["late_count"]
        
        # Calculate percentages
        submitted_pct = (submitted / total_students * 100) if total_students > 0 else 0
        graded_pct = (graded / total_students * 100) if total_students > 0 else 0
        missing_pct = (missing / total_students * 100) if total_students > 0 else 0
        late_pct = (late / submitted * 100) if submitted > 0 else 0
        
        output += f"  Submitted: {submitted}/{total_students} ({round(submitted_pct, 1)}%)\n"
        output += f"  Graded: {graded}/{total_students} ({round(graded_pct, 1)}%)\n"
        output += f"  Missing: {missing}/{total_students} ({round(missing_pct, 1)}%)\n"
        if submitted > 0:
            output += f"  Late: {late}/{submitted} ({round(late_pct, 1)}% of submissions)\n"
        output += f"  Excused: {submission_stats['excused_count']}\n\n"
        
        # Grade statistics
        if scores:
            output += "Grade Statistics:\n"
            output += f"  Average Score: {round(avg_score, 2)}/{points_possible} ({round(avg_percentage, 1)}%)\n"
            output += f"  Median Score: {round(median_score, 2)}/{points_possible} ({round((median_score/points_possible)*100, 1)}%)\n"
            output += f"  Standard Deviation: {round(std_dev, 2)}\n"
            
            # High/Low scores
            if low_scoring_students:
                output += "\nStudents Scoring Below 70%:\n"
                for name, score, percentage in sorted(low_scoring_students, key=lambda x: x[2]):
                    output += f"  {name}: {round(score, 1)}/{points_possible} ({round(percentage, 1)}%)\n"
            
            if high_scoring_students:
                output += "\nStudents Scoring Above 90%:\n"
                for name, score, percentage in sorted(high_scoring_students, key=lambda x: x[2], reverse=True):
                    output += f"  {name}: {round(score, 1)}/{points_possible} ({round(percentage, 1)}%)\n"
        
        # Missing students
        if missing_students:
            output += "\nStudents Missing Submission:\n"
            # Sort alphabetically and show first 10
            for name in sorted(missing_students)[:10]:
                output += f"  {name}\n"
            if len(missing_students) > 10:
                output += f"  ...and {len(missing_students) - 10} more\n"
        
        return output

    @mcp.tool(name="canvas_delete_assignment")
    @validate_params
    async def delete_assignment(course_identifier: Union[str, int],
                              assignment_id: Union[str, int]) -> str:
        """Delete a specific assignment from a course.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_id: The Canvas assignment ID to delete
        """
        course_id = await get_course_id(course_identifier)
        
        # First get the assignment details before deleting
        assignment_response = await make_canvas_request(
            "get", f"/courses/{course_id}/assignments/{assignment_id}"
        )
        
        assignment_name = "Unknown assignment"
        points_possible = 0
        if "error" not in assignment_response:
            assignment_name = assignment_response.get("name", "Unknown assignment")
            points_possible = assignment_response.get("points_possible", 0)
        
        # Delete the assignment
        response = await make_canvas_request(
            "delete", f"/courses/{course_id}/assignments/{assignment_id}"
        )
        
        if "error" in response:
            return f"Error deleting assignment: {response['error']}"
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Successfully deleted assignment from Course {course_display}:\n\n"
        result += f"Assignment: {assignment_name}\n"
        result += f"Assignment ID: {assignment_id}\n"
        result += f"Points: {points_possible}\n"
        
        return result

    @mcp.tool(name="canvas_bulk_delete_assignments")
    @validate_params
    async def bulk_delete_assignments(course_identifier: Union[str, int],
                                    assignment_ids: list = None,
                                    delete_unpublished: bool = False,
                                    delete_all: bool = False) -> str:
        """Delete multiple assignments from a course at once.
        
        Args:
            course_identifier: The Canvas course code (e.g., badm_554_120251_246794) or ID
            assignment_ids: List of assignment IDs to delete (e.g., [123, 456, 789])
            delete_unpublished: If True, delete all unpublished assignments (overrides assignment_ids)
            delete_all: If True, delete ALL assignments in the course (use with extreme caution!)
        """
        course_id = await get_course_id(course_identifier)
        
        # Safety check for delete_all
        if delete_all and not delete_unpublished and not assignment_ids:
            return ("⚠️ DANGEROUS OPERATION: To delete ALL assignments, you must confirm by setting "
                   "delete_all=true AND either providing specific assignment_ids or setting delete_unpublished=true. "
                   "This is a safety measure to prevent accidental deletion of all course content.")
        
        assignments_to_delete = []
        
        if delete_all or delete_unpublished:
            # Get all assignments first
            params = {
                "per_page": 100,
                "include[]": ["all_dates"]
            }
            all_assignments = await fetch_all_paginated_results(
                f"/courses/{course_id}/assignments", params
            )
            
            if isinstance(all_assignments, dict) and "error" in all_assignments:
                return f"Error fetching assignments: {all_assignments['error']}"
            
            if delete_all:
                assignments_to_delete = all_assignments
            elif delete_unpublished:
                assignments_to_delete = [
                    a for a in all_assignments 
                    if not a.get("published", True)
                ]
                
                if not assignments_to_delete:
                    return f"No unpublished assignments found to delete in course {course_identifier}."
        
        elif assignment_ids:
            # Convert to list of integers if needed
            try:
                assignment_ids = [int(aid) for aid in assignment_ids]
            except (ValueError, TypeError):
                return "Error: assignment_ids must be a list of integers."
            
            # Get details for specific assignments
            for aid in assignment_ids:
                assignment_response = await make_canvas_request(
                    "get", f"/courses/{course_id}/assignments/{aid}"
                )
                if "error" not in assignment_response:
                    assignments_to_delete.append(assignment_response)
        else:
            return "No deletion criteria specified. Use assignment_ids, delete_unpublished=true, or delete_all=true."
        
        if not assignments_to_delete:
            return "No assignments found to delete."
        
        # Delete assignments one by one
        results = []
        errors = []
        
        for assignment in assignments_to_delete:
            assignment_id = assignment.get("id")
            assignment_name = assignment.get("name", "Unknown assignment")
            points = assignment.get("points_possible", 0)
            published = assignment.get("published", False)
            
            response = await make_canvas_request(
                "delete", f"/courses/{course_id}/assignments/{assignment_id}"
            )
            
            if "error" in response:
                errors.append(f"Assignment '{assignment_name}' (ID: {assignment_id}): {response['error']}")
            else:
                status = "Published" if published else "Unpublished"
                results.append(f"✅ {assignment_name} ({points} pts, {status}, ID: {assignment_id})")
        
        course_display = await get_course_code(course_id) or course_identifier
        
        result = f"Bulk Delete Results for Course {course_display}:\n\n"
        
        if results:
            result += f"Successfully deleted {len(results)} assignments:\n"
            for success in results:
                result += f"{success}\n"
            result += "\n"
        
        if errors:
            result += f"Failed to delete {len(errors)} assignments:\n"
            for error in errors:
                result += f"❌ {error}\n"
        
        if not results and not errors:
            result += "No assignments were processed.\n"
        
        return result