# Environment Variables

## Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ROOT_DIRECTORY` | Root directory for all Yeti data | `~/yeti` |
| `YETI_ROOT_DIR` | Alias for `ROOT_DIRECTORY` (takes precedence if both set) | - |
| `SETTINGS_PATH` | Path to `yeti-config.yaml` | `$ROOT_DIRECTORY/yeti-config.yaml` |
| `APPLICATION_PORT` | Override `http.port` | `9996` |
| `OPERATIONS_PORT` | Override `operationsApi.port` | `9995` |
| `LOG_LEVEL` | Override `logging.level` | `"info"` |
| `ENVIRONMENT` | Override `environment` | `"development"` |

The `--root-dir` CLI argument overrides both `ROOT_DIRECTORY` and `YETI_ROOT_DIR`.

## Storage

| Variable | Description | Default |
|----------|-------------|---------|
| `STORAGE_MODE` | `"embedded"` or `"cluster"` | `"embedded"` |
| `CLUSTER_PD_ENDPOINTS` | Comma-separated PD endpoints | - |

## Authentication Secrets

### JWT

| Variable | Description | Default |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | `"development-secret-change-in-production"` |

### OAuth Providers

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 client secret |
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App client secret |
| `MICROSOFT_CLIENT_ID` | Microsoft Entra client ID |
| `MICROSOFT_CLIENT_SECRET` | Microsoft Entra client secret |
| `MICROSOFT_TENANT` | Microsoft Entra tenant ID (default: `"common"`) |

## AI Service Keys

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for content generation |
| `VOYAGE_API_KEY` | Voyage AI key for embedding generation |

## OpenTelemetry

| Variable | Description |
|----------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry collector endpoint |
| `OTEL_SERVICE_NAME` | Service name for OTLP export |

## Variable Substitution in Config Files

Application `config.yaml` files support `${VAR:-default}` syntax:

```yaml
custom:
  jwt:
    secret: "${JWT_SECRET:-development-secret-change-in-production}"
  oauth:
    github:
      client_id: "${GITHUB_CLIENT_ID:-}"
```

The `:-` separator provides a default value. An empty default (`${VAR:-}`) results in an empty string.

## Security Notes

- Never commit secrets to version control.
- Use `${VAR:-}` substitution in config files to reference secrets from the environment.
- The `get_configuration` operations API endpoint sanitizes secrets from its output.

## See Also

- [Server Configuration](server-config.md) - Config file reference
- [CLI Arguments](cli.md) - Command-line arguments
- [TLS & HTTPS](tls.md) - Certificate configuration
