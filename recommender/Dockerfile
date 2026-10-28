FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless tzdata \
    && ln -sfn "$(dirname "$(dirname "$(readlink -f /usr/bin/java)")")" /opt/java-home \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/opt/java-home

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY config.py content_sim.py train_als.py ./

CMD ["sh", "-c", "python content_sim.py && python train_als.py"]
