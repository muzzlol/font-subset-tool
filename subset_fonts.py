#!/usr/bin/env python3
"""
Font subsetting script for Latin-focused web use
Reduces font file sizes by keeping only essential characters for English websites
"""

import sys
import argparse
from pathlib import Path
import subprocess
import shutil

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover - fallback for older Python
    try:
        import tomli as tomllib  # type: ignore
    except ModuleNotFoundError:
        tomllib = None


DEFAULT_CONFIG = {
    "subset": {
        "unicodes": [
            "U+0020-007E",  # Basic ASCII (includes A-Z, a-z, 0-9, basic punctuation)
            "U+00A0",       # Non-breaking space
            "U+00A9",       # Copyright symbol
            "U+00AE",       # Registered trademark
            "U+2013-2014",  # En dash, Em dash
            "U+2018-2019",  # Smart single quotes
            "U+201C-201D",  # Smart double quotes
            "U+2026",       # Ellipsis
            "U+2122",       # Trademark symbol
            "U+2190-2193",  # Basic arrows
            "U+2022",       # Bullet point
            "U+00B7",       # Middle dot
            "U+2039-203A"   # Single angle quotes
        ],
        "layout_features": ["kern", "liga", "calt"],
        "flavor": "woff2",
        "output_extension": "woff2",
        "desubroutinize": True,
        "additional_args": []
    }
}


def _merge_config(base, override):
    merged = {**base}
    for key, value in override.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = _merge_config(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path):
    if not config_path:
        return _merge_config(DEFAULT_CONFIG, {})

    if tomllib is None:
        raise RuntimeError(
            "Reading TOML configs requires Python 3.11+ or installing tomli (pip install tomli)."
        )

    with open(config_path, "rb") as handle:
        loaded = tomllib.load(handle)

    return _merge_config(DEFAULT_CONFIG, loaded)

def subset_font(input_file, output_dir, prefix="", verbose=False, config=None, force=False):
    """
    Subset a single font file using the active configuration.
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"Skipping missing file: {input_path}")
        return False

    output_path.mkdir(parents=True, exist_ok=True)

    cfg = config or DEFAULT_CONFIG
    subset_cfg = cfg.get("subset", {})
    output_extension = subset_cfg.get("output_extension", "woff2")

    if prefix:
        output_filename = f"{prefix}-{input_path.stem}-subset.{output_extension}"
    else:
        output_filename = f"{input_path.stem}-subset.{output_extension}"
    
    output_file = output_path / output_filename
    
    unicode_ranges = ",".join(subset_cfg.get("unicodes", []))
    layout_features = ",".join(subset_cfg.get("layout_features", []))
    flavor = subset_cfg.get("flavor", "woff2")
    desubroutinize = subset_cfg.get("desubroutinize", True)
    additional_args = subset_cfg.get("additional_args", [])

    if not unicode_ranges:
        raise ValueError("Configuration must define at least one unicode range")
    
    cmd = [
        "pyftsubset",
        str(input_path),
        f"--output-file={output_file}",
        f"--flavor={flavor}",
        f"--layout-features={layout_features}",
        f"--unicodes={unicode_ranges}"
    ]

    if desubroutinize:
        cmd.append("--desubroutinize")

    cmd.extend(additional_args)
    
    if verbose:
        print(f"\nProcessing: {input_path.name}")
        print(f"Output: {output_file}")
    
    if output_file.exists() and not force:
        print(f"Skipping {input_path.name}: output already exists (use --force to overwrite)")
        return False

    if shutil.which("pyftsubset") is None:
        print("Error: pyftsubset not found. Please install fonttools (pip install fonttools brotli)")
        return False

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error processing {input_path.name}:")
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
            return False
        
        # Get file sizes for comparison
        original_size_bytes = input_path.stat().st_size
        new_size_bytes = output_file.stat().st_size

        original_size = original_size_bytes / 1024 if original_size_bytes else 0
        new_size = new_size_bytes / 1024 if new_size_bytes else 0

        if original_size_bytes == 0:
            reduction = 0
        else:
            reduction = ((original_size_bytes - new_size_bytes) / original_size_bytes) * 100
        
        print(f"Processed {input_path.name}")
        print(f"   Original: {original_size:.1f} KB -> Subset: {new_size:.1f} KB")
        print(f"   Reduction: {reduction:.1f}% ({(original_size - new_size):.1f} KB saved)")
        
        return True
        
    except FileNotFoundError:
        print("Error: pyftsubset not found. Please install fonttools:")
        print("   pip install fonttools brotli")
        return False
    except Exception as e:
        print(f"Error processing {input_path.name}: {str(e)}")
        return False

def process_directory(input_dir, output_dir, pattern="*.woff2", prefix="", verbose=False, config=None, force=False):
    """
    Process all font files in a directory
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist")
        return False
    
    # Find all matching font files
    font_files = list(input_path.rglob(pattern)) if pattern.startswith("**/") else list(input_path.glob(pattern))
    
    if not font_files:
        print(f"No files matching '{pattern}' found in {input_dir}")
        return False
    
    print(f"\nFound {len(font_files)} font files to process")
    print("=" * 50)
    
    success_count = 0
    for font_file in font_files:
        if subset_font(font_file, output_dir, prefix, verbose, config=config, force=force):
            success_count += 1
    
    print("=" * 50)
    print(f"\nCompleted: {success_count}/{len(font_files)} fonts processed successfully")
    
    return success_count == len(font_files)

