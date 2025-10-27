"""
Compatibility wrapper that re-exports the shared scraper service.

The FastAPI backend expects `backend.data_scraper_service` to define the
singleton used at runtime. We now host the implementation at the project root,
so this module simply aliases the shared objects.
"""

from data_scraper_service import DataScraperService, scraper_service  # noqa: F401

__all__ = ["DataScraperService", "scraper_service"]

