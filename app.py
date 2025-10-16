# app.py — Windows-friendly LFI challenge behavior
from flask import Flask, request, Response
import os
import posixpath
import urllib.parse

FLAG = "picoCTF{so_easy_this_is_4c004rcjj}"

app = Flask(__name__)

# place the flag next to the script for local testing (Windows-friendly)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FLAG_PATH = os.path.join(BASE_DIR, "flag.txt")
with open(FLAG_PATH, "w", encoding="utf-8") as f:
    f.write(FLAG)

@app.route("/")
def index():
    return """
    <h2>Simple File Viewer (Windows-ready)</h2>
    <form action="/view" method="get">
      file: <input name="file" />
      <input type="submit" value="View" />
    </form>
    <p>Examples (for testing):</p>
    <ul>
      <li><code>/view?file=flag.txt</code> (should be blocked)</li>
      <li><code>/view?file=....//app/flag.txt</code> (should work)</li>
      <li><code>/robots.txt</code></li>
    </ul>
    """

@app.route("/robots.txt")
def robots():
    txt = "User-agent: *\nDisallow: /flag.txt\n"
    return Response(txt, mimetype="text/plain")

def is_trivial_flag_request(raw: str) -> bool:
    """Return True for trivial/direct requests we want to block (flag.txt, /flag.txt, ./flag.txt)."""
    if not isinstance(raw, str):
        return False
    s = raw.strip().replace("\\", "").lstrip("/")
    s_lower = s.lower()
    # block exact "flag.txt" or simple variants beginning with ./ or / (we removed them)
    if s_lower == "flag.txt" or s_lower.startswith("flag.txt?"):
        return True
    # also block if they typed "./flag.txt", ".\\flag.txt", or "/flag.txt" (handled via lstrip above)
    if s_lower.startswith("./") and s_lower[2:] == "flag.txt":
        return True
    return False

def normalize_for_matching(raw: str) -> str:
    """
    Normalize the input to a simplified form to match traversal tricks.
    - percent-decodes
    - replaces backslashes with slashes
    - collapses repeated dots to detect patterns like '....//app/flag.txt'
    - collapses multiple slashes
    Returns a lowercase normalized string.
    """
    if not isinstance(raw, str):
        return ""
    # percent-decode first
    decoded = urllib.parse.unquote(raw)
    # unify slashes
    s = decoded.replace("\\", "/")
    # collapse multiple slashes
    while "//" in s:
        s = s.replace("//", "/")
    # collapse sequences of 4 or more dots to a standard pattern (many bypass tricks use '....//')
    # we convert any run of dots into exactly two dots where appropriate to reveal the underlying path
    # but keep it careful: replace runs of 4+ dots -> "../"
    import re
    s = re.sub(r"\.{4,}", "../", s)
    # also collapse ././ or similar patterns
    s = s.replace("/./", "/")
    return s.lower()

@app.route("/view")
def view():
    raw_path = request.args.get("file", "")

    # Block trivial direct attempts to read the flag by typing the filename
    if is_trivial_flag_request(raw_path):
        return "Access denied."

    # Weak/naive filter: block the literal "../" substring (keeps some challenge variants blocked),
    # but we will still accept certain bypass patterns that mention 'app/flag.txt' after normalization.
    if "../" in raw_path and "app/flag.txt" not in raw_path.lower():
        # if someone provided a plain ../ but not targeted at app/flag.txt, keep blocking
        return "Access denied."

    # Basic sanity
    if not isinstance(raw_path, str) or raw_path.strip() == "":
        return "Invalid file."

    # Normalize for pattern matching
    norm = normalize_for_matching(raw_path)

    # Special handling for common traversal-bypass patterns that target /app/flag.txt
    # We allow forms like:
    #   - "....//app/flag.txt"
    #   - "%2e%2e%2fapp%2fflag.txt" (decoded -> "../app/flag.txt")
    #   - "../app/flag.txt"
    #   - "/app/flag.txt"
    # On Windows these won't point to /app/flag.txt, so map them to the local FLAG_PATH.
    if "app/flag.txt" in norm or norm.endswith("/app/flag.txt") or norm.endswith("app/flag.txt"):
        # Serve the local flag file that we wrote next to the script
        try:
            with open(FLAG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
                return "<pre>{}</pre>".format(content.replace("<", "&lt;").replace(">", "&gt;"))
        except FileNotFoundError:
            return "File not found."
        except Exception as e:
            return f"Error: {e}"

    # Otherwise, attempt to resolve the path normally (Windows-aware)
    # We'll try a few candidate file paths similar to before
    base = "/"
    joined = posixpath.join(base, raw_path.lstrip("/"))
    normalized = posixpath.normpath(joined)

    try_paths = [normalized, os.path.join(BASE_DIR, raw_path.lstrip("/")), raw_path]

    for p in try_paths:
        try:
            # convert POSIX-style leading slash on Windows: remove leading '/' if it becomes '/C:/...'
            if os.name == "nt" and isinstance(p, str) and p.startswith("/") and len(p) > 2 and p[1].isalpha() and p[2] == ":":
                p = p.lstrip("/")

            # block direct basename 'flag.txt' if user somehow produced that in a candidate path
            if os.path.basename(p).lower() == "flag.txt":
                # if original raw_path was trivial, block it — we handled many already, but keep this check
                if raw_path.strip().replace("\\", "").lstrip("/").lower() == "flag.txt":
                    return "Access denied."

            if os.path.isfile(p):
                with open(p, "r", errors="ignore", encoding="utf-8") as f:
                    content = f.read(10000)
                    return "<pre>{}</pre>".format(content.replace("<", "&lt;").replace(">", "&gt;"))
        except Exception:
            continue

    return "File not found."

if __name__ == "__main__":
    # run on Windows: python app.py
    # Start from the directory containing app.py (so flag.txt is created there)
    app.run(host="0.0.0.0", port=5000)
