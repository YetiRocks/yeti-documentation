# TLS & HTTPS

Yeti serves HTTPS on port 9996 using Rustls with the ring cryptography provider - no OpenSSL dependency.

## Configuration

```yaml
tls:
  autoGenerate: false
  privateKey: null
  certificate: null
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tls.autoGenerate` | boolean | `false` | Auto-generate self-signed certificates on startup |
| `tls.privateKey` | string | `null` | Path to PEM-encoded private key |
| `tls.certificate` | string | `null` | Path to PEM-encoded certificate (or chain) |

## Auto-Generated Certificates

For development:

```yaml
tls:
  autoGenerate: true
```

Creates certificates at `$rootDirectory/certs/localhost/`, valid for `localhost` and `127.0.0.1`.

## Manual Certificates

```yaml
tls:
  privateKey: /etc/ssl/private/yeti.key
  certificate: /etc/ssl/certs/yeti.crt
```

Requirements: PEM format, RSA (2048+) or ECDSA (P-256/P-384), no password on private key. The certificate file can contain a full chain.

### Let's Encrypt

```bash
sudo certbot certonly --standalone -d yeti.example.com
```

### mkcert (Local Development)

```bash
brew install mkcert && mkcert -install
mkcert localhost 127.0.0.1
```

## Development Workflow

Self-signed certificates require `-k` with curl:

```bash
curl -sk https://localhost:9996/my-app/TableName
```

## Operations API (No TLS)

The Operations API on port 9995 runs plain HTTP. Do not expose it to the public internet.

```bash
curl http://localhost:9995/health
```

## Supported Protocols

- TLS 1.2 and TLS 1.3 (preferred)
- Cipher suites: `TLS_AES_256_GCM_SHA384`, `TLS_AES_128_GCM_SHA256`, `TLS_CHACHA20_POLY1305_SHA256`

## See Also

- [Server Configuration](server-config.md) - Complete config reference
- [Environment Variables](environment-variables.md) - Environment setup
- [CLI Arguments](cli.md) - Command-line options
