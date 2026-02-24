<p align="center">
  <img src="https://cdn.prod.website-files.com/68e09cef90d613c94c3671c0/697e805a9246c7e090054706_logo_horizontal_grey.png" alt="Yeti" width="200" />
</p>

---

# Yeti Documentation

[![Yeti](https://img.shields.io/badge/Yeti-Application-blue)](https://yetirocks.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![mdBook](https://img.shields.io/badge/mdBook-Powered-orange)](https://rust-lang.github.io/mdBook/)

Self-hosted documentation site built with mdBook. Serves the complete Yeti platform documentation as a static site.

## Features

- **mdBook Format** - Markdown-based documentation
- **Full-Text Search** - Built-in search functionality
- **Syntax Highlighting** - Code blocks with language support
- **Custom Theme** - Yeti-branded styling
- **Auto-Build** - Programmatic build on startup
- **Static Serving** - Fast, cached delivery

## Installation

```bash
# Clone into your Yeti applications folder
cd ~/yeti/applications/local
git clone https://github.com/yetirocks/documentation.git

# Build the documentation
cd documentation
cargo run --bin build-docs

# Restart Yeti to load the application
# The documentation will be available at /documentation
```

## Usage

### View Documentation

Open your browser to:
```
https://localhost:9996/documentation/
```

### Build Documentation

```bash
# Using the build tool
cargo run --bin build-docs

# Or using mdbook directly
cd source
mdbook build
```

### Development Mode

```bash
# Watch for changes and rebuild
cd source
mdbook serve

# Opens at http://localhost:3000
```

## Writing Documentation

### Add a New Page

1. Create a markdown file in `source/`:
   ```bash
   echo "# New Topic" > source/new-topic.md
   ```

2. Add to `source/SUMMARY.md`:
   ```markdown
   - [New Topic](new-topic.md)
   ```

3. Rebuild:
   ```bash
   cargo run --bin build-docs
   ```

### Markdown Features

```markdown
# Heading 1
## Heading 2

**Bold** and *italic* text

- Bullet lists
- With items

1. Numbered lists
2. With items

`inline code`

\`\`\`rust
// Code blocks with syntax highlighting
fn main() {
    println!("Hello, Yeti!");
}
\`\`\`

> Blockquotes for notes

[Links](https://yetirocks.com)

| Tables | Work |
|--------|------|
| Too    | Yes  |
```

## Project Structure

```
documentation/
├── Cargo.toml           # Build dependencies
├── build.rs             # Programmatic build tool
├── config.yaml          # Yeti application config
├── source/              # mdBook source
│   ├── book.toml        # mdBook configuration
│   ├── SUMMARY.md       # Table of contents
│   ├── introduction.md  # Landing page
│   ├── getting-started/
│   ├── guides/
│   └── theme/           # Custom styling
└── web/                  # Built HTML output
    ├── index.html
    ├── searchindex.json
    └── ...
```

## Configuration

### book.toml

```toml
[book]
title = "Yeti Documentation"
authors = ["Yeti Team"]
language = "en"

[build]
build-dir = "../web"

[output.html]
theme = "theme"
default-theme = "light"
```

## Learn More

- [Yeti Documentation](https://yetirocks.com/docs)
- [mdBook Guide](https://rust-lang.github.io/mdBook/)
- [Contributing to Docs](https://yetirocks.com/docs/contributing)

---

Built with [Yeti](https://yetirocks.com) - The fast, declarative database platform.
