import os
import re
import urllib.request
import json

# Setup konfigurasi pengguna
username = "khairudinfahmi"
github_token = os.environ.get("GITHUB_TOKEN")

# Peta konversi nama bahasa resmi GitHub ke pengidentifikasi skillicons
LANGUAGE_MAP = {
    "python": "python",
    "powershell": "powershell",
    "shell": "bash",
    "php": "php",
    "javascript": "js",
    "typescript": "ts",
    "astro": "astro",
    "html": "html",
    "css": "css",
    "dockerfile": "docker",
    "mysql": "mysql",
    "nginx": "nginx",
}

# Perkakas wajib SysAdmin dan workspace (tidak terdeteksi otomatis sebagai bahasa kode)
SYSADMIN_TOOLS = [
    "linux",
    "windows",
    "docker",
    "nginx",
    "git",
    "github",
    "vscode",
]

def get_existing_icons(readme_content):
    # Cari list ikon yang sudah ada di README.md
    match = re.search(r"https://skillicons.dev/icons\?i=([a-z0-9,]+)", readme_content)
    if match:
        existing = match.group(1).split(",")
        print(f"Found existing icons in README: {existing}")
        return set(existing)
    return set()

def fetch_languages():
    # Tentukan endpoint API. Jika token adalah token bot GitHub Actions (berawalan ghs_),
    # kita hindari /user/repos karena akan menghasilkan 403 Forbidden.
    # Kita hanya gunakan /user/repos jika memiliki Personal Access Token (PAT) atau berjalan lokal.
    is_actions_token = github_token and github_token.startswith("ghs_")
    
    if github_token and not is_actions_token:
        print("Using personal GITHUB_TOKEN to fetch all owned repositories (including private)...")
        url = "https://api.github.com/user/repos?per_page=100&type=owner"
        use_auth = True
    else:
        print("Fetching public repositories only (avoiding Actions Token 403 restriction)...")
        url = f"https://api.github.com/users/{username}/repos?per_page=100"
        use_auth = False
        
    req = urllib.request.Request(url)
    if use_auth:
        req.add_header("Authorization", f"token {github_token}")
    req.add_header("User-Agent", "antigravity-readme-updater")
    
    try:
        with urllib.request.urlopen(req) as response:
            repos = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching repos: {e}")
        # Jika gagal dengan auth, coba fallback ke public API tanpa auth
        if use_auth:
            print("Attempting fallback to public repos without auth...")
            try:
                public_url = f"https://api.github.com/users/{username}/repos?per_page=100"
                req_fallback = urllib.request.Request(public_url)
                req_fallback.add_header("User-Agent", "antigravity-readme-updater")
                with urllib.request.urlopen(req_fallback) as response:
                    repos = json.loads(response.read().decode())
            except Exception as fe:
                print(f"Fallback failed: {fe}")
                return []
        else:
            return []
    
    languages = set()
    for repo in repos:
        if repo.get("fork"):
            continue
        repo_name = repo.get("name")
        print(f"Fetching languages for repository: {repo_name}...")
        lang_url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
        lang_req = urllib.request.Request(lang_url)
        # Gunakan auth header hanya jika use_auth aktif
        if use_auth:
            lang_req.add_header("Authorization", f"token {github_token}")
        lang_req.add_header("User-Agent", "antigravity-readme-updater")
        try:
            with urllib.request.urlopen(lang_req) as response:
                repo_langs = json.loads(response.read().decode())
                for lang in repo_langs.keys():
                    languages.add(lang.lower())
        except Exception as e:
            print(f"Error fetching languages for {repo_name}: {e}")
            
    return list(languages)

def main():
    # Baca file README.md
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        readme_path = "../README.md"
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Ambil ikon lama yang sudah terdaftar
    existing_icons = get_existing_icons(content)
    
    # Ambil bahasa baru dari API
    detected_langs = fetch_languages()
    print(f"Detected languages on GitHub: {detected_langs}")
    
    # Gabungkan keahlian lama, perkakas SysAdmin wajib, dan bahasa baru yang terdeteksi
    icons = set(SYSADMIN_TOOLS)
    icons.update(existing_icons)
    
    for lang in detected_langs:
        mapped = LANGUAGE_MAP.get(lang)
        if mapped:
            icons.add(mapped)
            
    # Aturan khusus: Jika Laravel/PHP dideteksi, tambahkan laravel dan mysql
    if "php" in detected_langs or "php" in icons:
        icons.add("laravel")
        icons.add("mysql")
            
    # Urutkan secara alfabetis agar rapi
    sorted_icons = sorted(list(icons))
    icons_str = ",".join(sorted_icons)
    print(f"Final Tech Stack Icons: {icons_str}")
    
    pattern = r"<!-- TECH-STACK-LIST:START -->.*?<!-- TECH-STACK-LIST:END -->"
    replacement = f'<!-- TECH-STACK-LIST:START -->\n<p align="center">\n  <a href="https://skillicons.dev">\n    <img src="https://skillicons.dev/icons?i={icons_str}&perline=8&theme=dark" alt="Fahmi\'s Tech Stack" />\n  </a>\n</p>\n<!-- TECH-STACK-LIST:END -->'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully updated README.md with dynamic Tech Stack!")

if __name__ == "__main__":
    main()
