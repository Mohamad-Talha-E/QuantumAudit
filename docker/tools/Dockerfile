# Toolbox image: everything the project needs, in one place.
#
# Why Debian 13 instead of Alpine:
#   Debian ships OpenSSL 3.5.x with ML-KEM / ML-DSA built in, and it uses
#   glibc, so the scientific Python packages (pandas, matplotlib) install
#   from pre-built wheels instead of compiling for ~15 minutes.
FROM debian:13-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        openssl \
        python3 \
        python3-pip \
        python3-venv \
        sqlite3 \
        tzdata \
    && rm -rf /var/lib/apt/lists/*

# Isolated virtualenv so system Python stays untouched.
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

# Fail fast if the image ever loses post-quantum support.
RUN openssl version \
    && openssl list -kem-algorithms | grep -qi 'ML-KEM-768' \
    && openssl list -signature-algorithms | grep -qi 'ML-DSA-65' \
    && echo "post-quantum support OK"
