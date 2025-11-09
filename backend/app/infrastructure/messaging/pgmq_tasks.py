"""
PGMQ Background Tasks

Replaces Celery tasks with PGMQ-based background job processing.
Tasks are enqueued to PostgreSQL message queues and processed asynchronously.

Usage:
    # Enqueue a task
    client = get_pgmq_client()
    client.enqueue("user_tasks", {
        "task": "send_welcome_email",
        "email": "user@example.com",
        "username": "john"
    })

    # Process tasks
    while True:
        message = client.dequeue("user_tasks")
        if message:
            client.process_with_retry("user_tasks", message, process_user_task)
"""

import logging
from typing import Dict, Any
from app.infrastructure.messaging.pgmq_client import PGMQClient
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_pgmq_client() -> PGMQClient:
    """
    Get configured PGMQ client instance

    Returns:
        Configured PGMQClient connected to application database
    """
    return PGMQClient(
        host=settings.POSTGRES_SERVER,
        port=int(settings.POSTGRES_PORT),
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        max_retries=settings.PGMQ_RETRY_COUNT
    )


def process_user_task(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process user-related background tasks

    Dispatcher function that routes messages to specific task handlers
    based on the 'task' field in the message.

    Args:
        message: Task message with 'task' field and task-specific parameters

    Returns:
        Result dictionary from task handler

    Raises:
        ValueError: If task type is unknown
    """
    task_type = message.get("task")

    if task_type == "send_welcome_email":
        return send_welcome_email(
            user_email=message["email"],
            username=message["username"]
        )
    elif task_type == "cleanup_inactive_users":
        return cleanup_inactive_users()
    elif task_type == "generate_user_report":
        return generate_user_report(user_id=message["user_id"])
    else:
        raise ValueError(f"Unknown task type: {task_type}")


def send_welcome_email(user_email: str, username: str) -> Dict[str, Any]:
    """
    Background task: Send welcome email to new user

    This is a demonstration task showing how to use PGMQ
    for background processing. In production, this would
    integrate with an email service (SendGrid, AWS SES, etc.)

    Args:
        user_email: User's email address
        username: User's display name

    Returns:
        Status dictionary with email details
    """
    logger.info(f"Sending welcome email to {user_email}")

    # Simulate email sending
    # In production: integrate with email service
    message = f"""
    Welcome {username}!

    Thank you for joining Unison.
    Your account has been successfully created.

    Best regards,
    The Unison Team
    """

    logger.info(f"Welcome email sent to {user_email}")
    return {"status": "sent", "email": user_email}


def cleanup_inactive_users() -> Dict[str, Any]:
    """
    Scheduled task: Clean up inactive users

    This could be scheduled to run periodically.
    Example: Delete users who haven't logged in for 365 days.

    Returns:
        Status dictionary with cleanup results
    """
    logger.info("Running inactive user cleanup task")

    # In production: query database and delete/deactivate users
    # Example logic:
    # - Find users inactive for > 365 days
    # - Send notification email
    # - Deactivate or delete account

    logger.info("Inactive user cleanup completed")
    return {"status": "completed", "users_processed": 0}


def generate_user_report(user_id: int) -> Dict[str, Any]:
    """
    Async task: Generate user activity report

    Long-running task that generates a comprehensive
    report of user activity and downloads as PDF/CSV.

    Args:
        user_id: User ID to generate report for

    Returns:
        Status dictionary with report details
    """
    logger.info(f"Generating report for user {user_id}")

    # In production:
    # 1. Query user data
    # 2. Generate charts/statistics
    # 3. Create PDF/CSV file
    # 4. Upload to S3 or file storage
    # 5. Send download link to user

    logger.info(f"Report generated for user {user_id}")
    return {
        "status": "completed",
        "user_id": user_id,
        "report_url": f"/reports/user-{user_id}.pdf"
    }


# Task queue worker example
def run_user_task_worker():
    """
    Worker process to consume user tasks from PGMQ

    This function runs in a loop, processing messages from the user_tasks queue.
    Run this in a separate process or container for production.

    Usage:
        python -m app.infrastructure.messaging.pgmq_tasks
    """
    client = get_pgmq_client()
    queue_name = "user_tasks"

    logger.info(f"Starting PGMQ worker for queue '{queue_name}'")

    try:
        while True:
            # Dequeue message with 30 second visibility timeout
            message = client.dequeue(queue_name, vt=settings.PGMQ_VISIBILITY_TIMEOUT)

            if message:
                logger.info(f"Processing message {message.msg_id}: {message.message.get('task')}")

                # Process with automatic retry logic
                result = client.process_with_retry(queue_name, message, process_user_task)

                if result:
                    logger.info(f"Message {message.msg_id} completed: {result}")
            else:
                # No messages available, wait before polling again
                import time
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # Run worker when executed directly
    run_user_task_worker()
