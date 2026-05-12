# engine.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as mpatches
from matplotlib.widgets import Button
import networkx as nx
import random
import tkinter as tk
from tkinter import ttk
import warnings

warnings.filterwarnings("ignore")


class CoinFlipGame:
    def __init__(self, num_players=100, initial_games=100, wealth_dist="power"):
        """
        wealth_dist: 'power' for power-law distribution (default), 'uniform' for uniform distribution
        """
        self.num_players = num_players
        self.initial_games = initial_games
        self.wealth_dist = wealth_dist
        self.players = []
        self.generation = 0
        self.active_players = num_players
        self.game_history = []

        # Generate initial wealth distribution
        self.generate_initial_wealth()

        # Generate risk appetites (beta values between 0 and 1)
        self.generate_risk_appetites()

        # Initialize colors (green for all initially)
        self.colors = ["green"] * num_players

        # Create graph
        self.G = nx.erdos_renyi_graph(num_players, 0.1)

    def generate_initial_wealth(self):
        """Generate wealth from selected distribution (power law or uniform)"""
        if self.wealth_dist == "power":
            # Power law p(w) ∝ w^-3 using inverse transform sampling
            u = np.random.uniform(0, 1, self.num_players)
            wealths = 1 / np.sqrt(1 - u)
        else:  # uniform
            # Uniform between 0 and 200 (will be normalized)
            wealths = np.random.uniform(0, 200, self.num_players)

        # Normalize to start with total wealth = num_players * 100
        total_wealth_target = self.num_players * 100
        current_total = np.sum(wealths)
        wealths = wealths * (total_wealth_target / current_total)

        self.wealth = wealths.tolist()

    def generate_risk_appetites(self):
        """Generate random risk appetite values between 0 and 1"""
        self.beta = np.random.uniform(0, 1, self.num_players).tolist()

    def play_generation(self, num_games=None):
        """Play one generation of games"""
        if num_games is None:
            num_games = self.initial_games

        game_results = []
        active_indices = [i for i in range(self.num_players) if self.wealth[i] > 0]

        if len(active_indices) < 2:
            return game_results

        for _ in range(num_games):
            if len(active_indices) >= 2:
                i, j = random.sample(active_indices, 2)

                # Calculate maximum possible prize
                max_prize_i = (1 - self.beta[i]) * self.wealth[i]
                max_prize_j = (1 - self.beta[j]) * self.wealth[j]

                # Actual prize is the minimum of the two
                prize = min(max_prize_i, max_prize_j)

                # Flip coin (50/50 chance)
                if random.random() < 0.5:
                    winner, loser = i, j
                else:
                    winner, loser = j, i

                # Ensure loser has enough to pay
                actual_transfer = min(prize, self.wealth[loser])

                # Update wealth
                if actual_transfer > 0:
                    self.wealth[winner] += actual_transfer
                    self.wealth[loser] -= actual_transfer

                    # Check if loser is bankrupt
                    if self.wealth[loser] <= 0:
                        self.colors[loser] = "red"
                        self.active_players -= 1

                game_results.append(
                    {
                        "players": (i, j),
                        "winner": winner,
                        "prize": actual_transfer,
                        "generation": self.generation,
                    }
                )

        self.generation += 1
        self.game_history.extend(game_results)
        return game_results

    def get_player_stats(self, player_id):
        """Get statistics for a specific player"""
        return {
            "id": player_id,
            "wealth": self.wealth[player_id],
            "beta": self.beta[player_id],
            "color": self.colors[player_id],
            "active": self.wealth[player_id] > 0,
        }

    def get_overall_stats(self):
        """Get overall game statistics"""
        active_wealth = [w for w in self.wealth if w > 0]
        bankrupt_count = sum(1 for w in self.wealth if w <= 0)

        return {
            "generation": self.generation,
            "active_players": self.active_players,
            "bankrupt_players": bankrupt_count,
            "total_wealth": sum(self.wealth),
            "avg_wealth": np.mean(active_wealth) if active_wealth else 0,
            "median_wealth": np.median(active_wealth) if active_wealth else 0,
            "gini_coefficient": self.calculate_gini(),
            "max_wealth": max(self.wealth) if self.wealth else 0,
            "min_wealth": min(w for w in self.wealth if w > 0) if active_wealth else 0,
        }

    def calculate_gini(self):
        """Calculate Gini coefficient for wealth inequality"""
        wealth_array = np.array([w for w in self.wealth if w > 0])
        if len(wealth_array) == 0:
            return 0

        wealth_array.sort()
        n = len(wealth_array)
        index = np.arange(1, n + 1)
        return (np.sum((2 * index - n - 1) * wealth_array)) / (n * np.sum(wealth_array))


