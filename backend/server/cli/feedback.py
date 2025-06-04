#!/usr/bin/env python3
"""
CLI tool for querying and managing user feedback.
"""

import click
import json
from datetime import datetime
from typing import Optional
from backend.server.database.models import Feedback
from backend.server.database.connection import get_db_connection
from backend.logger.logging_config import configure_logging

# Configure logging
logger = configure_logging(log_file="feedback_cli.log")


@click.group()
def feedback():
    """Feedback management commands."""
    pass


@feedback.command()
@click.option("--user-id", help="Filter feedback by user ID")
@click.option(
    "--limit", default=100, help="Maximum number of feedback entries to return"
)
@click.option("--offset", default=0, help="Number of feedback entries to skip")
@click.option("--output", type=click.Path(), help="Output file path (JSON format)")
def list(user_id: Optional[str], limit: int, offset: int, output: Optional[str]):
    """List feedback entries with optional filtering."""
    try:
        feedback_entries = Feedback.list_feedback(
            user_id=user_id, limit=limit, offset=offset
        )

        # Format the output
        formatted_entries = []
        for entry in feedback_entries:
            formatted_entry = {
                "feedback_id": entry["feedback_id"],
                "user_id": entry["user_id"],
                "answer_id": entry["answer_id"],
                "like": entry["like"],
                "suggestion": entry["suggestion"],
                "created_at": entry["created_at"],
                "updated_at": entry["updated_at"],
            }
            formatted_entries.append(formatted_entry)

        # Output to file or console
        if output:
            with open(output, "w") as f:
                json.dump(formatted_entries, f, indent=2)
            click.echo(f"Feedback entries written to {output}")
        else:
            click.echo(json.dumps(formatted_entries, indent=2))

    except Exception as e:
        logger.error(f"Error listing feedback: {str(e)}")
        raise click.ClickException(str(e))


@feedback.command()
@click.argument("user_id")
@click.argument("answer_id")
def get(user_id: str, answer_id: str):
    """Get feedback for a specific user/answer pair."""
    try:
        feedback = Feedback.get(user_id=user_id, answer_id=answer_id)
        if feedback:
            click.echo(json.dumps(feedback, indent=2))
        else:
            click.echo("No feedback found for this user/answer pair")
    except Exception as e:
        logger.error(f"Error getting feedback: {str(e)}")
        raise click.ClickException(str(e))


@feedback.command()
@click.option(
    "--since", type=click.DateTime(), help="Filter feedback created since this date"
)
@click.option(
    "--until", type=click.DateTime(), help="Filter feedback created until this date"
)
@click.option("--output", type=click.Path(), help="Output file path (JSON format)")
def stats(since: Optional[datetime], until: Optional[datetime], output: Optional[str]):
    """Get feedback statistics."""
    try:
        conn = get_db_connection()
        try:
            # Build query
            query = """
                SELECT
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN like = 1 THEN 1 ELSE 0 END) as positive_feedback,
                    SUM(CASE WHEN like = 0 THEN 1 ELSE 0 END) as negative_feedback,
                    COUNT(CASE WHEN suggestion IS NOT NULL THEN 1 END) as feedback_with_suggestions
                FROM feedback
            """
            params = []

            if since or until:
                query += " WHERE "
                conditions = []
                if since:
                    conditions.append("created_at >= ?")
                    params.append(since)
                if until:
                    conditions.append("created_at <= ?")
                    params.append(until)
                query += " AND ".join(conditions)

            cursor = conn.execute(query, params)
            stats = dict(cursor.fetchone())

            # Calculate percentages
            total = stats["total_feedback"]
            if total > 0:
                stats["positive_percentage"] = round(
                    (stats["positive_feedback"] / total) * 100, 2
                )
                stats["negative_percentage"] = round(
                    (stats["negative_feedback"] / total) * 100, 2
                )
                stats["suggestion_percentage"] = round(
                    (stats["feedback_with_suggestions"] / total) * 100, 2
                )

            # Output to file or console
            if output:
                with open(output, "w") as f:
                    json.dump(stats, f, indent=2)
                click.echo(f"Feedback statistics written to {output}")
            else:
                click.echo(json.dumps(stats, indent=2))

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error getting feedback statistics: {str(e)}")
        raise click.ClickException(str(e))


@feedback.command()
@click.option("--user-id", help="Filter dislikes by user ID")
@click.option("--limit", default=100, help="Maximum number of entries to return")
@click.option("--offset", default=0, help="Number of entries to skip")
@click.option("--output", type=click.Path(), help="Output file path (JSON format)")
def dislikes(user_id: Optional[str], limit: int, offset: int, output: Optional[str]):
    """List all negative feedback entries."""
    try:
        conn = get_db_connection()
        try:
            query = "SELECT * FROM feedback WHERE like = 0"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            entries = [dict(row) for row in cursor.fetchall()]

            if output:
                with open(output, "w") as f:
                    json.dump(entries, f, indent=2)
                click.echo(f"Dislike entries written to {output}")
            else:
                click.echo(json.dumps(entries, indent=2))

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error listing dislikes: {str(e)}")
        raise click.ClickException(str(e))


@feedback.command()
@click.option("--user-id", help="Filter suggestions by user ID")
@click.option("--limit", default=100, help="Maximum number of entries to return")
@click.option("--offset", default=0, help="Number of entries to skip")
@click.option("--output", type=click.Path(), help="Output file path (JSON format)")
def suggestions(user_id: Optional[str], limit: int, offset: int, output: Optional[str]):
    """List all feedback entries with suggestions."""
    try:
        conn = get_db_connection()
        try:
            query = "SELECT * FROM feedback WHERE suggestion IS NOT NULL"
            params = []

            if user_id:
                query += " AND user_id = ?"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = conn.execute(query, params)
            entries = [dict(row) for row in cursor.fetchall()]

            if output:
                with open(output, "w") as f:
                    json.dump(entries, f, indent=2)
                click.echo(f"Suggestion entries written to {output}")
            else:
                click.echo(json.dumps(entries, indent=2))

        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Error listing suggestions: {str(e)}")
        raise click.ClickException(str(e))


if __name__ == "__main__":
    feedback()
