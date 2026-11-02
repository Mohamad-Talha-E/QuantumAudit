#!/usr/bin/env bash
# Start the 20 ground-truth TLS servers on ports 8443-8462.
#
# Each line is: port|name|cert|protocol|groups|cipher(TLS1.2)|ciphersuite(TLS1.3)
set -uo pipefail

cd "$(dirname "$0")/.."
CERTS="${CERTS_DIR:-lab/certs}"
LOGS="${LOG_DIR:-lab/logs}"
mkdir -p "$LOGS"

if [ ! -f "$CERTS/ca.pem" ]; then
  bash lab/genlab.sh
fi

CONFIGS='
8443|rsa2048-x25519|rsa2048|tls1_3|X25519||
8444|rsa4096-x25519|rsa4096|tls1_3|X25519||
8445|ecdsa256-x25519|ecdsa256|tls1_3|X25519||
8446|ecdsa384-p256|ecdsa384|tls1_3|P-256||
8447|rsa2048-hybrid|rsa2048|tls1_3|X25519MLKEM768||
8448|rsa2048-mlkem768|rsa2048|tls1_3|MLKEM768||
8449|mldsa65-x25519|mldsa65|tls1_3|X25519||
8450|mldsa65-hybrid|mldsa65|tls1_3|X25519MLKEM768||
8451|tls12-rsa2048-p256|rsa2048|tls1_2|P-256|ECDHE-RSA-AES256-GCM-SHA384|
8452|tls12-rsa4096-p384|rsa4096|tls1_2|P-384|ECDHE-RSA-AES256-GCM-SHA384|
8453|tls12-ecdsa256-p256|ecdsa256|tls1_2|P-256|ECDHE-ECDSA-AES256-GCM-SHA384|
8454|rsa2048-p256|rsa2048|tls1_3|P-256||
8455|ecdsa256-p384|ecdsa256|tls1_3|P-384||
8456|ed25519-x25519|ed25519|tls1_3|X25519||
8457|rsa2048-x448|rsa2048|tls1_3|X448||
8458|rsa2048-aes128|rsa2048|tls1_3|X25519||TLS_AES_128_GCM_SHA256
8459|ecdsa384-mlkem768|ecdsa384|tls1_3|MLKEM768||
8460|tls12-rsa2048-aes128|rsa2048|tls1_2|X25519|AES128-SHA|
8461|rsa2048-secp256r1mlkem|rsa2048|tls1_3|SecP256r1MLKEM768||
8462|mldsa65-mlkem768|mldsa65|tls1_3|MLKEM768||
'

pids=()
cleanup() {
  if [ ${#pids[@]} -gt 0 ]; then
    kill "${pids[@]}" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting lab servers..."
while IFS='|' read -r port name cert proto groups cipher ciphersuite; do
  [ -z "$port" ] && continue

  args=(-accept "$port" -cert "$CERTS/$cert.pem" -key "$CERTS/$cert.key"
        -www -quiet -naccept 100000)

  case "$proto" in
    tls1_3) args+=(-tls1_3) ;;
    tls1_2) args+=(-tls1_2) ;;
  esac
  [ -n "$groups" ] && args+=(-groups "$groups")
  [ -n "$cipher" ] && args+=(-cipher "$cipher")
  [ -n "$ciphersuite" ] && args+=(-ciphersuites "$ciphersuite")

  openssl s_server "${args[@]}" >"$LOGS/$name.log" 2>&1 &
  pids+=($!)
  echo "  $port  $name"
done <<< "$CONFIGS"

echo "Lab up: 20 servers, ports 8443-8462."
wait
