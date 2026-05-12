# Coin_Flip_Visual

A multi‑agent simulation where players with different risk appetites play repeated coin‑flip games, leading to wealth redistribution, bankruptcy, and measurable inequality (Gini coefficient). The project provides both a **desktop GUI** (Matplotlib) and a **web‑based interactive dashboard** (Flask + Chart.js + vis‑network).

## Table of Contents

- [Features](#features)
- [How the Game Works](#how-the-game-works)
- [Installation & Dependencies](#installation--dependencies)
- [Running the Simulation](#running-the-simulation)
  - [Desktop Version (Matplotlib)](#desktop-version-matplotlib)
  - [Web Dashboard (Flask)](#web-dashboard-flask)
- [Project Structure](#project-structure)
- [Web Dashboard Static Files](#web-dashboard-static-files)
- [Controls & Visualizations](#controls--visualizations)
- [Customisation](#customisation)
- [License](#license)

## Features

- **Wealth distributions**: power‑law (default) or uniform initial wealth.
- **Risk appetite (β)**: each player has a random β ∈ [0,1], influencing the maximum stake they are willing to risk.
- **Pairwise coin flips**: two randomly selected players bet the minimum of their individual risk‑adjusted wealth; the winner takes the stake.
- **Bankruptcy**: wealth ≤ 0 turns a player bankrupt (red, removed from future games).
- **Wealth conservation**: total system wealth remains constant.
- **Real‑time statistics**: Gini coefficient, Lorenz curve, active/bankrupt counts, wealth distribution.
- **Two interfaces**:
  - Desktop: interactive Matplotlib figure with buttons.
  - Web: responsive dashboard with bar charts, network graph, scatter plot, and Lorenz curve.

## How the Game Works

1. **Initialisation**  
   - `N = 100` players are created.  
   - Each player gets an initial wealth (power‑law or uniform) normalised so total wealth = `N * 100`.  
   - Each player receives a random risk appetite β ~ Uniform(0,1).

2. **A single generation** (by default 50 games)  
   - Two active players (wealth > 0) are chosen at random.  
   - Maximum stake each can offer: `(1-β) * wealth`.  
   - Actual stake = `min(stake_i, stake_j)`.  
   - A fair coin decides the winner.  
   - The stake is transferred from loser to winner.  
   - If the loser’s wealth drops to zero or below, they become bankrupt (marked red, inactive).

3. **Termination** – simulation stops when fewer than two players remain active (or manually reset).

## Installation & Dependencies

### Python Requirements

All required packages are listed below. Create a virtual environment (recommended) and install them.

```bash
pip install numpy matplotlib networkx flask
```

> **Note**: Even when using only the web version, `engine.py` imports `matplotlib`. Therefore `matplotlib` must be installed.

### JavaScript / Web Libraries

The web dashboard uses **Chart.js** and **vis‑network**. These are client‑side libraries. You must place the following files inside a `static/` folder (see [Web Dashboard Static Files](#web-dashboard-static-files)).

## Running the Simulation

### Desktop Version (Matplotlib)

```bash
python engine.py
```

A Matplotlib window opens with six subplots and control buttons (**Next Gen**, **10 Gens**, **100 Gens**, **Reset Game**).  
*Requires an interactive backend (e.g., TkAgg).*

### Web Dashboard (Flask)

1. Ensure the static files are in place (see below).  
2. Run the Flask application:

```bash
python web_app.py
```

3. Open your browser at [http://localhost:5000](http://localhost:5000)  
4. Use the buttons to advance the simulation step by step or in batches.

## Project Structure

```
.
├── engine.py          # Simulation core (CoinFlipGame) + desktop GUI
├── web_app.py         # Flask web server and API endpoints
├── static/            # (create this folder) – see next section
│   ├── chart.umd.min.js
│   └── vis-network.min.js
└── README.md
```

## Web Dashboard Static Files

The file `web_app.py` expects the following two JavaScript libraries to be served from the `/static/` directory:

- `chart.umd.min.js` – [Chart.js](https://www.chartjs.org/) (v4+)
- `vis-network.min.js` – [vis‑network](https://visjs.github.io/vis-network/docs/network/) (v9+)

**How to obtain them**:

- Download from the official CDN or repository, or
- Use a package manager (npm) and copy the minified files, or
- Replace the `<script>` URLs in `web_app.py` with **CDN links** (easiest).  
  For quick testing, you can edit the two lines:

  ```html
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js"></script>
  ```

  Then you **do not need** the `static/` folder. The provided code already uses local paths; change them as desired.

## Controls & Visualizations

| Component               | Desktop (engine.py) | Web Dashboard (web_app.py) |
|------------------------|-------------------|----------------------------|
| Wealth bar chart       | ✅                 | ✅                          |
| Player network graph   | ✅                 | ✅                          |
| Lorenz curve / Gini    | ✅                 | ✅                          |
| Risk appetite scatter  | ✅                 | ✅                          |
| Player status / logs   | ✅                 | (stats panel)              |
| Generation buttons     | ✅                 | ✅                          |
| Reset button           | ✅                 | ✅                          |

**Web Dashboard Additional Info**  
- Node size in network graph is proportional to wealth.  
- Hover over nodes to see player IDs.  
- Gini coefficient updates every generation.

## Customisation

You can modify the following parameters inside `web_app.py` or `engine.py`:

- `num_players` (default 100)  
- `initial_games` per generation (default 50)  
- `wealth_dist` – change from `"power"` to `"uniform"`  
- Risk appetite generation – currently `np.random.uniform(0,1)`  
- Network topology – currently Erdős–Rényi with `p=0.1`

## License

This project is open source and available under the MIT License.

---

**Enjoy exploring wealth inequality dynamics!**  
For questions or suggestions, feel free to open an issue.
