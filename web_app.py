# web_app.py
import json
from flask import Flask, render_template_string, jsonify, request
from engine import CoinFlipGame

app = Flask(__name__)

# Create game with UNIFORM initial wealth distribution
game = CoinFlipGame(num_players=100, initial_games=50, wealth_dist="uniform")


def get_full_state():
    stats = game.get_overall_stats()
    active = [i for i in range(game.num_players) if game.wealth[i] > 0]

    wealth_list = game.wealth
    beta_list = game.beta
    colors = ["green" if w > 0 else "red" for w in wealth_list]
    edges = [{"from": u, "to": v} for u, v in game.G.edges()]

    risk_wealth = [{"beta": beta_list[i], "wealth": wealth_list[i]} for i in active]

    sorted_wealth = sorted([w for w in wealth_list if w > 0])
    n = len(sorted_wealth)
    if n > 0:
        cum_wealth = [sum(sorted_wealth[: i + 1]) for i in range(n)]
        cum_wealth_norm = [cw / cum_wealth[-1] for cw in cum_wealth]
        cum_pop = [(i + 1) / n for i in range(n)]
        lorenz_data = {"x": cum_pop, "y": cum_wealth_norm}
    else:
        lorenz_data = {"x": [0, 1], "y": [0, 1]}

    player_ids = list(range(game.num_players))

    return {
        "generation": game.generation,
        "active_players": game.active_players,
        "bankrupt_players": game.num_players - game.active_players,
        "total_wealth": stats["total_wealth"],
        "gini": stats["gini_coefficient"],
        "wealth_list": wealth_list,
        "beta_list": beta_list,
        "colors": colors,
        "player_ids": player_ids,
        "edges": edges,
        "risk_wealth": risk_wealth,
        "lorenz": lorenz_data,
        "avg_wealth": stats["avg_wealth"],
        "max_wealth": stats["max_wealth"],
    }


@app.route("/api/state")
def api_state():
    return jsonify(get_full_state())


@app.route("/api/next_gen", methods=["POST"])
def api_next_gen():
    if game.active_players >= 2:
        game.play_generation()
    return jsonify(get_full_state())


@app.route("/api/10_gens", methods=["POST"])
def api_10_gens():
    for _ in range(10):
        if game.active_players >= 2:
            game.play_generation()
        else:
            break
    return jsonify(get_full_state())


@app.route("/api/100_gens", methods=["POST"])
def api_100_gens():
    for _ in range(100):
        if game.active_players >= 2:
            game.play_generation()
        else:
            break
    return jsonify(get_full_state())


@app.route("/api/reset", methods=["POST"])
def api_reset():
    global game
    game = CoinFlipGame(num_players=100, initial_games=50, wealth_dist="uniform")
    return jsonify(get_full_state())


