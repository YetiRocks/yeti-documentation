# CLI Reference

## Usage

```bash
yeti [COMMAND] [OPTIONS]
```

Running `yeti` with no command will launch the install wizard if Yeti is not yet set up, or display a status screen if already installed.

## Commands

| Command | Description |
|---------|-------------|
| `yeti` | Status screen (installed) or install wizard (not installed) |
| `yeti start [-f]` | Start the server (background by default, `-f` for foreground) |
| `yeti stop` | Stop the running background server |
| `yeti restart [-f]` | Stop and restart the server |
| `yeti install` | Run or re-run the setup wizard |
| `yeti update` | Self-update to the latest binary |
| `yeti logs` | Tail the server log |
| `yeti help` | Print help message |

## Options

| Option | Description |
|--------|-------------|
| `-f`, `--foreground` | Run in foreground (default: background) |
| `-V`, `--version` | Print version |
| `-h`, `--help` | Print help |
| `--buildonly` | Compile plugins only, then exit |
| `--apps <a,b,c>` | Only load specified applications (comma-separated) |
| `--port <PORT>` | HTTP port (default: 9996) |
| `--dir <PATH>` | Root directory (default: ~/yeti) |

### Install Options

| Option | Description |
|--------|-------------|
| `--admin-user <USER>` | Admin username (default: YETI_ADMIN) |
| `--admin-password <PW>` | Admin password (required for headless install) |
| `--agree-to-terms` | Accept terms of use (required for headless install) |

## Examples

```bash
# Start in foreground with specific apps
yeti start -f --apps yeti-auth,my-app,yeti-telemetry

# Start on a custom port
yeti start --port 8443

# Compile plugins without starting the server
yeti --buildonly

# Headless install (no interactive wizard)
yeti install --admin-password "secret" --agree-to-terms --dir /opt/yeti

# Check version
yeti --version
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `YETI_HOME` | Override settings directory (default: ~/.yeti) |
| `APPLICATION_PORT` | Override HTTP port |
| `LOG_LEVEL` | Override log level (default: info) |

## Startup Sequence

1. Resolve root directory (CLI `--dir` > env var > settings.toml default)
2. Read `yeti-config.yaml`
3. Discover applications in `$rootDirectory/applications/`
4. Filter by `--apps` if specified
5. Compile application plugins (~2 min per plugin on first run, ~10 seconds cached)
6. Load plugins and register resources
7. Start HTTPS server on configured port (default 9996)

## Plugin Cache

Clear the plugin cache when builds are stale:

```bash
rm -rf ~/yeti/cache/builds/target/
```

Clear copied source files too (required when fixing plugin errors):

```bash
rm -rf ~/yeti/cache/builds/*/src/
```

## See Also

- [Server Configuration](server-config.md) - Full `yeti-config.yaml` reference
- [Environment Variables](environment-variables.md) - Environment-based configuration
- [Application Configuration](app-config.md) - Per-app config files
