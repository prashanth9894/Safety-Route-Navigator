"""Patch script to insert /get_stats endpoint into app.py"""
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

stats_endpoint = '''

@app.route("/get_stats", methods=["GET"])
def get_stats():
    """Return live dataset statistics for the UI sidebar header"""
    try:
        df = get_crime_df()
        _, time_label = get_time_risk_multiplier()
        return jsonify({
            "total_incidents": int((df["severity"] > 0).sum()),
            "high_severity": int((df["severity"] >= 7).sum()),
            "safe_zones": int((df["severity"] < 0).sum()),
            "time_context": time_label
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


'''

target = 'if __name__ == "__main__":'
if target in content:
    new_content = content.replace(target, stats_endpoint + target, 1)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: /get_stats endpoint added to app.py")
else:
    print("ERROR: target string not found")
