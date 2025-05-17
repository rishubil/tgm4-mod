FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libmagickwand-dev \
        ssh \
        sudo \
        unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
RUN adduser ubuntu sudo

RUN mkdir -p /project/tmg4-mod && chown -R ubuntu:ubuntu /project

COPY --from=ghcr.io/astral-sh/uv:0.7.4 /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT /project/.venv

USER ubuntu
WORKDIR /project/tmg4-mod

ADD pyproject.toml uv.lock /project/tmg4-mod

RUN uv sync --locked

ENV PATH="/project/.venv/bin:$PATH"