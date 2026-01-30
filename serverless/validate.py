import argparse
import sys
import zipfile


def print_error(msg: str) -> None:
    print(f"\033[31m {msg}\033[0m")


def print_success(msg: str) -> None:
    print(f"\033[32m {msg}\033[0m")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate serverless package ZIP contents")
    parser.add_argument(
        "zip_path",
        nargs="?",
        default=".serverless/telegram-bot.zip",
        help="Path to ZIP file to validate",
    )
    parser.add_argument(
        "--handler",
        default="src/handler.py",
        help="Required handler path inside ZIP (default: src/handler.py)",
    )
    parser.add_argument(
        "--dependency-package-dir",
        default="telegram",
        help="Substring that must appear in at least one directory name",
    )

    args = parser.parse_args()

    try:
        with zipfile.ZipFile(args.zip_path) as z:
            entries = z.namelist()
    except FileNotFoundError:
        print_error(f"Zip not found: {args.zip_path}")
        return 1
    except zipfile.BadZipFile:
        print_error(f"Zip is invalid: {args.zip_path}")
        return 1

    if args.handler not in entries:
        print_error(f"Missing handler {args.handler}")
        return 1

    package_dirs = [
        e.split("/", 1)[0]
        for e in entries
        if "/" in e and args.dependency_package_dir.lower() in e.lower()
    ]

    if not package_dirs:
        print_error(f"No directory containing '{args.dependency_package_dir}' found")
        return 1

    print_success("No issues")
    return 0


if __name__ == "__main__":
    sys.exit(main())
