#!/bin/sh
set -eu
# Falhas de migração/seed impedem servir uma aplicação com banco incompleto.
python -m app.bootstrap
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
