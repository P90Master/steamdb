import zoneinfo

from auth.core.config import settings


timezone = zoneinfo.ZoneInfo(settings.TIME_ZONE if settings.USE_TZ else 'UTC')
