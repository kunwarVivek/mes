"""
PGMQ (PostgreSQL Message Queue) Client

Provides PostgreSQL-based message queue functionality using the pgmq extension.
Replaces Celery with a simpler, PostgreSQL-native solution for background jobs.

Features:
- Queue creation on first use
- Visibility timeout for message processing
- Automatic retry logic with exponential backoff
- Dead-letter queue (DLQ) for failed jobs
- Archive for completed jobs
"""

import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from tembo_pgmq_python import PGMQueue, Message

logger = logging.getLogger(__name__)


@dataclass
class PGMQMessage:
    """Wrapper for PGMQ message with metadata"""
    msg_id: int
    message: Dict[str, Any]
    vt: int
    read_count: int = 0


class PGMQClient:
    """
    PostgreSQL Message Queue Client using pgmq extension

    Provides reliable background job processing with:
    - Automatic queue creation
    - Configurable visibility timeout
    - Built-in retry logic
    - Dead-letter queue for failed jobs
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "unison",
        user: str = "postgres",
        password: str = "postgres",
        max_retries: int = 3
    ):
        """
        Initialize PGMQ client

        Args:
            host: PostgreSQL host
            port: PostgreSQL port
            database: PostgreSQL database name
            user: PostgreSQL user
            password: PostgreSQL password
            max_retries: Maximum retry attempts before moving to DLQ
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.max_retries = max_retries

        # Create connection to PostgreSQL with pgmq extension
        self.queue = PGMQueue(
            host=host,
            port=port,
            database=database,
            username=user,
            password=password
        )

        logger.info(f"PGMQ client initialized: {host}:{port}/{database}")

    def enqueue(self, queue_name: str, message: Dict[str, Any]) -> int:
        """
        Add message to queue

        Creates queue automatically on first use.
        Adds retry metadata to message payload.

        Args:
            queue_name: Name of the queue
            message: Message payload as dictionary

        Returns:
            Message ID assigned by PGMQ
        """
        # Add retry metadata if not present
        if "retry_count" not in message:
            message["retry_count"] = 0

        # Send message to queue (creates queue if doesn't exist)
        msg_id = self.queue.send(queue_name, message)

        logger.debug(f"Enqueued message {msg_id} to queue '{queue_name}'")
        return msg_id

    def dequeue(self, queue_name: str, vt: int = 30) -> Optional[PGMQMessage]:
        """
        Read message from queue with visibility timeout

        Args:
            queue_name: Name of the queue
            vt: Visibility timeout in seconds (default 30)

        Returns:
            PGMQMessage if available, None if queue is empty
        """
        raw_message = self.queue.read(queue_name, vt=vt)

        if raw_message is None:
            return None

        # Wrap in PGMQMessage for consistent interface
        message = PGMQMessage(
            msg_id=raw_message.msg_id,
            message=raw_message.message,
            vt=vt,
            read_count=getattr(raw_message, 'read_count', 0)
        )

        logger.debug(f"Dequeued message {message.msg_id} from queue '{queue_name}'")
        return message

    def archive(self, queue_name: str, msg_id: int) -> bool:
        """
        Archive message (mark as completed)

        Moves message to archive table for audit purposes.

        Args:
            queue_name: Name of the queue
            msg_id: Message ID to archive

        Returns:
            True if successful
        """
        result = self.queue.archive(queue_name, msg_id)
        logger.debug(f"Archived message {msg_id} from queue '{queue_name}'")
        return result

    def delete_queue(self, queue_name: str) -> bool:
        """
        Delete queue and all its messages

        Args:
            queue_name: Name of the queue to delete

        Returns:
            True if successful
        """
        result = self.queue.drop_queue(queue_name)
        logger.info(f"Deleted queue '{queue_name}'")
        return result

    def retry_message(
        self,
        queue_name: str,
        msg_id: int,
        message: Dict[str, Any]
    ) -> int:
        """
        Retry failed message by re-enqueueing with incremented retry count

        Args:
            queue_name: Name of the queue
            msg_id: Original message ID
            message: Message payload

        Returns:
            New message ID
        """
        # Increment retry count
        message["retry_count"] = message.get("retry_count", 0) + 1

        # Archive original message
        self.archive(queue_name, msg_id)

        # Re-enqueue with updated retry count
        new_msg_id = self.queue.send(queue_name, message)

        logger.info(
            f"Retrying message {msg_id} as {new_msg_id} "
            f"(attempt {message['retry_count']}/{self.max_retries})"
        )

        return new_msg_id

    def move_to_dlq(
        self,
        queue_name: str,
        msg_id: int,
        message: Dict[str, Any],
        error: str
    ) -> int:
        """
        Move message to Dead-Letter Queue after max retries exceeded

        Args:
            queue_name: Original queue name
            msg_id: Message ID
            message: Message payload
            error: Error message explaining failure

        Returns:
            DLQ message ID
        """
        dlq_name = f"{queue_name}_dlq"

        # Add DLQ metadata
        dlq_message = {
            **message,
            "original_queue": queue_name,
            "original_msg_id": msg_id,
            "error": error
        }

        # Send to DLQ
        dlq_msg_id = self.queue.send(dlq_name, dlq_message)

        # Archive original message
        self.archive(queue_name, msg_id)

        logger.warning(
            f"Moved message {msg_id} to DLQ '{dlq_name}' "
            f"after {message.get('retry_count', 0)} retries. Error: {error}"
        )

        return dlq_msg_id

    def process_with_retry(
        self,
        queue_name: str,
        message: PGMQMessage,
        processor: Callable[[Dict[str, Any]], Any]
    ) -> Optional[Any]:
        """
        Process message with automatic retry logic

        Args:
            queue_name: Name of the queue
            message: Message to process
            processor: Function to process message payload

        Returns:
            Result from processor if successful, None if failed
        """
        try:
            # Process the message
            result = processor(message.message)

            # Archive on success
            self.archive(queue_name, message.msg_id)

            logger.info(f"Successfully processed message {message.msg_id}")
            return result

        except Exception as e:
            retry_count = message.message.get("retry_count", 0)

            # Check if max retries exceeded
            if retry_count >= self.max_retries:
                # Move to DLQ
                self.move_to_dlq(
                    queue_name,
                    message.msg_id,
                    message.message,
                    str(e)
                )
                logger.error(
                    f"Message {message.msg_id} failed after {retry_count} retries: {e}"
                )
            else:
                # Retry the message
                self.retry_message(queue_name, message.msg_id, message.message)
                logger.warning(
                    f"Message {message.msg_id} failed, retrying "
                    f"(attempt {retry_count + 1}/{self.max_retries}): {e}"
                )

            return None
