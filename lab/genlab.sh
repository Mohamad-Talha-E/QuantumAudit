#!/usr/bin/env bash
# Generate the lab certificate authority and six leaf certificates.
#
# The guide's version of this script died on its first iteration: it read
# `alg=${spec#*:}` which gives "rsa:2048" (not "rsa"), so the RSA branch was
# never taken and it tried to build an EC curve called "P-2048".
set -euo pipefail

cd "$(dirname "$0")/.."
CERTS="${CERTS_DIR:-lab/certs}"
mkdir -p "$CERTS"
cd "$CERTS"

SAN="subjectAltName=DNS:localhost,DNS:lab,DNS:*.lab,IP:127.0.0.1"

if [ ! -f ca.pem ]; then
  echo "Creating lab certificate authority..."
  openssl req -x509 -newkey rsa:2048 -keyout ca.key -out ca.pem \
    -days 3650 -nodes -subj "/CN=QuantumAudit Lab CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" >/dev/null 2>&1
fi

sign() {
  local name="$1"
  openssl req -new -key "$name.key" -out "$name.csr" \
    -subj "/CN=$name.lab" -addext "$SAN" >/dev/null 2>&1
  openssl x509 -req -in "$name.csr" -CA ca.pem -CAkey ca.key \
    -CAcreateserial -out "$name.pem" -days 825 \
    -extfile <(printf '%s\nbasicConstraints=CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n' "$SAN") \
    >/dev/null 2>&1
  rm -f "$name.csr"
}

make_rsa() {
  local name="rsa$1"
  [ -f "$name.pem" ] && return
  echo "  $name"
  openssl genpkey -algorithm RSA -pkeyopt "rsa_keygen_bits:$1" -out "$name.key" >/dev/null 2>&1
  sign "$name"
}

make_ec() {
  local name="ecdsa$1" curve="$2"
  [ -f "$name.pem" ] && return
  echo "  $name"
  openssl genpkey -algorithm EC -pkeyopt "ec_paramgen_curve:$curve" -out "$name.key" >/dev/null 2>&1
  sign "$name"
}

make_ed25519() {
  [ -f ed25519.pem ] && return
  echo "  ed25519"
  openssl genpkey -algorithm ED25519 -out ed25519.key >/dev/null 2>&1
  sign ed25519
}

make_mldsa65() {
  [ -f mldsa65.pem ] && return
  echo "  mldsa65"
  openssl genpkey -algorithm ML-DSA-65 -out mldsa65.key >/dev/null 2>&1
  sign mldsa65
}

make_rsa 2048
make_rsa 4096
make_ec 256 P-256
make_ec 384 P-384
make_ed25519
make_mldsa65

echo "Lab certificates ready in $CERTS"
