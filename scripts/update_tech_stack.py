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

def fetch_languages():
    # Gunakan endpoint /user/repos jika token tersedia untuk mengambil repositori privat juga
    if github_token:
        print("Using GITHUB_TOKEN to fetch all owned repositories (including private)...")
        url = "https://api.github.com/user/repos?per_page=100&type=owner"
    else:
        print("No GITHUB_TOKEN. Fetching public repositories only...")
        url = f"https://api.github.com/users/{username}/repos?per_page=100"
        
    req = urllib.request.Request(url)
    if github_token:
        req.add_header("Authorization", f"token {github_token}")
    req.add_header("User-Agent", "antigravity-readme-updater")
    
    try:
        with urllib.request.urlopen(req) as response:
            repos = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching repos: {e}")
        return []
    
    languages = set()
    for repo in repos:
        if repo.get("fork"):
            continue
        repo_name = repo.get("name")
        print(f"Fetching languages for repository: {repo_name}...")
        lang_url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
        lang_req = urllib.request.Request(lang_url)
        if github_token:
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
    detected_langs = fetch_languages()
    print(f"Detected languages on GitHub: {detected_langs}")
    
    # Gabungkan keahlian manual dengan bahasa koding terdeteksi
    icons = set(SYSADMIN_TOOLS)
    for lang in detected_langs:
        mapped = LANGUAGE_MAP.get(lang)
        if mapped:
            icons.add(mapped)
            
    # Aturan khusus: Jika Laravel/PHP dideteksi, tambahkan laravel dan mysql
    if "php" in detected_langs:
        icons.add("laravel")
        icons.add("mysql")
            
    # Urutkan secara alfabetis agar rapi
    sorted_icons = sorted(list(icons))
    icons_str = ",".join(sorted_icons)
    print(f"Final Tech Stack Icons: {icons_str}")
    
    # Jalur berkas README
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        readme_path = "../README.md"
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    pattern = r"<!-- TECH-STACK-LIST:START -->.*?<!-- TECH-STACK-LIST:END -->"
    replacement = f'<!-- TECH-STACK-LIST:START -->\n<p align="center">\n  <a href="https://skillicons.dev">\n    <img src="https://skillicons.dev/icons?i={icons_str}&perline=8&theme=dark" alt="Fahmi\'s Tech Stack" />\n  </a>\n</p>\n<!-- TECH-STACK-LIST:END -->'
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully updated README.md with dynamic Tech Stack!")

if __name__ == "__main__":
    main()
