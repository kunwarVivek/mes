# Email Service Adapter Architecture

Pluggable email service supporting multiple providers (SMTP, SendGrid, AWS SES) with Billion Mail integration.

## Architecture

- **EmailService**: Abstract interface defining the contract
- **Adapters**: Provider-specific implementations (SMTP, SendGrid, AWS SES)
- **Factory**: Runtime provider selection based on configuration

## Usage

### Basic Usage with Factory

```python
from app.infrastructure.email import EmailServiceFactory
from app.core.config import settings

# Create email service based on configuration
email_service = EmailServiceFactory.create(settings)

# Send plain text email
success = email_service.send_email(
    from_email="noreply@example.com",
    to_email="user@example.com",
    subject="Welcome to Unison",
    body="Thank you for joining us!"
)

# Send HTML email
success = email_service.send_email(
    from_email="noreply@example.com",
    to_email="user@example.com",
    subject="Welcome to Unison",
    body="Thank you for joining us!",
    html_body="<html><body><h1>Thank you for joining us!</h1></body></html>"
)
```

### Direct Adapter Usage

```python
from app.infrastructure.email import SMTPEmailAdapter, SendGridEmailAdapter, AWSEmailAdapter
from app.core.config import settings

# Use SMTP adapter directly
smtp_service = SMTPEmailAdapter(settings)
smtp_service.send_email(...)

# Use SendGrid adapter directly
sendgrid_service = SendGridEmailAdapter(settings)
sendgrid_service.send_email(...)

# Use AWS SES adapter directly
aws_service = AWSEmailAdapter(settings)
aws_service.send_email(...)
```

## Configuration

Set the email provider in your `.env` file:

```env
# Email Provider Selection (smtp, sendgrid, aws_ses)
EMAIL_PROVIDER=smtp

# SMTP Configuration
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_TLS=True

# SendGrid Configuration
SENDGRID_API_KEY=your-sendgrid-api-key

# AWS SES Configuration
AWS_SES_REGION=us-east-1
AWS_SES_ACCESS_KEY=your-aws-access-key
AWS_SES_SECRET_KEY=your-aws-secret-key
```

## Adding New Providers

To add a new email provider:

1. Create a new adapter class implementing `EmailService`
2. Add configuration settings to `app/core/config.py`
3. Update `EmailServiceFactory.create()` to include the new provider
4. Add comprehensive tests in `tests/unit/test_email_service.py`

Example:

```python
from app.application.services.email_service import EmailService
from app.core.config import Settings

class MailgunEmailAdapter(EmailService):
    def __init__(self, settings: Settings):
        self.api_key = settings.MAILGUN_API_KEY
        self.domain = settings.MAILGUN_DOMAIN

    def send_email(self, from_email: str, to_email: str, subject: str,
                   body: str, html_body: Optional[str] = None) -> bool:
        # Implementation here
        pass
```

## Billion Mail Integration

New self-hosted email notification system using Billion Mail SMTP with async processing.

### Features

- Direct SMTP integration with Billion Mail server
- Jinja2-based HTML and plain text templates
- Async background processing via PGMQ
- Pre-built notifications for materials, work orders, inventory, MRP, and user activities
- Attachment support (PDF, Excel reports)
- Automatic retry with exponential backoff
- Email audit logging

### Usage

```python
from app.infrastructure.email import NotificationEmailService
from app.core.config import settings

# Initialize Billion Mail service
email_service = NotificationEmailService(settings)

# Send material created notification
email_service.send_material_created(
    recipient_email="user@example.com",
    recipient_name="John Doe",
    material_code="MAT-001",
    material_description="Steel Plate 10mm",
    created_by="admin",
    base_uom="EA"
)

# Send asynchronously via PGMQ
msg_id = email_service.send_material_created_async(...)
```

### Available Notifications

1. `send_material_created()` - Material master data created
2. `send_work_order_released()` - Work order released for production
3. `send_low_stock_alert()` - Inventory below reorder point
4. `send_mrp_completed()` - MRP run completion

### Templates

All templates located in `templates/` with both HTML and TXT versions:
- `material_created.{html,txt}`
- `work_order_released.{html,txt}`
- `low_stock_alert.{html,txt}`
- `mrp_completed.{html,txt}`
- `user_welcome.{html,txt}`
- `password_reset.{html,txt}`

## Testing

Run email service tests:

```bash
# All email tests
python3 -m pytest tests/unit/infrastructure/test_email*.py tests/unit/infrastructure/test_billion_mail_service.py -v

# Results: 28 passed, 1 warning in 0.56s
```

All adapters include dependency injection for testability, allowing mock clients to be passed for unit testing.

## Error Handling

All adapters return `True` on success and `False` on failure. Errors are logged but not raised, allowing graceful degradation. For production use, consider implementing:

- Retry logic for transient failures (✓ Implemented via PGMQ)
- Circuit breaker pattern for provider outages
- Fallback to alternative providers
- Email queue for deferred delivery (✓ Implemented via PGMQ)
