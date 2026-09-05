"""
SENTINEL AI — AUTO CHECKER AGENT
Checks the entire project for common errors:
- JS function definitions vs calls
- HTML element IDs vs JS references
- API endpoints vs frontend fetch calls
- Python imports validity
- File integrity
Run: python sentinel_checker.py
"""

import os
import re
import sys

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

errors = []
warnings = []
passed = []

def check(name, condition, error_msg):
    if condition:
        passed.append(name)
        print(f"{GREEN}✅ PASS{RESET} — {name}")
    else:
        errors.append(f"{name}: {error_msg}")
        print(f"{RED}❌ FAIL{RESET} — {name} — {error_msg}")

def warn(name, msg):
    warnings.append(f"{name}: {msg}")
    print(f"{YELLOW}⚠️  WARN{RESET} — {name} — {msg}")

print(f"\n{CYAN}{'='*60}")
print("SENTINEL AI — AUTO CHECKER AGENT")
print(f"{'='*60}{RESET}\n")

# ──────────────────────────────────────────────
# 1. FILE EXISTENCE CHECK
# ──────────────────────────────────────────────
print(f"{CYAN}--- 1. FILE INTEGRITY ---{RESET}")

required_files = [
    "frontend/index.html",
    "frontend/style.css",
    "frontend/app.js",
    "api/main.py",
    "api/routes/news.py",
    "api/routes/country.py",
    "tools/wikipedia_tool.py",
    "tools/leader_tracker.py",
    ".env",
]

for f in required_files:
    check(f"File exists: {f}", os.path.exists(f), "FILE MISSING!")

