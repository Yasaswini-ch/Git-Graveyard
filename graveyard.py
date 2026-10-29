import subprocess, json, sys, urllib.request

REPO = sys.argv[1] if len(sys.argv) > 1 else "."
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 40

# llama-server:
# URL = "http://localhost:8080/v1/chat/completions"
# Ollama (uncomment):
URL = "http://localhost:11434/v1/chat/completions"
MODEL = sys.argv[3] if len(sys.argv) > 3 else "gemma3:4b"  # ignored by llama-server, required by Ollama
OUT = sys.argv[4] if len(sys.argv) > 4 else "graves.json"

def git(*args):
    return subprocess.run(["git", "-C", REPO, *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace").stdout

def deleted_files():
    out = git("log", "--diff-filter=D", "--name-only",
              "--format=@@%H|%an|%ad|%s", "--date=short")
    graves, cur = [], None
    for line in out.splitlines():
        if line.startswith("@@"):
            h, who, date, msg = line[2:].split("|", 3)
            cur = {"killer": who, "died": date, "message": msg}
        elif line.strip() and cur:
            graves.append({**cur, "path": line.strip()})
    return graves[:LIMIT]

def born(path):
    out = git("log", "--diff-filter=A", "--format=%ad", "--date=short", "--", path)
    lines = out.strip().splitlines()
    return lines[-1] if lines else "unknown"

def ask(prompt):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": 80,
    }).encode()
    req = urllib.request.Request(URL, body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["choices"][0]["message"]["content"].strip()

PROMPT = """Write a two-line epitaph for a deleted source file.
File: {path}
Born: {born}
Died: {died}
Killed by: {killer}, commit message "{message}"
Tone: dry, affectionate, slightly spooky. Under 25 words. No emojis. Output only the epitaph."""

graves = []
for g in deleted_files():
    g["born"] = born(g["path"])
    try:
        g["epitaph"] = ask(PROMPT.format(**g)).replace("\n", " ")
    except OSError as e:
        sys.exit(f"Could not reach the model at {URL}: {e}\nIs llama-server or Ollama running?")
    g["model"] = MODEL
    graves.append(g)
    print("buried", g["path"])

if not graves:
    print("No deleted files found. This repo is immortal.")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(graves, f, indent=1)
