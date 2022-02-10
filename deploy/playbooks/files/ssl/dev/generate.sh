#!/bin/bash
# Easily generate a 10 year SSL certificate and key for development.  It
# creates a configuration file for wild card domains, if no argument is passed
# in will fallback to "node.a" as the domain to use.
#
# Upon completion, these files should now exist::
#
#   * openssl.cnf
#   * ssl.key
#   * ssl.crt
#
# If those files exist they will be overwritten

set -e

if [ ! -z $1 ]
then
    domain=$1
else
    domain="node.a"
fi

template="[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no
[req_distinguished_name]
CN = *.${domain}
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = *.${domain}"

echo "-> generating openssl.cnf configuration file"
echo "$template" > openssl.cnf
command="openssl req -new -newkey rsa:2048 -sha256 -days 3650 -nodes -x509 -keyout ssl.key -out ssl.crt -config openssl.cnf"
echo "-> running: $command"
eval $command
echo "-> completed self signed certs"
