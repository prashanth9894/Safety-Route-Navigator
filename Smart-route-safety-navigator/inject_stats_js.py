"""Patch script to inject stats fetch + narrative JS into index.html"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = "        console.log('\\u2705 SafeRoute initialized successfully');\r\n        console.log('\\U0001f3a8 Professional UI/UX active');\r\n    </script>"

# Try different line endings
for le in ['\r\n', '\n']:
    old = (
        f"        console.log('\\u2705 SafeRoute initialized successfully');{le}"
        f"        console.log('\\U0001f3a8 Professional UI/UX active');{le}"
        f"    </script>"
    )
    if old in content:
        new_block = f"""        console.log('\\u2705 SafeRoute AI initialized \\u2014 NCRB Tamil Nadu Data Active');{le}        console.log('\\ud83d\\udd50 Time-Aware Scoring: ON');{le}{le}        // ============================================================{le}        // LOAD LIVE STATS INTO SIDEBAR HEADER{le}        // ============================================================{le}        (async function loadStats() {{{le}            try {{{le}                const res = await fetch('/get_stats');{le}                const data = await res.json();{le}                const incidentEl = document.getElementById('statIncidents');{le}                const timeEl = document.getElementById('statTime');{le}                if (incidentEl) incidentEl.textContent = `\\U0001f4ca ${{data.total_incidents}} Incidents Tracked`;{le}                if (timeEl && data.time_context) {{{le}                    timeEl.textContent = data.time_context;{le}                    if (data.time_context.includes('Night') || data.time_context.includes('HIGH')) {{{le}                        timeEl.className = 'stat-pill risk';{le}                    }} else if (data.time_context.includes('Evening') || data.time_context.includes('MODERATE')) {{{le}                        timeEl.className = 'stat-pill moderate';{le}                    }} else {{{le}                        timeEl.className = 'stat-pill safe';{le}                    }}{le}                }}{le}            }} catch (e) {{ console.warn('Stats fetch failed', e); }}{le}        }})();{le}    </script>"""
        content = content.replace(old, new_block, 1)
        print(f"SUCCESS with line ending: {repr(le)}")
        break
else:
    # Manual substring search
    idx = content.find("console.log('\u2705 SafeRoute initialized successfully')")
    if idx == -1:
        idx = content.find("SafeRoute initialized")
    print(f"Found at index: {idx}")
    print(repr(content[idx-10:idx+120]))

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done.")
