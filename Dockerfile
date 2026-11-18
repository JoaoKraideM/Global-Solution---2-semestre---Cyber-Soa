FROM python:3.12-slim
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/build_css.py
EXPOSE 8000
CMD ["sh", "scripts/start.sh"]
