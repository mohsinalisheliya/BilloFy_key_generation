import base64
from django.conf import settings

def get_scratch_card_html(license_key, hardware_id, expiry_date, logo_base64=None):
    """
    Returns a self-contained HTML string with a Red-Themed Scratch Card.
    Scratch surface contains:
    - Repeating diagonal logo watermark
    - Center 'SCRATCH HERE' text
    """

    logo_data_uri = ""
    logo_html = ""

    if logo_base64:
        logo_data_uri = f"data:image/png;base64,{logo_base64}"
        logo_html = f'<img src="{logo_data_uri}" class="card-logo" alt="Logo">'

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{settings.BRANDING['PROJECT_NAME']} - License</title>

<style>
body {{
    margin: 0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #0f172a;
    font-family: 'Segoe UI', Tahoma, sans-serif;
}}

.card-container {{
    position: relative;
    width: 400px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 0 0 8px #dc2626, 0 30px 60px rgba(0,0,0,0.5);
    padding: 40px 30px;
    text-align: center;
}}

.top-banner {{
    position: absolute;
    top: 0;
    left: 0;
    height: 8px;
    width: 100%;
    background: #dc2626;
}}

.card-logo {{
    height: 70px;
    margin: 20px auto;
    display: block;
}}

h1 {{
    margin: 0;
    font-size: 22px;
    letter-spacing: 1px;
    color: #1e293b;
}}

.subtitle {{
    font-size: 14px;
    color: #64748b;
    margin: 6px 0 25px;
}}

.scratch-area {{
    position: relative;
    width: 360px;
    height: 80px;
    margin: 0 auto 25px;
    border-radius: 12px;
    overflow: hidden;
    border: 2px dashed #cbd5e1;
}}

.hidden-code {{
    position: absolute;
    inset: 0;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fef2f2;
    font-family: 'Courier New', monospace;
    font-size: 24px;
    font-weight: bold;
    color: #dc2626;
    z-index: 1;
}}

canvas {{
    position: absolute;
    inset: 0;
    z-index: 2;
}}

.info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 25px;
}}

.info-item {{
    background: #f8fafc;
    border-radius: 10px;
    padding: 10px;
    border: 1px solid #e2e8f0;
    text-align: left;
}}

.info-label {{
    font-size: 11px;
    color: #94a3b8;
    text-transform: uppercase;
    font-weight: bold;
}}

.info-value {{
    font-size: 13px;
    color: #334155;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}}

.btn {{
    display: none;
    width: 100%;
    padding: 14px;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}}
</style>
</head>

<body>

<div class="card-container">
    <div class="top-banner"></div>

    {logo_html}

    <h1>Official License</h1>
    <p class="subtitle">Scratch below to reveal your activation key</p>

    <div class="scratch-area">
        <div class="hidden-code" id="secretCode">{license_key}</div>
        <canvas id="scratchCanvas"></canvas>
    </div>

    <div class="info-grid">
        <div class="info-item">
            <span class="info-label">Hardware ID</span>
            <span class="info-value">{hardware_id}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Valid Until</span>
            <span class="info-value">{expiry_date}</span>
        </div>
    </div>

    <button class="btn" id="copyBtn" onclick="copyKey()">Copy Key</button>
</div>

<script>
const canvas = document.getElementById("scratchCanvas");
const ctx = canvas.getContext("2d");
const width = 360;
const height = 80;
canvas.width = width;
canvas.height = height;

// Silver base
const grad = ctx.createLinearGradient(0, 0, width, height);
grad.addColorStop(0, "#94a3b8");
grad.addColorStop(0.5, "#e5e7eb");
grad.addColorStop(1, "#94a3b8");
ctx.fillStyle = grad;
ctx.fillRect(0, 0, width, height);

// Repeating diagonal watermark
const logoUrl = "{logo_data_uri}";
if (logoUrl) {{
    const img = new Image();
    img.onload = () => {{
        ctx.save();
        ctx.globalAlpha = 0.12;
        ctx.translate(width / 2, height / 2);
        ctx.rotate(-Math.PI / 6);

        const size = 40;
        const gap = 30;

        for (let x = -width; x < width; x += size + gap) {{
            for (let y = -height; y < height; y += size + gap) {{
                ctx.drawImage(img, x, y, size, size);
            }}
        }}
        ctx.restore();
    }};
    img.src = logoUrl;
}}

// Center text
ctx.globalAlpha = 0.45;
ctx.font = "bold 18px sans-serif";
ctx.fillStyle = "#475569";
ctx.textAlign = "center";
ctx.textBaseline = "middle";
ctx.fillText("SCRATCH HERE", width / 2, height / 2);
ctx.globalAlpha = 1;

// Scratch logic
let drawing = false;
let scratched = 0;

function scratch(x, y) {{
    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(x, y, 18, 0, Math.PI * 2);
    ctx.fill();
    scratched++;
    if (scratched > 20) {{
        document.getElementById("copyBtn").style.display = "block";
    }}
}}

function pos(e) {{
    const r = canvas.getBoundingClientRect();
    return {{
        x: (e.touches ? e.touches[0].clientX : e.clientX) - r.left,
        y: (e.touches ? e.touches[0].clientY : e.clientY) - r.top
    }};
}}

["mousedown","touchstart"].forEach(ev =>
    canvas.addEventListener(ev, e => {{
        drawing = true;
        const p = pos(e);
        scratch(p.x, p.y);
    }})
);

["mousemove","touchmove"].forEach(ev =>
    canvas.addEventListener(ev, e => {{
        if (!drawing) return;
        e.preventDefault();
        const p = pos(e);
        scratch(p.x, p.y);
    }})
);

["mouseup","mouseleave","touchend"].forEach(ev =>
    canvas.addEventListener(ev, () => drawing = false)
);

function copyKey() {{
    navigator.clipboard.writeText(document.getElementById("secretCode").innerText);
    const btn = document.getElementById("copyBtn");
    btn.innerText = "COPIED ✓";
    btn.style.background = "#10b981";
}}
</script>

</body>
</html>
"""
