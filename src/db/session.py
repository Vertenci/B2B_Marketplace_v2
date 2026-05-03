from src.core.settings import settings
from src.db.database import Database

db = Database(str(settings.DATABASE_URL))
