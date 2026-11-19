"""Configuração do SombraViva para MySQL 8.x via PyMySQL."""
import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL, make_url

load_dotenv()


def build_database_url() -> URL:
    # DATABASE_URL permite conexões externas. Para uso comum, prefira DB_*:
    # URL.create realiza o escape de caracteres especiais da senha.
    override = os.getenv("DATABASE_URL", "").strip()
    if override:
        url = make_url(override)
        if url.get_backend_name() != "mysql" and not (
            os.getenv("APP_ENV") == "test" and url.get_backend_name() == "sqlite"
        ):
            raise ValueError("O banco da aplicação deve ser MySQL (mysql+pymysql://...).")
        return url
    return URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "sombraviva"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "sombraviva"),
        query={"charset": "utf8mb4"},
    )


DATABASE_URL = build_database_url()
JWT_SECRET = os.getenv("JWT_SECRET", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sombraviva.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SENSOR_A_KEY = os.getenv("SENSOR_A_KEY", "")
SENSOR_B_KEY = os.getenv("SENSOR_B_KEY", "")
# Dispositivo ESP32 do Wokwi. Sem token próprio, reutiliza a chave do sensor A.
ESP32_DEVICE_ID = os.getenv("ESP32_DEVICE_ID", "esp32-osasco-calcadao-01")
ESP32_DEVICE_TOKEN = os.getenv("ESP32_DEVICE_TOKEN", "") or SENSOR_A_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def require_secrets():
    values = [JWT_SECRET, ADMIN_PASSWORD, SENSOR_A_KEY, SENSOR_B_KEY]
    if any(len(s) < 16 or s.startswith("SUBSTITUA") for s in values):
        raise RuntimeError(
            "Configure JWT_SECRET, ADMIN_PASSWORD, SENSOR_A_KEY e SENSOR_B_KEY no .env "
            "(mínimo de 16 caracteres)."
        )
    if os.getenv("APP_ENV") != "test" and not os.getenv("DATABASE_URL", "").strip():
        password = os.getenv("DB_PASSWORD", "")
        if len(password) < 8 or password.startswith("SUBSTITUA"):
            raise RuntimeError("Configure DB_PASSWORD no .env (mínimo de 8 caracteres).")