# ──────────────────────────────────────────────
# 2. READ FILES
# ──────────────────────────────────────────────
def read(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

html = read("frontend/index.html")
js = read("frontend/app.js")
css = read("frontend/style.css")
country_py = read("api/routes/country.py")
main_py = read("api/main.py")
env = read(".env")

# ──────────────────────────────────────────────
# 3. JS SYNTAX BASIC CHECKS
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 2. JAVASCRIPT CHECKS ---{RESET}")

# Bracket balance
open_braces = js.count("{")
close_braces = js.count("}")
check("JS braces balanced", open_braces == close_braces,
      f"{{ count: {open_braces}, }} count: {close_braces}")

open_parens = js.count("(")
close_parens = js.count(")")
check("JS parentheses balanced", open_parens == close_parens,
      f"( count: {open_parens}, ) count: {close_parens}")

# Duplicate function definitions
func_defs = re.findall(r"function\s+(\w+)\s*\(", js)
dupes = set([f for f in func_defs if func_defs.count(f) > 1])
check("No duplicate JS functions", len(dupes) == 0,
      f"Duplicates: {dupes}")

# ──────────────────────────────────────────────
# 4. HTML ID vs JS getElementById CHECK
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 3. HTML ↔ JS ID MATCHING ---{RESET}")

html_ids = set(re.findall(r'id="([^"]+)"', html))
# ids the JS creates itself (modals, detail panes) count as present
html_ids |= set(re.findall(r'id="([^"]+)"', js))
html_ids |= set(re.findall(r'\.id\s*=\s*["\']([^"\']+)["\']', js))
js_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', js))

missing_ids = js_ids - html_ids
check("All JS getElementById IDs exist in HTML",
      len(missing_ids) == 0,
      f"JS references missing HTML IDs: {missing_ids}")

# data-screen vs screen sections
data_screens = set(re.findall(r'data-screen="([^"]+)"', html))
screen_sections = set(re.findall(r'id="screen-([^"]+)"', html))
missing_screens = data_screens - screen_sections
check("All nav buttons have screen sections",
      len(missing_screens) == 0,
      f"Nav buttons without screens: {missing_screens}")

# ──────────────────────────────────────────────
# 5. API ENDPOINT vs FRONTEND FETCH CHECK
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 4. API ↔ FRONTEND MATCHING ---{RESET}")

# Endpoints defined in backend
backend_endpoints = set(re.findall(
    r'@router\.(?:get|post)\("(/[^"]*)"', country_py))
news_py = read("api/routes/news.py")
backend_endpoints |= set(re.findall(
    r'@router\.(?:get|post)\("(/[^"]*)"', news_py))

# Fetch calls in frontend (extract path after API_BASE)
frontend_calls = set(re.findall(
    r'API_BASE\}?/([a-z\-]+)', js))

print(f"   Backend endpoints: {sorted(backend_endpoints)}")
print(f"   Frontend calls: {sorted(frontend_calls)}")

for call in frontend_calls:
    found = any(call in ep for ep in backend_endpoints)
    check(f"Frontend call '/{call}' has backend endpoint",
          found, "NO MATCHING BACKEND ENDPOINT!")

# ──────────────────────────────────────────────
# 6. PYTHON IMPORT CHECKS
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 5. PYTHON IMPORT CHECKS ---{RESET}")

# Check tool imports referenced in country.py exist
tool_imports = re.findall(r"from tools\.(\w+) import (\w+)", country_py)
for module, func in tool_imports:
    tool_file = f"tools/{module}.py"
    if os.path.exists(tool_file):
        tool_content = read(tool_file)
        has_func = f"def {func}" in tool_content
        check(f"tools/{module}.py has {func}()",
              has_func, f"Function '{func}' NOT FOUND in {module}.py!")
    else:
        check(f"tools/{module}.py exists", False, "FILE MISSING!")

# .env is loaded once, centrally, in config.py
check("config.py loads dotenv for API keys",
      "load_dotenv" in read("config.py"),
      "Missing load_dotenv in config.py — API keys won't load!")
check("No direct OpenRouter calls outside tools/llm.py",
      not any("openrouter.ai" in read(os.path.join(d, f))
              for d in ("tools", "api/routes", "agents") if os.path.isdir(d)
              for f in os.listdir(d) if f.endswith(".py") and f != "llm.py"),
      "Some module bypasses tools/llm.py")

# ──────────────────────────────────────────────
# 7. ENV CHECK
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 6. ENVIRONMENT CHECKS ---{RESET}")

check(".env has OPENROUTER_API_KEY",
      "OPENROUTER_API_KEY" in env, "KEY MISSING!")
check(".env has TAVILY_API_KEY",
      "TAVILY_API_KEY" in env, "KEY MISSING!")

# ──────────────────────────────────────────────
# 8. CDN CHECK (Edge Tracking Prevention)
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 7. CDN CHECKS ---{RESET}")

if "unpkg.com" in html:
    warn("CDN", "unpkg.com blocked by Edge Tracking Prevention! Use cdnjs.cloudflare.com")
else:
    check("Using Edge-safe CDN", "cdnjs.cloudflare.com" in html or "leaflet" not in html.lower(),
          "Leaflet CDN issue")

# ──────────────────────────────────────────────
# 9. LIVE API CHECK (if backend running)
# ──────────────────────────────────────────────
print(f"\n{CYAN}--- 8. LIVE BACKEND CHECK ---{RESET}")

try:
    import requests
    r = requests.get("http://127.0.0.1:8000/api/v1/health", timeout=3)
    check("FastAPI backend is running", r.status_code == 200,
          f"Status: {r.status_code}")

    # Test country endpoint
    r2 = requests.get("http://127.0.0.1:8000/api/v1/country/Russia", timeout=30)
    if r2.status_code == 200:
        data = r2.json()
        has_data = data.get("army_strength") not in [None, "N/A", "Officially Not Available"]
        check("Country endpoint returns real data (Russia)",
              has_data, f"army_strength = {data.get('army_strength')}")
    else:
        check("Country endpoint works", False, f"Status: {r2.status_code}")
except Exception as e:
    warn("Backend", f"Not running or unreachable — start with uvicorn! ({str(e)[:50]})")

# ──────────────────────────────────────────────
# FINAL REPORT
# ──────────────────────────────────────────────
print(f"\n{CYAN}{'='*60}")
print("FINAL REPORT")
print(f"{'='*60}{RESET}")
print(f"{GREEN}✅ Passed: {len(passed)}{RESET}")
print(f"{YELLOW}⚠️  Warnings: {len(warnings)}{RESET}")
print(f"{RED}❌ Errors: {len(errors)}{RESET}")

if errors:
    print(f"\n{RED}ERRORS TO FIX:{RESET}")
    for e in errors:
        print(f"  ❌ {e}")

if warnings:
    print(f"\n{YELLOW}WARNINGS:{RESET}")
    for w in warnings:
        print(f"  ⚠️ {w}")

if not errors:
    print(f"\n{GREEN}🎉 ALL CHECKS PASSED — SENTINEL IS HEALTHY!{RESET}")

sys.exit(1 if errors else 0)