# Installation

## Quick Install

**macOS / Linux**

```bash
curl -fsSL https://yetirocks.com/install.sh | sh
```

**macOS (Homebrew)**

```bash
brew tap yetirocks/yeti && brew install yeti
```

**Windows (PowerShell)**

```powershell
irm https://yetirocks.com/install.ps1 | iex
```

Pre-built binaries are also available for direct download at [yetirocks.com/install](https://yetirocks.com/install).

## Initialize

```bash
yeti init
```

This creates `~/yeti/` with default configuration, certificates, and starter applications, then starts the server.

## Verify

```bash
curl -sk https://localhost:9996/health
```

## Next Steps

- [Quickstart](quickstart.md) - Build a REST API in 5 minutes
- [Your First Application](first-application.md) - Detailed tutorial
- [Core Concepts](../concepts/applications.md) - How Yeti works
