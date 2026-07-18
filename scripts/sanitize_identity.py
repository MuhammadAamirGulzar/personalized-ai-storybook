#!/usr/bin/env python3
"""
Conservative sanitizer for repository documentation and config files.

This script replaces personal names, student IDs, and project origin markers
in documentation files only (markdown, tex, html, txt, json, etc.). It is
conservative by design and does not touch source code files like .py/.ts
or rename file-system paths.

Usage:
  python scripts/sanitize_identity.py --apply

Run without --apply to perform a dry run.
"""
import argparse
import re
from pathlib import Path

REPLACEMENTS = {
    # Primary authors / students
    r"(?i)\bMuhammad\s*Abdul\s*Wahab\b": "muhammadaamirgulzar",
    r"(?i)\bM\.?\s*Abdul\s*Wahab\b": "muhammadaamirgulzar",
    r"(?i)\bWahab\b": "muhammadaamirgulzar",
    r"(?i)\bWahab\s*Kiyani\b": "muhammadaamirgulzar",
    r"(?i)\bMuhammad\s*Abdul\s*Wahab\s*Kiyani\b": "muhammadaamirgulzar",

    r"(?i)\bSyed\s*Ahmed\s*Ali\s*Zaidi\b": "muhammadaamirgulzar",
    r"(?i)\bSyed\s*Ahmed\b": "muhammadaamirgulzar",
    r"(?i)\bAhmed\b": "muhammadaamirgulzar",

    r"(?i)\bMujahid\s*Abbas\b": "muhammadaamirgulzar",
    r"(?i)\bMujahid\b": "muhammadaamirgulzar",

    # Team / org / upstream references
    r"(?i)\bStorix\b": "muhammadaamirgulzar",
    r"(?i)\bglassesart14-alt\b": "muhammadaamirgulzar",

    # Student IDs and cohort tags
    r"(?i)\b22I-?\d{3,4}\b": "muhammadaamirgulzar",
    r"(?i)\b22i-?\d{3,4}\b": "muhammadaamirgulzar",
    r"(?i)22I-?X+": "muhammadaamirgulzar",

    # Project name normalization (docs only)
    r"(?i)\bMyAIStorybook\b": "personalized-ai-storybook",
}

DOC_EXTS = {'.md', '.rst', '.txt', '.yml', '.yaml', '.json', '.env', '.html', '.tex', '.ipynb'}


def replace_in_text(text: str):
    count = 0
    for pat, repl in REPLACEMENTS.items():
        new_text, n = re.subn(pat, repl, text)
        if n:
            text = new_text
            count += n
    return text, count


def sanitize_file(path: Path, apply: bool):
    try:
        text = path.read_text(encoding='utf8', errors='ignore')
    except Exception:
        return 0
    new_text, count = replace_in_text(text)
    if count:
        try:
            display = str(path.relative_to(Path.cwd()))
        except Exception:
            display = str(path)
        print(f"{display}: {count} replacements")
        if apply:
            path.write_text(new_text, encoding='utf8')
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--root', default='.')
    args = parser.parse_args()

    root = Path(args.root)
    files = list(root.rglob('*'))
    total = 0
    for f in files:
        if f.is_file() and f.suffix.lower() in DOC_EXTS:
            try:
                total += sanitize_file(f, args.apply)
            except Exception as e:
                print(f"Skipping {f}: {e}")

    print(f"Done. Total replacements: {total}")


if __name__ == '__main__':
    main()
