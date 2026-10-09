
from flask import Flask, jsonify, render_template_string
from datetime import datetime, timezone

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevSecOps Security Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
        }
        header {
            padding: 28px 6%;
            background: #111c32;
            border-bottom: 1px solid #334155;
        }
        header h1 { margin: 0 0 8px; color: #38bdf8; }
        header p { margin: 0; color: #94a3b8; }
        main { padding: 30px 6%; }
        .status {
            padding: 15px;
            margin-bottom: 24px;
            background: #132b2a;
            border: 1px solid #166534;
            border-radius: 10px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 18px;
        }
        .card {
            padding: 22px;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
        }
        .card h2 { margin-top: 0; font-size: 19px; }
        .card p { color: #94a3b8; line-height: 1.6; }
        .tag {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 6px;
            background: #334155;
            color: #7dd3fc;
            font-size: 12px;
        }
        a.button {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 14px;
            border-radius: 7px;
            background: #0284c7;
            color: white;
            text-decoration: none;
        }
        a.button:hover { background: #0369a1; }
        footer {
            padding: 25px 6%;
            color: #64748b;
            font-size: 13px;
        }
    </style>
</head>
<body>
<header>
    <h1>DevSecOps Security Dashboard</h1>
    <p>Application Security Testing Laboratory</p>
</header>

<main>
    <div class="status">
        <strong>● Application status:</strong> Running
        <br><br>
        <strong>Environment:</strong> Development / Testing
    </div>

    <div class="grid">
        <section class="card">
            <span class="tag">SAST</span>
            <h2>Static Application Security Testing</h2>
            <p>Manba kodidagi xavfsizlik zaifliklarini statik tahlil qilish.</p>
            <p>Tool: Semgrep CE</p>
            <a class="button" href="/health">API status</a>
        </section>

        <section class="card">
            <span class="tag">SCA</span>
            <h2>Software Composition Analysis</h2>
            <p>Loyihadagi kutubxonalar va bog‘liqliklarning zaifliklarini aniqlash.</p>
            <p>Tool: OWASP Dependency-Check</p>
            <a class="button" href="/api/info">Project info</a>
        </section>

        <section class="card">
            <span class="tag">SECRETS</span>
            <h2>Secret Detection</h2>
            <p>Kod va repozitoriyda oshkor bo‘lib qolgan token, parol yoki kalitlarni aniqlash.</p>
            <p>Tool: Gitleaks</p>
            <a class="button" href="/api/info">Project info</a>
        </section>

        <section class="card">
            <span class="tag">CONTAINER</span>
            <h2>Container Security</h2>
            <p>Docker image tarkibidagi paketlar, zaifliklar va konfiguratsiya xatarlarini tekshirish.</p>
            <p>Tool: Trivy</p>
            <a class="button" href="/health">API status</a>
        </section>

        <section class="card">
            <span class="tag">DAST</span>
            <h2>Dynamic Application Security Testing</h2>
            <p>Ishlayotgan web-ilovani HTTP so‘rovlari orqali dinamik xavfsizlik tekshiruvidan o‘tkazish.</p>
            <p>Tool: OWASP ZAP</p>
            <a class="button" href="/health">Test endpoint</a>
        </section>

        <section class="card">
            <span class="tag">REPORT</span>
            <h2>Security Reports</h2>
            <p>Pipeline natijalari va xavfsizlik hisobotlarini ko‘rish uchun bo‘lim.</p>
            <p>Source: Jenkins artifacts</p>
            <a class="button" href="/api/info">Application JSON</a>
        </section>
    </div>
</main>

<footer>
    DevSecOps Laboratory · Flask · Security Testing
</footer>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "application": "devsecops-lab",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.get("/api/info")
def info():
    return jsonify({
        "name": "DevSecOps Laboratory",
        "version": "1.0.0",
        "framework": "Flask",
        "security_checks": [
            "SAST",
            "SCA",
            "Secrets",
            "Container",
            "DAST",
            "Report"
        ],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
