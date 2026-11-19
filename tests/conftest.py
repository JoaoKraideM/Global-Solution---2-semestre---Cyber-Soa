import os
os.environ['APP_ENV']='test'
os.environ['DATABASE_URL']='sqlite:///./test_unused.db'
os.environ['JWT_SECRET']='secret_super_forte_so_para_testes_2026'
os.environ['ADMIN_PASSWORD']='senha_segura_somente_de_teste'
os.environ['SENSOR_A_KEY']='chave_super_segura_a_somente_teste'
os.environ['SENSOR_B_KEY']='chave_super_segura_b_somente_teste'
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from app.auth import hash_device_key, hash_password
from app.database import Base, get_db
from app.main import app, failed_logins, failed_iot_keys
from app.models import User, Station, Reading, IotDevice
from datetime import datetime, timezone

@pytest.fixture
def client():
    engine = create_engine('sqlite://',connect_args={'check_same_thread':False},poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(User(email='admin@sombraviva.local',password_hash=hash_password(os.environ['ADMIN_PASSWORD']),role='admin'))
        db.add(Station(code='centro-demo',name='Centro (TESTE)',setting='Exposto',simulated=True,api_key_hash=hash_device_key(os.environ['SENSOR_A_KEY'])))
        db.add(Station(code='verde-demo',name='Verde (TESTE)',setting='Arborizado',simulated=True,api_key_hash=hash_device_key(os.environ['SENSOR_B_KEY'])))
        db.add(IotDevice(device_id='esp32-osasco-calcadao-01',name='ESP32 (TESTE)',token_hash=hash_device_key(os.environ['SENSOR_A_KEY'])))
        db.commit()
    def override_db():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    failed_logins.clear()
    failed_iot_keys.clear()
    with TestClient(app) as testclient:
        yield testclient
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def token(client):
    r=client.post('/api/v1/auth/login',json={'email':'admin@sombraviva.local','password':os.environ['ADMIN_PASSWORD']})
    assert r.status_code==200,r.text
    return r.json()['access_token']
