# Installation

## One-Line Install

macOS / Linux:

```bash
curl -fsSL https://yetirocks.com/install.sh | sh
```

Windows (PowerShell):

```powershell
irm https://yetirocks.com/install.ps1 | iex
```

Downloads the Yeti binary for your platform, verifies its checksum, installs it to your PATH, and launches the interactive setup wizard. Pin a version with `sh -s -- v0.5.0` or `$v="v0.5.0"` on Windows.

## Docker

```bash
docker run -d \
  --name yeti \
  -p 9996:9996 \
  -v yeti-data:/yeti \
  -e YETI_ADMIN_USER=admin \
  -e YETI_ADMIN_PASSWORD=changeme \
  -e YETI_AGREE_TO_TERMS=yes \
  ghcr.io/yetirocks/yeti:latest
```

| Variable | Default | Description |
|----------|---------|-------------|
| `YETI_HOSTNAME` | `localhost` | Server hostname for TLS certificate generation |
| `YETI_PORT` | `9996` | HTTPS listen port |
| `YETI_ENVIRONMENT` | `development` | `development` or `production` |
| `YETI_ENABLE_STUDIO` | `yes` | Install the Yeti Studio web interface |
| `YETI_INCLUDE_DEMO` | `yes` | Install a sample application to explore |
| `YETI_INCLUDE_VECTOR_MODEL` | `yes` | Download the default embedding model for vector search |
| `YETI_ADMIN_USER` | `admin` | Username for the initial administrator account |
| `YETI_ADMIN_PASSWORD` | *(required)* | Password for the admin account |
| `YETI_AGREE_TO_TERMS` | *(required)* | Must be `yes` to accept terms and conditions |

Studio is at `https://localhost:9996/studio/` once the container is running.

## System Requirements

| Platform | Architectures |
|----------|--------------|
| macOS | Apple Silicon, Intel |
| Linux | x64, ARM64 |
| Windows | x64 |

No external dependencies. A Rust toolchain is required only for custom resources.
