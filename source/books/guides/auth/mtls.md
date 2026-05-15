# mTLS Authentication

Mutual TLS (mTLS) authenticates clients using X.509 certificates. The client presents a certificate signed by a trusted CA during the TLS handshake — no passwords, tokens, or cookies needed.

## How It Works

1. Client connects with a certificate signed by the app's trusted CA
2. Rustls verifies the certificate chain during the TLS handshake
3. `MtlsAuthProvider` extracts the Common Name (CN) and Subject Alternative Names (SANs)
4. CN is mapped to a username via the configured identity strategy
5. User's `roleId` resolves to a Role with permissions

## Configuration

Add `mtls` to your app's auth methods and configure the client CA:

```yaml
auth:
  methods: [mtls]
  mtls:
    client_ca: "certs/client-ca.pem"    # Trusted CA certificate (PEM)
    identity: cn                         # How to map cert → username
    default_role: "service"              # Default role for mTLS clients
```

### Identity Mapping Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| `cn` | Certificate CN becomes the username | CN=`service-a` → username `service-a` |
| `san_email` | First SAN email becomes the username | SAN=`bot@acme.com` → username `bot@acme.com` |
| `mapping` | Explicit CN-to-username mapping from config | See below |

#### Custom Mapping

```yaml
auth:
  methods: [mtls]
  mtls:
    client_ca: "certs/partner-ca.pem"
    identity: mapping
    default_role: "partner"
    mapping:
      "partner-a.example.com": "partner-a"
      "partner-b.example.com": "partner-b"
      "*.internal.example.com": "internal-service"
```

## Server Configuration

Enable client certificate verification in `yeti-config.yaml`:

```yaml
tls:
  domain: "api.example.com"
  autoGenerate: true
  clientAuth: optional    # none | optional | required
  clientCaDir: "certs/clients"   # Directory of trusted client CA .pem files
```

| Mode | Behavior |
|------|----------|
| `none` | No client cert verification (default) |
| `optional` | Accept client certs if offered, don't require them |
| `required` | Reject connections without a valid client certificate |

Use `optional` to support both mTLS and other auth methods on the same port. Use `required` for zero-trust environments where every client must present a certificate.

## Generating Certificates

### Create a Client CA

```bash
# Using mkcert (development)
mkcert -install
mkcert -client -cert-file client-ca.pem -key-file client-ca-key.pem "My App Client CA"

# Using openssl (production)
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
  -keyout client-ca-key.pem -out client-ca.pem -days 365 -nodes \
  -subj "/CN=My App Client CA"
```

### Issue a Client Certificate

```bash
# Generate client key
openssl ecparam -genkey -name prime256v1 -out client-key.pem

# Generate CSR
openssl req -new -key client-key.pem -out client.csr -subj "/CN=service-a"

# Sign with the CA
openssl x509 -req -in client.csr -CA client-ca.pem -CAkey client-ca-key.pem \
  -CAcreateserial -out client.pem -days 90
```

### Place the CA Certificate

```bash
# Copy the CA cert (not the key!) to your app's certs directory
cp client-ca.pem ~/yeti/applications/my-app/certs/client-ca.pem
```

## Making Requests

```bash
# curl with client certificate
curl -sk --cert client.pem --key client-key.pem \
  https://localhost:443/my-app/MyTable

# Verify authentication
curl -sk --cert client.pem --key client-key.pem \
  https://localhost:443/yeti-auth/auth
# → {"authenticated":true,"method":"mtls","username":"service-a"}
```

## Combining with Other Auth Methods

mTLS coexists with Basic, JWT, and OAuth. The auth pipeline tries each provider in priority order -- mTLS is checked first because identity is established at the transport layer:

```yaml
auth:
  methods: [mtls, jwt, basic]
  mtls:
    client_ca: "certs/client-ca.pem"
    identity: cn
    default_role: "service"
  jwt:
    secret: "${JWT_SECRET}"
```

| Priority | Method | Check |
|----------|--------|-------|
| 1 (highest) | mTLS | Client certificate in TLS handshake |
| 2 | JWT | `Authorization: Bearer` header |
| 3 | Basic | `Authorization: Basic` header |
| 4 | OAuth | Session cookie |

If a client presents both a certificate and a Bearer token, the mTLS identity wins.

## Use Cases

- **Service-to-service**: Microservices authenticate without shared secrets
- **IoT devices**: Each device gets its own certificate
- **CI/CD agents**: Build systems authenticate via cert, no token rotation
- **MQTT clients**: MQTTS connections use the same client CA for authentication
- **Partner APIs**: Issue certs to partners, revoke by removing their CA

## Certificate Revocation

Remove a client CA from the trust store to revoke all certificates signed by it:

```bash
rm ~/yeti/applications/my-app/certs/client-ca.pem
# Restart the app or wait for hot-reload
```

For individual certificate revocation, maintain a revocation list in a `RevokedCert` table and check certificate serial numbers in the `MtlsAuthProvider`.

## Security Notes

- The client CA private key should never be on the server — only the CA certificate (public key) is needed for verification
- Use short-lived client certificates (30-90 days) and automate renewal
- mTLS provides mutual authentication — the server verifies the client AND the client verifies the server
- `clientAuth: required` prevents any unauthenticated connections, including health checks from load balancers — use `optional` if external health checks don't present certificates

## See Also

- [Authentication Overview](overview.md)
- [Basic Authentication](basic.md) - Password-based auth
- [JWT Authentication](jwt.md) - Token-based auth
- [OAuth Integration](oauth.md) - Third-party login
- [Roles & Permissions](rbac.md) - Configuring access
- [TLS & HTTPS](../reference/tls.md) - Server TLS configuration
