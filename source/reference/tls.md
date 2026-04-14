# TLS & HTTPS

HTTPS on port 9996 via Rustls with the ring provider. No OpenSSL dependency.

## Configuration

```yaml
tls:
  autoGenerate: false
  privateKey: null
  certificate: null
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.autoGenerate` | boolean | `false` | Auto-generate self-signed certs on startup |
| `tls.privateKey` | string | `null` | PEM private key path |
| `tls.certificate` | string | `null` | PEM certificate (or chain) path |

## Auto-Generated Certificates

```yaml
tls:
  autoGenerate: true
```

Creates certificates at `$rootDirectory/certs/localhost/`, valid for `localhost` and `127.0.0.1`.

## mkcert (Recommended for Development)

Browser-trusted local development certificates via [mkcert](https://github.com/FiloSottile/mkcert):

```bash
# Install mkcert
brew install mkcert

# Install the local CA into your system trust store (one-time setup)
mkcert -install

# Generate certificates for localhost
cd ~/yeti/certs/localhost
mkcert localhost 127.0.0.1
```

Creates `localhost+1.pem` (certificate) and `localhost+1-key.pem` (private key):

```yaml
tls:
  certificate: certs/localhost/localhost+1.pem
  privateKey: certs/localhost/localhost+1-key.pem
```

Paths resolve relative to the root directory. With mkcert, browsers trust the certificate without warnings.

## Manual Certificates

```yaml
tls:
  privateKey: /etc/ssl/private/yeti.key
  certificate: /etc/ssl/certs/yeti.crt
```

PEM format, RSA (2048+) or ECDSA (P-256/P-384), no password on private key. Certificate file can contain a full chain.

### Let's Encrypt

```bash
sudo certbot certonly --standalone -d yeti.example.com
```

## Development Workflow

Self-signed certificates require `-k` with curl:

```bash
curl -sk https://localhost:9996/my-app/TableName
```

With mkcert certificates, curl works without `-k`:

```bash
curl -s https://localhost:9996/my-app/TableName
```

## Supported Protocols

- TLS 1.2 and TLS 1.3 (preferred)
- Cipher suites: `TLS_AES_256_GCM_SHA384`, `TLS_AES_128_GCM_SHA256`, `TLS_CHACHA20_POLY1305_SHA256`

## See Also

- [Server Configuration](server-config.md) - Complete config reference
- [Environment Variables](environment-variables.md) - Environment setup
- [CLI Arguments](cli.md) - Command-line options
