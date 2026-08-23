import base64

def get_scratch_card_html(license_key, hardware_id, expiry_date, logo_base64=None):
    """
    Returns a self-contained HTML string with a Premium Silver Scratch-off effect.
    """
    
    logo_html = ""
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="card-logo" alt="Logo">'

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>License Key</title>
    <style>
        body {{
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
            font-family: 'Segoe UI', sans-serif;
            color: white;
        }}
        .card-container {{
            position: relative;
            width: 420px;
            padding: 40px;
            background: white;
            border-radius: 24px;
            box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.6);
            text-align: center;
            color: #333;
            overflow: hidden;
        }}
        
        .card-logo {{
            height: 60px;
            margin-bottom: 20px;
            display: block;
            margin-left: auto;
            margin-right: auto;
        }}

        h1 {{ 
            margin: 0 0 8px; 
            color: #1e293b; 
            letter-spacing: 1px; 
            font-size: 22px;
            text-transform: uppercase;
            font-weight: 800;
        }}
        
        p.subtitle {{ 
            color: #64748b; 
            font-size: 14px; 
            margin: 0 0 30px; 
        }}
        
        /* Scratch Area */
        .scratch-area {{
            position: relative;
            width: 380px;
            height: 80px;
            margin: 0 auto 30px;
            user-select: none;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: inset 0 2px 6px rgba(0,0,0,0.1);
            border: 1px solid #cbd5e1;
        }}
        
        .hidden-code {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            background: #f1f5f9;
            font-family: 'Courier New', monospace;
            font-size: 26px;
            font-weight: bold;
            color: #0f172a;
            letter-spacing: 3px;
            z-index: 1;
        }}
        
        canvas {{
            position: absolute;
            top: 0; left: 0;
            width: 100%; height: 100%;
            z-index: 2;
            cursor: pointer;
            transition: opacity 0.5s;
        }}

        /* Info Box */
        .info-box {{
            background: #f8fafc;
            border-radius: 12px;
            padding: 16px;
            text-align: left;
            font-size: 13px;
            color: #475569;
            margin-bottom: 24px;
            border: 1px solid #e2e8f0;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .info-row {{ display: flex; justify-content: space-between; }}
        .info-label {{ color: #94a3b8; font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .info-value {{ color: #334155; font-weight: 600; font-family: monospace; font-size: 14px; }}

        /* Copy Button */
        .btn {{
            background: #2563eb;
            color: white;
            border: none;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.2s;
            display: none; /* Hidden until scratched */
            width: 100%;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
        }}
        .btn:hover {{ background: #1d4ed8; transform: translateY(-2px); }}
        .btn:active {{ transform: translateY(0); }}

    </style>
</head>
<body>
    <div class="card-container">
        
        {logo_html}

        <h1>Official License</h1>
        <p class="subtitle">Scratch the silver foil to reveal your key</p>

        <div class="scratch-area">
            <div class="hidden-code" id="secretCode">{license_key}</div>
            <canvas id="scratchCanvas"></canvas>
        </div>

        <div class="info-box">
            <div class="info-row">
                <span class="info-label">Hardware ID</span>
                <span class="info-value">{hardware_id}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Valid Until</span>
                <span class="info-value">{expiry_date}</span>
            </div>
        </div>

        <button class="btn" id="copyBtn" onclick="copyKey()">Copy Key to Clipboard</button>
    </div>

    <script>
        const canvas = document.getElementById('scratchCanvas');
        const ctx = canvas.getContext('2d');
        const width = 380;
        const height = 80;
        let isDrawing = false;

        // Setup Canvas
        canvas.width = width;
        canvas.height = height;

        // 1. Draw Silver Foil Gradient
        const gradient = ctx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, '#94a3b8');
        gradient.addColorStop(0.2, '#cbd5e1');
        gradient.addColorStop(0.4, '#94a3b8');
        gradient.addColorStop(0.6, '#e2e8f0');
        gradient.addColorStop(0.8, '#94a3b8');
        gradient.addColorStop(1, '#cbd5e1');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);

        // 2. Add "Scratch Here" Text pattern
        ctx.font = "bold 16px sans-serif";
        ctx.fillStyle = "rgba(71, 85, 105, 0.5)";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        for(let i=0; i<width; i+=120) {{
            ctx.fillText("SCRATCH", i + 60, height/2);
        }}

        // Scratch Logic
        const scratch = (x, y) => {{
            ctx.globalCompositeOperation = 'destination-out';
            ctx.beginPath();
            ctx.arc(x, y, 20, 0, Math.PI * 2);
            ctx.fill();
            checkReveal();
        }};

        // Events
        const getPos = (e) => {{
            const rect = canvas.getBoundingClientRect();
            return {{
                x: (e.touches ? e.touches[0].clientX : e.clientX) - rect.left,
                y: (e.touches ? e.touches[0].clientY : e.clientY) - rect.top
            }};
        }};

        ['mousedown', 'touchstart'].forEach(evt => 
            canvas.addEventListener(evt, (e) => {{ isDrawing = true; const p = getPos(e); scratch(p.x, p.y); }})
        );
        ['mousemove', 'touchmove'].forEach(evt => 
            canvas.addEventListener(evt, (e) => {{ if(isDrawing) {{ e.preventDefault(); const p = getPos(e); scratch(p.x, p.y); }} }})
        );
        ['mouseup', 'mouseleave', 'touchend'].forEach(evt => 
            canvas.addEventListener(evt, () => isDrawing = false)
        );

        // Reveal Logic
        let scratchedPixels = 0;
        function checkReveal() {{
            if(document.getElementById('copyBtn').style.display === 'block') return;
            scratchedPixels++;
            if (scratchedPixels > 20) {{
                document.getElementById('copyBtn').style.display = 'block';
            }}
        }}

        function copyKey() {{
            const code = document.getElementById('secretCode').innerText;
            navigator.clipboard.writeText(code);
            const btn = document.getElementById('copyBtn');
            const originalText = btn.innerText;
            btn.innerText = "Copied!";
            btn.style.background = "#10b981";
            setTimeout(() => {{
                btn.innerText = originalText;
                btn.style.background = "#2563eb";
            }}, 2000);
        }}
    </script>
</body>
</html>
    """