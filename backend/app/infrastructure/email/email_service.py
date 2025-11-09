"""Notification email service for Billion Mail integration."""
import logging
from typing import Optional, Dict, Any

from app.infrastructure.email.smtp_client import BillionMailSMTPClient
from app.infrastructure.email.templates import TemplateManager
from app.infrastructure.email.models import EmailMessage, EmailRecipient
from app.infrastructure.messaging.pgmq_client import PGMQClient
from app.core.config import Settings

logger = logging.getLogger(__name__)


class NotificationEmailService:
    """Service for sending domain-specific email notifications.

    Provides high-level methods for sending different types of notifications
    (material changes, work orders, inventory alerts, etc.) using templates
    and async processing via PGMQ.
    """

    def __init__(
        self,
        settings: Settings,
        from_email: Optional[str] = None,
        from_name: str = "Unison ERP"
    ):
        """Initialize notification email service.

        Args:
            settings: Application settings with SMTP configuration
            from_email: Custom from email address (defaults to SMTP_USER)
            from_name: Sender display name
        """
        self.settings = settings
        self.from_email = from_email or settings.SMTP_USER
        self.from_name = from_name

        # Initialize SMTP client
        self.smtp_client = BillionMailSMTPClient(
            host=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            user=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_TLS
        )

        # Initialize template manager
        self.template_manager = TemplateManager()

        # Initialize PGMQ client for async processing
        self.pgmq_client = PGMQClient(
            host=settings.POSTGRES_SERVER,
            port=int(settings.POSTGRES_PORT),
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            max_retries=settings.PGMQ_RETRY_COUNT
        )

    def send_material_created(
        self,
        recipient_email: str,
        recipient_name: str,
        material_code: str,
        material_description: str,
        created_by: str,
        base_uom: str
    ) -> bool:
        """Send material created notification.

        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's display name
            material_code: Material code (e.g., MAT-001)
            material_description: Material description
            created_by: User who created the material
            base_uom: Base unit of measure

        Returns:
            bool: True if sent successfully
        """
        context = {
            "material_code": material_code,
            "material_description": material_description,
            "created_by": created_by,
            "base_uom": base_uom
        }

        return self._send_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=f"Material Created: {material_code}",
            template_name="material_created",
            context=context
        )

    def send_work_order_released(
        self,
        recipient_email: str,
        recipient_name: str,
        work_order_number: str,
        material_code: str,
        quantity: int,
        status: str
    ) -> bool:
        """Send work order released notification.

        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's display name
            work_order_number: Work order number
            material_code: Material to produce
            quantity: Production quantity
            status: Work order status

        Returns:
            bool: True if sent successfully
        """
        context = {
            "work_order_number": work_order_number,
            "material_code": material_code,
            "quantity": quantity,
            "status": status
        }

        return self._send_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=f"Work Order Released: {work_order_number}",
            template_name="work_order_released",
            context=context
        )

    def send_low_stock_alert(
        self,
        recipient_email: str,
        recipient_name: str,
        material_code: str,
        material_description: str,
        current_stock: int,
        reorder_point: int,
        warehouse: str
    ) -> bool:
        """Send low stock alert notification.

        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's display name
            material_code: Material code with low stock
            material_description: Material description
            current_stock: Current stock level
            reorder_point: Reorder point threshold
            warehouse: Warehouse code

        Returns:
            bool: True if sent successfully
        """
        context = {
            "material_code": material_code,
            "material_description": material_description,
            "current_stock": current_stock,
            "reorder_point": reorder_point,
            "warehouse": warehouse
        }

        return self._send_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=f"Low Stock Alert: {material_code}",
            template_name="low_stock_alert",
            context=context
        )

    def send_mrp_completed(
        self,
        recipient_email: str,
        recipient_name: str,
        run_id: str,
        planned_orders_count: int,
        execution_time: str
    ) -> bool:
        """Send MRP completion notification.

        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's display name
            run_id: MRP run identifier
            planned_orders_count: Number of planned orders created
            execution_time: MRP execution time

        Returns:
            bool: True if sent successfully
        """
        context = {
            "run_id": run_id,
            "planned_orders_count": planned_orders_count,
            "execution_time": execution_time
        }

        return self._send_notification(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            subject=f"MRP Run Completed: {run_id}",
            template_name="mrp_completed",
            context=context
        )

    def send_material_created_async(
        self,
        recipient_email: str,
        recipient_name: str,
        material_code: str,
        material_description: str,
        created_by: str,
        base_uom: str
    ) -> int:
        """Enqueue material created notification for async processing.

        Args:
            Same as send_material_created()

        Returns:
            int: PGMQ message ID
        """
        email_data = {
            "task": "send_material_created",
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "material_code": material_code,
            "material_description": material_description,
            "created_by": created_by,
            "base_uom": base_uom
        }

        return self._enqueue_email(email_data)

    def _send_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        """Send notification email using template.

        Args:
            recipient_email: Recipient's email address
            recipient_name: Recipient's display name
            subject: Email subject
            template_name: Name of the template to use
            context: Template context variables

        Returns:
            bool: True if sent successfully
        """
        try:
            # Render templates
            body_html = self.template_manager.render(template_name, context)
            body_text = self.template_manager.render_text(template_name, context)

            # Create email message
            recipient = EmailRecipient(email=recipient_email, name=recipient_name)
            message = EmailMessage(
                to=recipient,
                subject=subject,
                body_text=body_text,
                body_html=body_html,
                from_email=self.from_email,
                from_name=self.from_name
            )

            # Send via SMTP
            return self.smtp_client.send(message)

        except Exception as e:
            logger.error(f"Failed to send notification to {recipient_email}: {e}")
            return False

    def _enqueue_email(self, email_data: Dict[str, Any]) -> int:
        """Enqueue email to PGMQ for async processing.

        Args:
            email_data: Email task data

        Returns:
            int: PGMQ message ID
        """
        queue_name = "email_notifications"
        return self.pgmq_client.enqueue(queue_name, email_data)
