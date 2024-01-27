import os

from pathlib import Path

from pydantic import BaseSettings

env_path = Path("..") / ".env"
env_file = env_path


class Settings(BaseSettings):
    project_name: str = "UGC"

    jaeger_enabled: bool = os.getenv("JAEGER_ENABLED", "False") == "True"
    jaeger_host: str = os.getenv("JAEGER_HOST", "localhost")
    jaeger_port: int = int(os.getenv("JAEGER_PORT", 0))


class AuthjwtSettings(BaseSettings):
    authjwt_secret_key: str = os.getenv("AUTHJWT_SECRET_KEY", "secret")
    authjwt_token_location: set = {"cookies"}
    authjwt_refresh_cookie_key = "refresh_token"
    authjwt_access_cookie_key = "access_token"
    authjwt_access_token_expires: int = 3600  # seconds
    authjwt_cookie_csrf_protect: bool = False


class MongoSettings(BaseSettings):
    """Mongo uri must contain both services mongos1 and mongos2"""
    collection: str = "ugc_events"
    db: str = "movies_ugc"
    username: str = os.getenv("MONGO_INITDB_ROOT_USERNAME", "admin")
    password: str = os.getenv("MONGO_INITDB_ROOT_PASSWORD", "admin")
    hosts: str = os.getenv("MONGO_URI_HOSTS", "localhost:27019,localhost:27020")
    # hosts: str = os.getenv("MONGO_URI_HOSTS", "mongos1:27019,mongos2:27020")

    uri: str = os.getenv("MONGO_URI", f"mongodb://{username}:{password}@{hosts}/")


settings = Settings()
auth_jwt_settings = AuthjwtSettings()
mongo_settings = MongoSettings()
