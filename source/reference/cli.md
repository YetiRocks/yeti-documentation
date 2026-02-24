# CLI Reference

## Usage

```bash
yeti [COMMAND] [OPTIONS]
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize a new runtime directory with defaults, then start the server |
| `start` | Start the server |
| `stop` | Stop the running server |
| `restart` | Stop and restart the server |

## Options

### --root-dir

Override the root directory. Takes precedence over `ROOT_DIRECTORY` and `YETI_ROOT_DIR` environment variables and the `rootDirectory` config setting.

```bash
yeti start --root-dir /opt/yeti
```

The root directory must contain `yeti-config.yaml` and `applications/`. The `data/` and `certs/` directories are created automatically.

### --apps

Filter which applications to load. Comma-separated list of app IDs.

```bash
yeti start --apps yeti-auth,my-app,yeti-telemetry
```

Without `--apps`, all applications with `enabled: true` are loaded.

## Startup Sequence

1. Resolve root directory (CLI > env var > config default)
2. Read `yeti-config.yaml`
3. Discover applications in `$rootDirectory/applications/`
4. Filter by `--apps` if specified
5. Compile application plugins (~2 min per plugin on first run, ~10 seconds cached)
6. Load plugins and register resources
7. Start HTTPS server and Operations API

## Plugin Cache

Clear the plugin cache when builds are stale:

```bash
rm -rf ~/yeti/cache/builds/*/target/
```

Clear copied source files too (required when fixing plugin errors):

```bash
rm -rf ~/yeti/cache/builds/*/src/
```

## See Also

- [Server Configuration](server-config.md) - Full `yeti-config.yaml` reference
- [Environment Variables](environment-variables.md) - Environment-based configuration
- [Application Configuration](app-config.md) - Per-app config files
