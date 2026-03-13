# Environment Variables

## Core Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `YETI_HOME` | Settings directory containing `settings.toml` | `~/.yeti` |
| `YETI_ROOT_DIR` | Root directory for all Yeti data | `~/yeti` |
| `ROOT_DIRECTORY` | Alias for `YETI_ROOT_DIR` | `~/yeti` |
| `SETTINGS_PATH` | Path to `yeti-config.yaml` | `$ROOT_DIRECTORY/yeti-config.yaml` |
| `APPLICATION_PORT` | Override `http.port` | `9996` |
| `LOG_LEVEL` | Override `logging.level` | `"info"` |
| `ENVIRONMENT` | Override `environment` | `"development"` |

The `--dir` CLI argument overrides both `ROOT_DIRECTORY` and `YETI_ROOT_DIR`.

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

## Variable Substitution

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

Variables can also be set in `yeti-config.yaml` under the `env:` key:

```yaml
env:
  JWT_SECRET_KEY: "my-secret"
  GOOGLE_CLIENT_ID: "123456.apps.googleusercontent.com"
```

Real environment variables take precedence over values in the `env:` section.

## Security Notes

- Never commit secrets to version control.
- Use `${VAR:-}` substitution in config files to reference secrets from the environment.
- Use the `env:` section in yeti-config.yaml for non-sensitive defaults.

## See Also

- [Server Configuration](server-config.md) - Config file reference
- [CLI Arguments](cli.md) - Command-line arguments
- [TLS & HTTPS](tls.md) - Certificate configuration
