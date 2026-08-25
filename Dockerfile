FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data output/digests logs

# Don't run the process as root — a container escape or dependency RCE
# would otherwise hand an attacker root inside the image for free.
RUN useradd --create-home --uid 1000 signalharvest \
    && chown -R signalharvest:signalharvest /app
USER signalharvest

EXPOSE 8000

# Shell form (not exec-array) so $PORT is substituted at container start —
# the host (Render, etc.) injects its own PORT; local runs default to 8000.
CMD uvicorn gateway.main:app --host 0.0.0.0 --port ${PORT:-8000}
