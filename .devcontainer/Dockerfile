FROM python:3.12-bookworm

# Some editor/host processes forward en_US.UTF-8 despite the container defaults.
# Generate it at build time so it also works after rebuilding the dev container.
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && localedef -i en_US -f UTF-8 en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
