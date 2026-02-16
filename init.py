from handlers.start import router as start_router
from handlers.surveys import router as surveys_router
from handlers.admin import router as admin_router

__all__ = ["start_router", "surveys_router", "admin_router"]