class GameVisualization:
    def __init__(self, game):
        self.game = game
        self.fig = plt.figure(figsize=(15, 8))
        self.setup_plots()

    def setup_plots(self):
        """Setup the matplotlib figure with multiple subplots"""
        # Main layout
        gs = self.fig.add_gridspec(2, 3, height_ratios=[1, 1], width_ratios=[1, 1, 1])

        # Wealth distribution plot
        self.ax1 = self.fig.add_subplot(gs[0, 0])
        self.ax1.set_title("Wealth Distribution", fontsize=12, fontweight="bold")
        self.ax1.set_xlabel("Player ID")
        self.ax1.set_ylabel("Wealth")

        # Network graph
        self.ax2 = self.fig.add_subplot(gs[0, 1])
        self.ax2.set_title("Player Network", fontsize=12, fontweight="bold")

        # Wealth inequality (Lorenz curve)
        self.ax3 = self.fig.add_subplot(gs[0, 2])
        self.ax3.set_title(
            "Lorenz Curve (Wealth Inequality)", fontsize=12, fontweight="bold"
        )
        self.ax3.set_xlabel("Cumulative Population %")
        self.ax3.set_ylabel("Cumulative Wealth %")
        self.ax3.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect Equality")

        # Risk appetite vs wealth
        self.ax4 = self.fig.add_subplot(gs[1, 0])
        self.ax4.set_title("Risk Appetite vs Wealth", fontsize=12, fontweight="bold")
        self.ax4.set_xlabel("Risk Appetite (β)")
        self.ax4.set_ylabel("Wealth")

        # Player status
        self.ax5 = self.fig.add_subplot(gs[1, 1])
        self.ax5.set_title("Player Status", fontsize=12, fontweight="bold")
        self.ax5.axis("off")

        # Game statistics
        self.ax6 = self.fig.add_subplot(gs[1, 2])
        self.ax6.set_title("Game Statistics", fontsize=12, fontweight="bold")
        self.ax6.axis("off")

        plt.tight_layout()

    def update_plots(self):
        """Update all plots with current game state"""
        self.fig.suptitle(
            f"Coin Flip Game - Generation {self.game.generation}",
            fontsize=14,
            fontweight="bold",
            y=0.98,
        )

        # Clear axes
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
            ax.clear()
            if ax not in [self.ax5, self.ax6]:
                ax.grid(True, alpha=0.3)

        # Plot 1: Wealth distribution
        active_players = [
            i for i in range(self.game.num_players) if self.game.wealth[i] > 0
        ]
        bankrupt_players = [
            i for i in range(self.game.num_players) if self.game.wealth[i] <= 0
        ]

        colors = []
        for i in range(self.game.num_players):
            if i in bankrupt_players:
                colors.append("red")
            else:
                colors.append("green")

        self.ax1.bar(
            range(self.game.num_players), self.game.wealth, color=colors, alpha=0.7
        )
        self.ax1.set_title("Wealth Distribution", fontsize=12, fontweight="bold")
        self.ax1.set_xlabel("Player ID")
        self.ax1.set_ylabel("Wealth")

        # Plot 2: Network graph
        pos = nx.spring_layout(self.game.G)

        node_colors = []
        node_sizes = []
        for i in range(self.game.num_players):
            node_colors.append(self.game.colors[i])
            if self.game.wealth[i] > 0:
                node_sizes.append(100 + self.game.wealth[i] / 10)
            else:
                node_sizes.append(50)

        nx.draw(
            self.game.G,
            pos,
            ax=self.ax2,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.7,
            with_labels=False,
        )
        self.ax2.set_title("Player Network", fontsize=12, fontweight="bold")

        # Plot 3: Lorenz curve
        self.plot_lorenz_curve()

        # Plot 4: Risk appetite vs wealth
        active_beta = [self.game.beta[i] for i in active_players]
        active_wealth = [self.game.wealth[i] for i in active_players]

        if active_players:
            self.ax4.scatter(active_beta, active_wealth, c="blue", alpha=0.6)
            self.ax4.set_title(
                "Risk Appetite vs Wealth", fontsize=12, fontweight="bold"
            )
            self.ax4.set_xlabel("Risk Appetite (β)")
            self.ax4.set_ylabel("Wealth")

            # Add trend line
            if len(active_players) > 1:
                z = np.polyfit(active_beta, active_wealth, 1)
                p = np.poly1d(z)
                self.ax4.plot(
                    np.sort(active_beta), p(np.sort(active_beta)), "r--", alpha=0.8
                )

        # Plot 5: Player status
        self.ax5.axis("off")
        stats_text = self.get_status_text()
        self.ax5.text(
            0.1,
            0.9,
            stats_text,
            fontsize=10,
            verticalalignment="top",
            transform=self.ax5.transAxes,
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

        # Plot 6: Game statistics
        self.ax6.axis("off")
        game_stats = self.game.get_overall_stats()
        stats_text = (
            f"Generation: {game_stats['generation']}\n"
            f"Active Players: {game_stats['active_players']}\n"
            f"Bankrupt Players: {game_stats['bankrupt_players']}\n"
            f"Total Wealth: {game_stats['total_wealth']:.2f}\n"
            f"Avg Wealth: {game_stats['avg_wealth']:.2f}\n"
            f"Gini Coefficient: {game_stats['gini_coefficient']:.3f}\n"
            f"Max Wealth: {game_stats['max_wealth']:.2f}\n"
            f"Min Wealth: {game_stats['min_wealth']:.2f}"
        )
        self.ax6.text(
            0.1,
            0.9,
            stats_text,
            fontsize=10,
            verticalalignment="top",
            transform=self.ax6.transAxes,
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
        )

        # Add legend
        green_patch = mpatches.Patch(color="green", label="Active Players")
        red_patch = mpatches.Patch(color="red", label="Bankrupt Players")
        self.ax1.legend(handles=[green_patch, red_patch], loc="upper right")

        plt.draw()

    def plot_lorenz_curve(self):
        """Plot Lorenz curve for wealth inequality"""
        wealth_sorted = np.sort([w for w in self.game.wealth if w > 0])
        n = len(wealth_sorted)

        if n > 0:
            cumulative_wealth = np.cumsum(wealth_sorted)
            cumulative_wealth_normalized = cumulative_wealth / cumulative_wealth[-1]

            line_equality = np.linspace(0, 1, n)

            self.ax3.plot(
                line_equality,
                cumulative_wealth_normalized,
                "b-",
                label="Actual Distribution",
                linewidth=2,
            )
            self.ax3.plot([0, 1], [0, 1], "k--", alpha=0.5, label="Perfect Equality")
            self.ax3.fill_between(
                line_equality,
                cumulative_wealth_normalized,
                line_equality,
                alpha=0.3,
                color="blue",
            )

            self.ax3.set_title(
                "Lorenz Curve (Wealth Inequality)", fontsize=12, fontweight="bold"
            )
            self.ax3.set_xlabel("Cumulative Population %")
            self.ax3.set_ylabel("Cumulative Wealth %")
            self.ax3.legend(loc="upper left")

    def get_status_text(self):
        """Get status text for display"""
        active_count = self.game.active_players
        bankrupt_count = self.game.num_players - active_count

        wealth_with_indices = [(w, i) for i, w in enumerate(self.game.wealth) if w > 0]
        wealth_with_indices.sort(reverse=True)

        top_players_text = "Top 5 Wealthiest Players:\n"
        for rank, (wealth, idx) in enumerate(wealth_with_indices[:5], 1):
            top_players_text += f"{rank}. Player {idx}: ${wealth:.2f}\n"

        recent_games = self.game.game_history[-5:] if self.game.game_history else []
        recent_games_text = "\nRecent Games:\n"
        for game in recent_games:
            players = game["players"]
            winner = game["winner"]
            prize = game["prize"]
            recent_games_text += (
                f"P{players[0]} vs P{players[1]}: P{winner} won ${prize:.2f}\n"
            )

        return f"Active: {active_count}\nBankrupt: {bankrupt_count}\n\n{top_players_text}\n{recent_games_text}"


class GameController:
    def __init__(self):
        # You can change to uniform distribution here too if desired
        self.game = CoinFlipGame(num_players=100, initial_games=50, wealth_dist="power")
        self.viz = GameVisualization(self.game)
        self.setup_controls()
        self.viz.update_plots()

    def setup_controls(self):
        """Add control buttons to the figure"""
        ax_next = plt.axes([0.15, 0.02, 0.1, 0.04])
        ax_10 = plt.axes([0.27, 0.02, 0.1, 0.04])
        ax_100 = plt.axes([0.39, 0.02, 0.1, 0.04])
        ax_reset = plt.axes([0.51, 0.02, 0.1, 0.04])

        self.btn_next = Button(ax_next, "Next Gen")
        self.btn_10 = Button(ax_10, "10 Gens")
        self.btn_100 = Button(ax_100, "100 Gens")
        self.btn_reset = Button(ax_reset, "Reset Game")

        self.btn_next.on_clicked(lambda event: self.play_generations(1))
        self.btn_10.on_clicked(lambda event: self.play_generations(10))
        self.btn_100.on_clicked(lambda event: self.play_generations(100))
        self.btn_reset.on_clicked(lambda event: self.reset_game())

    def play_generations(self, num_generations):
        for _ in range(num_generations):
            if self.game.active_players >= 2:
                self.game.play_generation()
        self.viz.update_plots()

    def reset_game(self):
        self.game = CoinFlipGame(num_players=100, initial_games=50, wealth_dist="power")
        self.viz.game = self.game
        self.viz.update_plots()


def main():
    """Main function to run the game"""
    print("Starting Coin Flip Game Simulation...")
    print("=" * 50)
    print("Game Rules:")
    print("1. 100 players with selected wealth distribution (power law or uniform)")
    print("2. Each player has random risk appetite (β between 0 and 1)")
    print("3. Players randomly pair for coin flip games")
    print("4. Prize = min((1-β₁)w₁, (1-β₂)w₂)")
    print("5. Bankrupt players (wealth ≤ 0) turn red")
    print("6. Total wealth is conserved")
    print("=" * 50)
    print("\nControls:")
    print("- Next Gen: Play 1 generation (50 games)")
    print("- 10 Gens: Play 10 generations")
    print("- 100 Gens: Play 100 generations")
    print("- Reset Game: Start over with new random players")
    print("\nVisualizations:")
    print("1. Wealth Distribution (bar chart)")
    print("2. Player Network (graph)")
    print("3. Lorenz Curve (wealth inequality)")
    print("4. Risk Appetite vs Wealth (scatter)")
    print("5. Player Status (text)")
    print("6. Game Statistics (text)")

    controller = GameController()
    plt.show()


if __name__ == "__main__":
    main()
