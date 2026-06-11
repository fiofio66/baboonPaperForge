"""ORM model registry — import all models here so Base.metadata is complete."""

from app.models.task_record import TaskRecord  # noqa: F401
from app.models.template import TemplateMetadata  # noqa: F401
from app.models.user_config import LLMConfig, UserConfig  # noqa: F401