@app.route("/")
def index():
    # This is the full HTML from your working version (no placeholder)
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Coin Flip Game – Interactive Simulation</title>
        <style>
            * { box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f0f2f5;
                margin: 0;
                padding: 20px;
            }
            h1 { margin-top: 0; color: #1e466e; }
            .dashboard {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 20px;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                border-radius: 12px;
                padding: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .card h3 {
                margin-top: 0;
                margin-bottom: 12px;
                color: #2c3e50;
                border-left: 4px solid #3498db;
                padding-left: 10px;
            }
            .controls {
                display: flex;
                gap: 12px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            button {
                background: #3498db;
                border: none;
                color: white;
                padding: 8px 18px;
                border-radius: 30px;
                font-size: 16px;
                cursor: pointer;
                transition: 0.2s;
                font-weight: bold;
            }
            button:hover { background: #2980b9; transform: scale(1.02); }
            .reset-btn { background: #e67e22; }
            .reset-btn:hover { background: #d35400; }
            .stats {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
                background: #ecf0f1;
                border-radius: 12px;
                padding: 12px 20px;
                margin-bottom: 20px;
                justify-content: space-between;
            }
            .stat-item { font-size: 15px; font-weight: 500; }
            .stat-value { font-weight: bold; color: #2c3e50; margin-left: 6px; }
            canvas, #network { max-height: 350px; width: 100%; }
            #network { height: 350px; border: 1px solid #ddd; border-radius: 8px; background: #fefefe; }
            .subnote { font-size: 12px; color: #7f8c8d; text-align: center; margin-top: 8px; }
            @media (max-width: 900px) { .dashboard { grid-template-columns: 1fr; } }
        </style>
        <script src="/static/chart.umd.min.js"></script>
        <script src="/static/vis-network.min.js"></script>
    </head>
    <body>
        <h1>💰 Coin Flip Game – Wealth Dynamics</h1>
        <div class="controls">
            <button id="btnNext">▶ Next Generation</button>
            <button id="btn10">⏩ 10 Generations</button>
            <button id="btn100">🚀 100 Generations</button>
            <button id="btnReset" class="reset-btn">⟳ Reset Game</button>
        </div>
        <div class="stats" id="statsPanel"></div>

        <div class="dashboard">
            <div class="card"><h3>📊 Wealth Distribution</h3><canvas id="wealthChart"></canvas><div class="subnote">Green=active, Red=bankrupt</div></div>
            <div class="card"><h3>📉 Lorenz Curve (Inequality)</h3><canvas id="lorenzChart"></canvas><div class="subnote">Gini coefficient above</div></div>
            <div class="card"><h3>⚖️ Risk Appetite (β) vs Wealth</h3><canvas id="scatterChart"></canvas><div class="subnote">Active players only</div></div>
            <div class="card"><h3>🕸️ Player Network</h3><div id="network"></div><div class="subnote">Node size ∝ wealth</div></div>
        </div>

        <script>
            let wealthChart, lorenzChart, scatterChart, network = null;
            function destroyChart(chart) { if (chart) chart.destroy(); }

            async function refreshDashboard() {
                try {
                    const resp = await fetch('/api/state');
                    const data = await resp.json();

                    document.getElementById('statsPanel').innerHTML = `
                        <div class="stat-item">🎲 Generation: <span class="stat-value">${data.generation}</span></div>
                        <div class="stat-item">👥 Active: <span class="stat-value">${data.active_players}</span></div>
                        <div class="stat-item">💀 Bankrupt: <span class="stat-value">${data.bankrupt_players}</span></div>
                        <div class="stat-item">💰 Total Wealth: <span class="stat-value">${data.total_wealth.toFixed(1)}</span></div>
                        <div class="stat-item">📈 Avg Wealth: <span class="stat-value">${data.avg_wealth.toFixed(1)}</span></div>
                        <div class="stat-item">🏆 Max Wealth: <span class="stat-value">${data.max_wealth.toFixed(1)}</span></div>
                        <div class="stat-item">⚖️ Gini Coef: <span class="stat-value">${data.gini.toFixed(3)}</span></div>
                    `;

                    destroyChart(wealthChart);
                    wealthChart = new Chart(document.getElementById('wealthChart'), {
                        type: 'bar',
                        data: {
                            labels: data.player_ids.map(id => `P${id}`),
                            datasets: [{
                                label: 'Wealth',
                                data: data.wealth_list,
                                backgroundColor: data.colors.map(c => c === 'green' ? '#2ecc71' : '#e74c3c'),
                                borderWidth: 0,
                                barPercentage: 0.7,
                                categoryPercentage: 0.8
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: true,
                            scales: { y: { beginAtZero: true, title: { display: true, text: 'Wealth' } },
                                      x: { ticks: { autoSkip: true, maxTicksLimit: 15, maxRotation: 90 } } },
                            plugins: { legend: { display: false } }
                        }
                    });

                    destroyChart(lorenzChart);
                    const lorenzData = data.lorenz;
                    lorenzChart = new Chart(document.getElementById('lorenzChart'), {
                        type: 'line',
                        data: {
                            datasets: [{
                                label: 'Actual Distribution',
                                data: lorenzData.x.map((x,i) => ({x, y: lorenzData.y[i]})),
                                borderColor: '#3498db', backgroundColor: 'rgba(52,152,219,0.1)',
                                fill: true, tension: 0.1, pointRadius: 0
                            }, {
                                label: 'Perfect Equality',
                                data: [{x:0,y:0},{x:1,y:1}],
                                borderColor: '#95a5a6', borderDash: [5,5], fill: false, pointRadius: 0
                            }]
                        },
                        options: { responsive: true, scales: { x: { min:0, max:1, title: { text: 'Cumulative Population %' } },
                                                               y: { min:0, max:1, title: { text: 'Cumulative Wealth %' } } } }
                    });

                    destroyChart(scatterChart);
                    scatterChart = new Chart(document.getElementById('scatterChart'), {
                        type: 'scatter',
                        data: { datasets: [{ label: 'Players (active)', data: data.risk_wealth.map(p => ({x: p.beta, y: p.wealth})),
                                            backgroundColor: '#9b59b6', pointRadius: 4 }] },
                        options: { responsive: true, scales: { x: { title: { text: 'Risk Appetite β' }, min:0, max:1 },
                                                               y: { title: { text: 'Wealth' }, beginAtZero: true } } }
                    });

                    const nodes = data.player_ids.map(id => ({
                        id, label: `P${id}`, color: data.colors[id],
                        size: Math.max(10, Math.min(40, 10 + data.wealth_list[id]/20)),
                        font: { size: 12 }
                    }));
                    const edges = data.edges;
                    if (network) network.destroy();
                    network = new vis.Network(document.getElementById('network'),
                        { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) },
                        { physics: { stabilization: true, barnesHut: { gravitationalConstant: -2000 } },
                          nodes: { shape: 'dot', scaling: { label: { enabled: true } } },
                          edges: { smooth: true, width: 1, color: '#aaa' } }
                    );
                } catch (err) { console.error("Refresh error:", err); }
            }

            async function postAction(endpoint) {
                const resp = await fetch(endpoint, { method: 'POST' });
                if (resp.ok) refreshDashboard();
            }

            document.getElementById('btnNext').onclick = () => postAction('/api/next_gen');
            document.getElementById('btn10').onclick = () => postAction('/api/10_gens');
            document.getElementById('btn100').onclick = () => postAction('/api/100_gens');
            document.getElementById('btnReset').onclick = () => postAction('/api/reset');

            refreshDashboard();
        </script>
    </body>
    </html>
    """
    return render_template_string(html_content)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
