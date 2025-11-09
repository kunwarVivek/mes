import pytest
from unittest.mock import MagicMock, patch
from app.infrastructure.messaging.pgmq_client import PGMQClient, PGMQMessage


class TestPGMQClient:
    """Unit tests for PGMQClient using mocked PGMQ connection"""

    @pytest.fixture
    def mock_pgmq(self):
        """Mock the tembo_pgmq_python.PGMQueue class"""
        with patch("app.infrastructure.messaging.pgmq_client.PGMQueue") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_pgmq):
        """Create PGMQClient with mocked connection"""
        client = PGMQClient(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        return client

    def test_enqueue_creates_queue_and_sends_message(self, client, mock_pgmq):
        """Test enqueue creates queue on first use and sends message"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        queue_instance.send.return_value = 123

        # Act
        msg_id = client.enqueue("test_queue", {"task": "send_email", "user_id": 1})

        # Assert
        assert msg_id == 123
        queue_instance.send.assert_called_once()
        call_args = queue_instance.send.call_args[0]
        assert call_args[0] == "test_queue"
        assert call_args[1]["task"] == "send_email"
        assert call_args[1]["user_id"] == 1
        assert "retry_count" in call_args[1]
        assert call_args[1]["retry_count"] == 0

    def test_dequeue_returns_message_with_visibility_timeout(self, client, mock_pgmq):
        """Test dequeue returns message with visibility timeout"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        mock_message = MagicMock()
        mock_message.msg_id = 123
        mock_message.message = {"task": "send_email", "user_id": 1, "retry_count": 0}
        mock_message.vt = 30
        queue_instance.read.return_value = mock_message

        # Act
        message = client.dequeue("test_queue", vt=30)

        # Assert
        assert message is not None
        assert message.msg_id == 123
        assert message.message["task"] == "send_email"
        assert message.message["user_id"] == 1
        queue_instance.read.assert_called_once_with("test_queue", vt=30)

    def test_dequeue_returns_none_when_queue_empty(self, client, mock_pgmq):
        """Test dequeue returns None when no messages available"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        queue_instance.read.return_value = None

        # Act
        message = client.dequeue("test_queue")

        # Assert
        assert message is None

    def test_archive_marks_message_as_completed(self, client, mock_pgmq):
        """Test archive moves message to archive"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        queue_instance.archive.return_value = True

        # Act
        result = client.archive("test_queue", 123)

        # Assert
        assert result is True
        queue_instance.archive.assert_called_once_with("test_queue", 123)

    def test_delete_queue_removes_queue(self, client, mock_pgmq):
        """Test delete_queue removes queue from system"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        queue_instance.drop_queue.return_value = True

        # Act
        result = client.delete_queue("test_queue")

        # Assert
        assert result is True
        queue_instance.drop_queue.assert_called_once_with("test_queue")

    def test_retry_logic_increments_count(self, client, mock_pgmq):
        """Test that retry logic increments retry count"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        original_message = {"task": "send_email", "user_id": 1, "retry_count": 0}

        # Act
        client.retry_message("test_queue", 123, original_message)

        # Assert
        queue_instance.send.assert_called_once()
        sent_message = queue_instance.send.call_args[0][1]
        assert sent_message["retry_count"] == 1
        queue_instance.archive.assert_called_once_with("test_queue", 123)

    def test_move_to_dlq_after_max_retries(self, client, mock_pgmq):
        """Test message moves to DLQ after exceeding max retries"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        message_at_max_retries = {
            "task": "send_email",
            "user_id": 1,
            "retry_count": 3
        }

        # Act
        client.move_to_dlq("test_queue", 123, message_at_max_retries, "Task failed")

        # Assert
        # Should send to DLQ queue
        dlq_calls = [call for call in queue_instance.send.call_args_list
                     if "test_queue_dlq" in str(call)]
        assert len(dlq_calls) > 0
        # Should archive original message
        queue_instance.archive.assert_called_with("test_queue", 123)

    def test_process_with_retry_success_on_first_attempt(self, client, mock_pgmq):
        """Test process_with_retry succeeds on first attempt"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        mock_message = MagicMock()
        mock_message.msg_id = 123
        mock_message.message = {"task": "send_email", "user_id": 1, "retry_count": 0}

        def successful_task(msg):
            return {"status": "success"}

        # Act
        result = client.process_with_retry("test_queue", mock_message, successful_task)

        # Assert
        assert result["status"] == "success"
        queue_instance.archive.assert_called_once_with("test_queue", 123)

    def test_process_with_retry_retries_on_failure(self, client, mock_pgmq):
        """Test process_with_retry retries on failure"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        mock_message = MagicMock()
        mock_message.msg_id = 123
        mock_message.message = {"task": "send_email", "user_id": 1, "retry_count": 0}

        def failing_task(msg):
            raise Exception("Task failed")

        # Act
        result = client.process_with_retry("test_queue", mock_message, failing_task)

        # Assert
        assert result is None
        # Should retry by sending back to queue with incremented count
        queue_instance.send.assert_called_once()
        sent_message = queue_instance.send.call_args[0][1]
        assert sent_message["retry_count"] == 1

    def test_process_with_retry_moves_to_dlq_after_max_retries(self, client, mock_pgmq):
        """Test process_with_retry moves to DLQ after max retries"""
        # Arrange
        queue_instance = mock_pgmq.return_value
        mock_message = MagicMock()
        mock_message.msg_id = 123
        mock_message.message = {"task": "send_email", "user_id": 1, "retry_count": 3}

        def failing_task(msg):
            raise Exception("Task failed")

        # Act
        result = client.process_with_retry("test_queue", mock_message, failing_task)

        # Assert
        assert result is None
        # Should send to DLQ
        dlq_calls = [call for call in queue_instance.send.call_args_list
                     if "test_queue_dlq" in str(call)]
        assert len(dlq_calls) > 0
