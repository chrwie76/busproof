#!/bin/sh
# Runs once, in a container of its own, the first time the demo starts: every installation gets a
# password, a small certificate authority and a broker certificate of its own, and nothing secret
# is ever in the repository. The folder is ignored by Git and closed to AI assistants (AGENTS.md).
set -eu
cd /secrets

if [ -f password ]; then
    echo "credentials are there already"
    exit 0
fi

apk add --no-cache openssl > /dev/null
umask 077

# Strict clients (Python 3.13 by default) insist on these extensions.
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -keyout ca.key -out ca.crt \
    -subj "/CN=BusProof demo CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,keyCertSign,cRLSign" 2> /dev/null
openssl req -newkey rsa:2048 -nodes -keyout broker.key -out broker.csr \
    -subj "/CN=mosquitto" 2> /dev/null
cat > broker.ext <<EXTENSIONS
subjectAltName=DNS:mosquitto,DNS:localhost,IP:127.0.0.1
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
EXTENSIONS
openssl x509 -req -in broker.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 3650 \
    -extfile broker.ext -out broker.crt 2> /dev/null
rm broker.csr broker.ext ca.srl

# The broker runs as its own user. The units and the tests need the password and the CA to connect.
chown 1883 broker.key
chmod 644 ca.crt broker.crt

# Last, as its presence means that everything is there.
openssl rand -hex 16 > password
chmod 644 password
chmod 755 .
echo "credentials created"
