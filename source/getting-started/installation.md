# Installation

Yeti ships as a single binary with a built-in setup wizard. No package managers, containers, or external dependencies required.

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

A scrollable form with the following fields. Defaults are shown in parentheses.

| Field | Default | Description |
|-------|---------|-------------|
| ROOT DIRECTORY | `~/yeti` | Where Yeti stores applications, data, and configuration |
| HOSTNAME | `localhost` | Server hostname for TLS certificate generation |
| PORT | `443` | HTTPS listen port |
| ENVIRONMENT | `development` | Toggle with Space between `development` and `production` |
| ENABLE LOCAL STUDIO | `yes` | Install the Yeti Studio web interface |
| INCLUDE BASIC DEMO APP | `yes` | Install a sample application to explore |
| INCLUDE DEFAULT VECTOR MODEL | `yes` | Download the default embedding model for vector search |
| ADMIN USER | `YETI_ADMIN` | Username for the initial administrator account |
| ADMIN PASSWORD | *(type and press Enter)* | Password for the admin account |
| ACCEPT TERMS AND CONDITIONS | `yes` | Press ESC to read the full terms before accepting |

Navigate between fields with arrow keys. Press Enter to confirm and proceed to installation.

### 3. Progress

A live log stream shows each installation step as it completes. When the server is ready, an **Open Yeti Studio** button appears. Press it to launch Studio in your default browser.

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
  --port 443 \
  --environment development
```

## What Gets Installed

Installation creates this structure:

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

No files are installed outside this directory. Uninstalling is `rm -rf ~/yeti`.

## After Install

Yeti starts automatically when installation completes. Studio is accessible at:

```
https://localhost/studio/
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

No external dependencies. Yeti embeds its own storage engine, TLS stack, and plugin compiler. A Rust toolchain is required only for applications with custom resources.

## Next Steps

- [Quickstart](quickstart.md) -- Build a REST API in 5 minutes
- [Your First Application](first-application.md) -- A complete app with custom resources and seed data
