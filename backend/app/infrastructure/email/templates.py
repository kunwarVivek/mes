"""Email template rendering using Jinja2."""
import os
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class TemplateManager:
    """Manager for email template rendering using Jinja2.

    Provides methods to render HTML and plain text email templates
    with dynamic context data.
    """

    def __init__(self):
        """Initialize TemplateManager with Jinja2 environment."""
        # Get templates directory path relative to this file
        templates_dir = os.path.join(
            os.path.dirname(__file__),
            "templates"
        )

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render HTML email template.

        Args:
            template_name: Name of the template (without .html extension)
            context: Dictionary of template variables

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        template_file = f"{template_name}.html"
        template = self.env.get_template(template_file)
        return template.render(**context)

    def render_text(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render plain text email template.

        Args:
            template_name: Name of the template (without .txt extension)
            context: Dictionary of template variables

        Returns:
            Rendered plain text string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        template_file = f"{template_name}.txt"
        template = self.env.get_template(template_file)
        return template.render(**context)
