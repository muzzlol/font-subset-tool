# Font Subset Tool

We hate slow page loads, [FOIT](https://fonts.google.com/knowledge/glossary/foit) and [FOUT](https://fonts.google.com/knowledge/glossary/fout) over here.

Fonts on the web are often a major bottleneck for page load times, frequently adding 200-500KB+ per typeface when using the full set of characters - which isn't required for most websites. 
This tool dramatically reduces font file sizes (typically by 75-85%) by keeping only the characters you actually [need](#default-character-set), while preserving essential typography features like kerning and ligatures and allowing you to customize what is required with [config files](#configuration).


## Features

- **Smart subsetting**: Default English character set with common symbols
- **Configurable**: TOML config support for custom character sets
- **Web-optimized**: Converts to WOFF2 format by default
- **Batch processing**: Process entire directories of fonts
- **Safe operations**: Checks before overwriting, validates inputs
- **Multiple formats**: Supports OTF, TTF, WOFF, WOFF2 input formats

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
# Clone the repository
git clone https://github.com/muzzlol/font-subset-tool.git
cd font-subset-tool

# Install dependencies
uv sync
```

### Requirements

- Python 3.8+
- fonttools
- brotli

## Quick Start

```bash
# Process a single font file
uv run python subset_fonts.py -i MyFont-Regular.ttf -o ./output/

# Process all fonts in a directory
uv run python subset_fonts.py -i ./fonts/ -o ./output/ --dir

# Process with custom config
uv run python subset_fonts.py -i ./fonts/ -o ./output/ --dir --config my-config.toml
```

## Usage

### Basic Options

```
-i, --input INPUT         Input font file or directory path
-o, --output OUTPUT       Output directory for subset fonts
--dir                     Process all font files in input directory
--pattern PATTERN         File pattern to match (default: *.woff2)
--prefix PREFIX           Prefix to add to output filenames
-v, --verbose             Show verbose output
--config CONFIG           Path to TOML config file
--force                   Overwrite existing files
--dry-run                 Preview what would be processed
-h, --help                Show help message
```

### Examples

#### Process OTF fonts to web-ready WOFF2
```bash
uv run python subset_fonts.py \
  -i ~/Downloads/MyFontFamily/ \
  -o ./web-fonts/ \
  --dir \
  --pattern "*.otf" \
  -v
```

#### Use custom configuration
```bash
uv run python subset_fonts.py \
  -i ./fonts/ \
  -o ./output/ \
  --dir \
  --config font-subset-minimal.toml
```

#### Process recursively with prefix
```bash
uv run python subset_fonts.py \
  -i ./fonts/ \
  -o ./output/ \
  --dir \
  --pattern "**/*.ttf" \
  --prefix "web"
```

## Configuration

The tool uses sensible defaults optimized for English websites. You can override these with a TOML config file.

### Default Character Set

- A-Z, a-z, 0-9, basic punctuation
- Smart quotes (' ' " ")
- Dashes (– —)
- Common symbols (©, ®, ™)
- Arrows (← ↑ → ↓)
- Bullet points (•)
- Ellipsis (…)

### Custom Configuration

See `font-subset.example.toml` for a complete example with comments.

```toml
[subset]
unicodes = [
    "U+0020-007E",  # Basic ASCII
    "U+00A0-00FF",  # Latin-1 Supplement
]
layout_features = ["kern", "liga", "calt"]
flavor = "woff2"
output_extension = "woff2"
desubroutinize = true
```

### Preset Configs

- `font-subset.example.toml` - Documented default configuration
- `font-subset-minimal.toml` - Minimal ASCII-only (smaller files)

## Output

The tool generates:
- WOFF2 files (by default) optimized for web use
- Filenames with `-subset` suffix
- Typical size reduction: 75-85%


## License

MIT

## Credits

Built with [fonttools](https://github.com/fonttools/fonttools) - the industry-standard font manipulation library.

