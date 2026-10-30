# One image for every machine: the argument picks which one a container is.
FROM python:3.13-slim

WORKDIR /app
COPY pyproject.toml config.json ./
COPY src ./src
RUN pip install --no-cache-dir .

USER nobody
ENV PLANT_CONFIG=/app/config.json PLANT_CONTRACTS=/contracts
ENTRYPOINT ["python", "-m", "plant"]