def main():
    parser = argparse.ArgumentParser(
        description="Subset fonts for web use (English-focused character set)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single font file
  python subset_fonts.py -i ExampleFont-Bold.woff2 -o ./subset/

  # Process all woff2 files in a directory
  python subset_fonts.py -i ./fonts/ -o ./subset/ --dir

  # Process with custom prefix
  python subset_fonts.py -i ./fonts/ -o ./subset/ --dir --prefix "web"
  
  # Process TTF files instead of WOFF2
  python subset_fonts.py -i ./fonts/ -o ./subset/ --dir --pattern "*.ttf"
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input font file or directory path"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output directory for subset fonts"
    )
    
    parser.add_argument(
        "--dir",
        action="store_true",
        help="Process all font files in input directory"
    )
    
    parser.add_argument(
        "--pattern",
        default="*.woff2",
        help="File pattern to match when using --dir (default: *.woff2)"
    )
    
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix to add to output filenames"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    
    parser.add_argument(
        "--config",
        help="Path to a TOML config file to override defaults"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing subset files if present"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without calling pyftsubset"
    )

    args = parser.parse_args()
    
    try:
        import fontTools
    except ImportError:
        print("Error: fonttools is not installed")
        print("Please install it with: pip install fonttools brotli")
        sys.exit(1)
    
    try:
        config = load_config(args.config)
    except RuntimeError as err:
        print(f"Error loading config: {err}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Config file '{args.config}' not found")
        sys.exit(1)
    except tomllib.TOMLDecodeError as err:  # type: ignore[attr-defined]
        print(f"Error: Failed to parse config file '{args.config}': {err}")
        sys.exit(1)

    print("\nFont Subsetting Tool")
    print("Keeping only English characters + common symbols (override via TOML config)")
    
    if args.dir:
        if args.dry_run:
            print("Dry run: would process directory with current settings")
            print(f"Input: {args.input}")
            print(f"Output: {args.output}")
            print(f"Pattern: {args.pattern}")
            print(f"Prefix: {args.prefix or '(none)'}")
            print(f"Force overwrite: {'yes' if args.force else 'no'}")
            print(f"Config: {args.config or 'default built-in profile'}")
            sys.exit(0)

        success = process_directory(
            args.input,
            args.output,
            args.pattern,
            args.prefix,
            args.verbose,
            config=config,
            force=args.force
        )
    else:
        # Process single file
        if not Path(args.input).exists():
            print(f"Error: File '{args.input}' does not exist")
            sys.exit(1)
        
        if args.dry_run:
            print("Dry run: would process single file with current settings")
            print(f"Input: {args.input}")
            print(f"Output: {args.output}")
            print(f"Prefix: {args.prefix or '(none)'}")
            print(f"Force overwrite: {'yes' if args.force else 'no'}")
            print(f"Config: {args.config or 'default built-in profile'}")
            sys.exit(0)

        print(f"\nProcessing single file...")
        print("=" * 50)
        success = subset_font(
            args.input,
            args.output,
            args.prefix,
            args.verbose,
            config=config,
            force=args.force
        )
        print("=" * 50)
    
    if success:
        print(f"\nOutput saved to: {args.output}")
        print("\nTip: These subset fonts contain:")
        print("   - A-Z, a-z, 0-9, basic punctuation")
        print("   - Smart quotes, dashes, ellipsis")
        print("   - Common symbols (copyright, trademark, arrows)")
        print("   - Essential ligatures (fi, fl)")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
