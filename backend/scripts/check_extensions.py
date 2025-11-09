#!/usr/bin/env python3
"""
PostgreSQL Extensions Status Checker

Usage:
    python scripts/check_extensions.py
    python scripts/check_extensions.py --verbose
    python scripts/check_extensions.py --available

This script checks the status of required PostgreSQL extensions.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import engine
from app.core.extensions import (
    verify_extensions_with_report,
    get_all_available_extensions,
    get_extension_info,
    REQUIRED_EXTENSIONS,
    EXTENSION_DESCRIPTIONS
)


def check_status(verbose: bool = False):
    """Check and display extension installation status."""
    print("=" * 80)
    print("PostgreSQL Extensions Status Check")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            report = verify_extensions_with_report(conn)

            if 'error' in report:
                print(f"\nError checking extensions: {report['error']}")
                return 1

            print(f"\nRequired Extensions: {report['total_required']}")
            print(f"Installed: {len(report['installed'])}")
            print(f"Missing: {len(report['missing'])}")

            if report['all_installed']:
                print("\n✓ All required extensions are installed!")
            else:
                print("\n✗ Some extensions are missing!")

            if report['installed']:
                print("\n" + "=" * 80)
                print("INSTALLED EXTENSIONS")
                print("=" * 80)
                for ext_name in sorted(report['installed']):
                    version = report['versions'].get(ext_name, 'unknown')
                    description = EXTENSION_DESCRIPTIONS.get(ext_name, '')
                    print(f"\n✓ {ext_name} (v{version})")
                    print(f"  {description}")

                    if verbose:
                        info = get_extension_info(conn, ext_name)
                        if info:
                            print(f"  Schema: {info.get('schema', 'N/A')}")
                            print(f"  Relocatable: {info.get('relocatable', 'N/A')}")

            if report['missing']:
                print("\n" + "=" * 80)
                print("MISSING EXTENSIONS")
                print("=" * 80)
                for ext_name in sorted(report['missing']):
                    description = EXTENSION_DESCRIPTIONS.get(ext_name, '')
                    print(f"\n✗ {ext_name}")
                    print(f"  {description}")

            print("\n" + "=" * 80)

            return 0 if report['all_installed'] else 1

    except Exception as e:
        print(f"\nError: {e}")
        return 1


def list_available():
    """List all available extensions in PostgreSQL."""
    print("=" * 80)
    print("Available PostgreSQL Extensions")
    print("=" * 80)

    try:
        with engine.connect() as conn:
            extensions = get_all_available_extensions(conn)

            if not extensions:
                print("\nNo extensions found or error occurred.")
                return 1

            print(f"\nTotal available: {len(extensions)}")

            # Group extensions
            required_available = []
            other_available = []

            for name, version, comment in extensions:
                if name in REQUIRED_EXTENSIONS:
                    required_available.append((name, version, comment))
                else:
                    other_available.append((name, version, comment))

            if required_available:
                print("\n" + "=" * 80)
                print("REQUIRED EXTENSIONS (Available)")
                print("=" * 80)
                for name, version, comment in sorted(required_available):
                    print(f"\n{name} (v{version})")
                    if comment:
                        print(f"  {comment[:80]}")

            missing_required = REQUIRED_EXTENSIONS - {ext[0] for ext in extensions}
            if missing_required:
                print("\n" + "=" * 80)
                print("REQUIRED EXTENSIONS (NOT Available)")
                print("=" * 80)
                for name in sorted(missing_required):
                    print(f"\n✗ {name}")
                    print(f"  {EXTENSION_DESCRIPTIONS.get(name, '')}")

            print("\n" + "=" * 80)
            print(f"Other Extensions: {len(other_available)}")
            print("=" * 80)
            print("(Use --verbose to see all)")

            return 0

    except Exception as e:
        print(f"\nError: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check PostgreSQL extensions status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/check_extensions.py
  python scripts/check_extensions.py --verbose
  python scripts/check_extensions.py --available
        """
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed information'
    )
    parser.add_argument(
        '--available', '-a',
        action='store_true',
        help='List all available extensions'
    )

    args = parser.parse_args()

    if args.available:
        return list_available()
    else:
        return check_status(verbose=args.verbose)


if __name__ == "__main__":
    sys.exit(main())
