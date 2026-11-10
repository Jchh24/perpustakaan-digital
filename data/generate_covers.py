import os

os.makedirs("static/images", exist_ok=True)

covers = [
    ("default_cover.png", "Perpustakaan Digital", "#2563eb", "#1d4ed8"),
    ("default_cover.svg", "Perpustakaan Digital", "#2563eb", "#1d4ed8"),
    ("clean_code.jpg", "Clean Code", "#1e293b", "#0f172a"),
    ("design_patterns.jpg", "Design Patterns", "#0f766e", "#115e59"),
    ("laskar_pelangi.jpg", "Laskar Pelangi", "#b45309", "#92400e"),
    ("bumi_manusia.jpg", "Bumi Manusia", "#991b1b", "#7f1d1d"),
    ("brief_history.jpg", "Brief History of Time", "#4338ca", "#3730a3"),
    ("lean_startup.jpg", "The Lean Startup", "#0d9488", "#0f766e"),
]

template = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="560" viewBox="0 0 400 560">
  <defs>
    <linearGradient id="grad_{idx}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c1};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c2};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="400" height="560" fill="url(#grad_{idx})" rx="12" />
  <rect x="20" y="20" width="360" height="520" fill="none" stroke="#ffffff" stroke-width="2" stroke-opacity="0.4" rx="8" />
  <circle cx="200" cy="180" r="50" fill="#ffffff" fill-opacity="0.15" />
  <text x="200" y="320" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#ffffff" text-anchor="middle">{title}</text>
  <text x="200" y="360" font-family="Arial, sans-serif" font-size="14" fill="#ffffff" fill-opacity="0.8" text-anchor="middle">Perpustakaan Digital</text>
  <rect x="80" y="420" width="240" height="3" fill="#ffffff" fill-opacity="0.5" />
</svg>"""

for idx, (name, title, c1, c2) in enumerate(covers):
    content = template.format(idx=idx, title=title, c1=c1, c2=c2)
    with open(os.path.join("static/images", name), "w", encoding="utf-8") as f:
        f.write(content)

print("Covers created successfully")
