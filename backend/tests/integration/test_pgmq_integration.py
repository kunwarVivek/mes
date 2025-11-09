import pytest
import os
from app.infrastructure.messaging.pgmq_client import PGMQClient


@pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS") == "true",
    reason="Integration tests require PostgreSQL with pgmq extension"
)
class TestPGMQIntegration:
    """Integration tests for PGMQClient with real PostgreSQL + pgmq extension"""

    @pytest.fixture
    def client(self):
        """Create PGMQClient with test database connection"""
        client = PGMQClient(
            host=os.getenv("POSTGRES_SERVER", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "unison_test"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres")
        )
        yield client
        # Cleanup: delete test queues
        try:
            client.delete_queue("integration_test_queue")
            client.delete_queue("integration_test_queue_dlq")
        except Exception:
            pass

    def test_full_workflow_enqueue_dequeue_archive(self, client):
        """Test complete workflow: enqueue -> dequeue -> process -> archive"""
        queue_name = "integration_test_queue"

        # Enqueue a message
        msg_id = client.enqueue(queue_name, {
            "task": "send_email",
            "email": "test@example.com",
            "user_id": 123
        })
        assert msg_id > 0

        # Dequeue the message
        message = client.dequeue(queue_name, vt=30)
        assert message is not None
        assert message.msg_id == msg_id
        assert message.message["task"] == "send_email"
        assert message.message["email"] == "test@example.com"
        assert message.message["retry_count"] == 0

        # Archive the message (mark as completed)
        result = client.archive(queue_name, msg_id)
        assert result is True

        # Verify queue is now empty
        next_message = client.dequeue(queue_name)
        assert next_message is None

    def test_visibility_timeout_prevents_duplicate_processing(self, client):
        """Test that visibility timeout prevents message from being read twice"""
        queue_name = "integration_test_queue"

        # Enqueue a message
        msg_id = client.enqueue(queue_name, {"task": "test_vt"})

        # Dequeue with short visibility timeout
        message1 = client.dequeue(queue_name, vt=2)
        assert message1 is not None

        # Try to dequeue immediately - should be None (still invisible)
        message2 = client.dequeue(queue_name, vt=2)
        assert message2 is None

        # Wait for visibility timeout to expire
        import time
        time.sleep(3)

        # Now should be able to dequeue again
        message3 = client.dequeue(queue_name, vt=2)
        assert message3 is not None
        assert message3.msg_id == msg_id

        # Cleanup
        client.archive(queue_name, msg_id)

    def test_retry_logic_with_failure(self, client):
        """Test retry logic when processing fails"""
        queue_name = "integration_test_queue"

        # Enqueue a message
        msg_id = client.enqueue(queue_name, {"task": "failing_task", "data": "test"})

        # Dequeue and simulate failure
        message = client.dequeue(queue_name)
        assert message is not None
        assert message.message["retry_count"] == 0

        # Retry the message
        client.retry_message(queue_name, message.msg_id, message.message)

        # Dequeue again - should have incremented retry count
        retried_message = client.dequeue(queue_name)
        assert retried_message is not None
        assert retried_message.message["retry_count"] == 1
        assert retried_message.message["task"] == "failing_task"

        # Cleanup
        client.archive(queue_name, retried_message.msg_id)

    def test_dead_letter_queue_after_max_retries(self, client):
        """Test that messages move to DLQ after max retries"""
        queue_name = "integration_test_queue"
        dlq_name = f"{queue_name}_dlq"

        # Enqueue a message that has already failed 3 times
        msg_id = client.enqueue(queue_name, {
            "task": "always_failing_task",
            "retry_count": 3
        })

        # Dequeue the message
        message = client.dequeue(queue_name)
        assert message is not None

        # Move to DLQ since it's at max retries
        client.move_to_dlq(queue_name, message.msg_id, message.message, "Max retries exceeded")

        # Check that message is in DLQ
        dlq_message = client.dequeue(dlq_name)
        assert dlq_message is not None
        assert dlq_message.message["task"] == "always_failing_task"
        assert dlq_message.message["retry_count"] == 3
        assert "error" in dlq_message.message
        assert "original_queue" in dlq_message.message

        # Cleanup
        client.archive(dlq_name, dlq_message.msg_id)

    def test_process_with_retry_integration(self, client):
        """Test process_with_retry with real queue"""
        queue_name = "integration_test_queue"

        # Enqueue a message
        msg_id = client.enqueue(queue_name, {"task": "process_data", "value": 42})

        # Dequeue message
        message = client.dequeue(queue_name)
        assert message is not None

        # Define a successful processor
        def successful_processor(msg):
            return {"status": "success", "result": msg["value"] * 2}

        # Process with retry
        result = client.process_with_retry(queue_name, message, successful_processor)

        # Verify success
        assert result["status"] == "success"
        assert result["result"] == 84

        # Verify queue is empty (message was archived)
        next_message = client.dequeue(queue_name)
        assert next_message is None

    def test_multiple_messages_fifo_order(self, client):
        """Test that multiple messages are processed in FIFO order"""
        queue_name = "integration_test_queue"

        # Enqueue multiple messages
        msg_ids = []
        for i in range(5):
            msg_id = client.enqueue(queue_name, {"task": "order_test", "order": i})
            msg_ids.append(msg_id)

        # Dequeue and verify order
        for expected_order in range(5):
            message = client.dequeue(queue_name)
            assert message is not None
            assert message.message["order"] == expected_order
            client.archive(queue_name, message.msg_id)

        # Verify queue is empty
        assert client.dequeue(queue_name) is None
