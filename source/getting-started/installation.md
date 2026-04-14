# Installation

Single binary with a built-in setup wizard. No package managers, containers, or external dependencies.

## Download

Download for your platform:

```bash
# macOS (Apple Silicon)
curl -Lo yeti https://yeti-releases.us-east-1.linodeobjects.com/latest/yeti-darwin-arm64
chmod +x yeti

# macOS (Intel)
curl -Lo yeti https://yeti-releases.us-east-1.linodeobjects.com/latest/yeti-darwin-x86_64
chmod +x yeti

# Linux (x64)
curl -Lo yeti https://yeti-releases.us-east-1.linodeobjects.com/latest/yeti-linux-x86_64
chmod +x yeti

# Linux (ARM64)
curl -Lo yeti https://yeti-releases.us-east-1.linodeobjects.com/latest/yeti-linux-arm64
chmod +x yeti
```

Move the binary somewhere on your PATH (e.g., `/usr/local/bin/`) or run it from the current directory.

## One-Line Install

```bash
yeti
```

Launches the interactive setup wizard on first run, or starts the server if already installed.

## Interactive Installer

The installer runs as a terminal UI with three screens.

### 1. Welcome

Press the **Install Yeti** button to continue.

### 2. Configure

Scrollable form. Defaults shown in parentheses.

| Field | Default | Description |
|-------|---------|-------------|
| ROOT DIRECTORY | `~/yeti` | Where Yeti stores applications, data, and configuration |
| HOSTNAME | `localhost` | Server hostname for TLS certificate generation |
| PORT | `9996` | HTTPS listen port (`interfaces.port` in yeti-config.yaml) |
| ENVIRONMENT | `development` | Toggle with Space between `development` and `production` |
| ENABLE LOCAL STUDIO | `yes` | Install the Yeti Studio web interface |
| INCLUDE BASIC DEMO APP | `yes` | Install a sample application to explore |
| INCLUDE DEFAULT VECTOR MODEL | `yes` | Download the default embedding model for vector search |
| ADMIN USER | `YETI_ADMIN` | Username for the initial administrator account |
| ADMIN PASSWORD | *(type and press Enter)* | Password for the admin account |
| ACCEPT TERMS AND CONDITIONS | `yes` | Press ESC to read the full terms before accepting |

Navigate between fields with arrow keys. Press Enter to confirm and proceed to installation.

### 3. Progress

A live log stream shows each step. When the server is ready, press **Open Yeti Studio** to launch Studio in your browser.

## Headless Install

For scripted installations:

```bash
yeti install --admin-password <PASSWORD> --agree-to-terms
```

Optional flags:

```bash
yeti install \
  --admin-password <PASSWORD> \
  --agree-to-terms \
  --dir ~/yeti \
  --hostname localhost \
  --port 9996 \
  --environment development
```

## What Gets Installed

Installation creates:

```
~/yeti/
  yeti-config.yaml       # Server configuration
  applications/          # Your applications live here
  data/                  # RocksDB storage
  cache/                 # Plugin compilation cache
  certs/                 # TLS certificates (auto-generated)
  logs/                  # Server and telemetry logs
  models/                # Vector embedding models
  keys/                  # API keys and secrets
```

Nothing is installed outside this directory. Uninstall with `rm -rf ~/yeti`.

## After Install

Yeti starts automatically. Studio is at:

```
https://localhost:9996/studio/
```

On subsequent runs, start the server from the root directory:

```bash
cd ~/yeti && yeti
```

## System Requirements

| Platform | Architectures |
|----------|--------------|
| macOS | Apple Silicon, Intel |
| Linux | x64, ARM64 |
| Windows | x64 |

No external dependencies. Yeti embeds its storage engine, TLS stack, and plugin compiler. A Rust toolchain is required only for custom resources.

## Next Steps

- [Quickstart](quickstart.md) -- Build a REST API in 5 minutes
- [Your First Application](first-application.md) -- A complete app with custom resources and seed data
