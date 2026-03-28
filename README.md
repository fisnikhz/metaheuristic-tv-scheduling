# Simulated Annealing for TV Channel Scheduling Optimization

This repository contains an implementation of the Simulated Annealing (SA) metaheuristic algorithm applied to the highly constrained TV Channel Scheduling Optimization for Public Spaces problem. The implementation utilizes a hybrid approach: combining Simulated Annealing with Beam Search for initial solution generation, and employing various structure-aware perturbation strategies (Large Neighborhood Search, Channel Swapping, Targeted Weakness Removal) to iteratively refine and maximize the total viewership score.

## Algorithm Overview

### Simulated Annealing (SA)
The core Simulated Annealing engine (`SimulatedAnnealingScheduler`) iteratively explores the constrained solution space to reliably maximize the objective function (total viewership score). It is specifically adapted to escape local optima by occasionally accepting non-improving (worse) solutions with a dynamically decreasing probability. 

The implementation works as follows:

1. **Initial Solution Generation**: Before SA begins, a deterministic Beam Search constructs a high-quality, strictly constraint-satisfying baseline schedule.
2. **Main Loop**: Iterates for a predefined number of `max_iterations`, randomly perturbing the schedule in each step, executing a localized reconstruction, and evaluating the new fitness score.
3. **Acceptance Criterion**: Uses the standard Metropolis criterion:
   - If the new solution improves the total score ($\Delta > 0$), it is always accepted.
   - If the new solution is worse ($\Delta \le 0$), it is accepted with probability $P = e^{\Delta / T}$, where $T$ is the current temperature.
4. **Cooling Schedule**: The temperature $T$ decays exponentially at each step based on a precisely calculated cooling rate, gradually shifting the algorithm from broad exploration to greedy exploitation.

**Key Parameters:**
- `max_iterations`: Maximum number of SA iterations (default: 5000). The search terminates strictly after these iterations.
- `initial_temp`: Starting exploration temperature (adaptive based on strict instance complexity).
- `cooling_rate`: Exponential decay factor that guarantees $T$ reaches near-zero by the final iteration.

### Instance-Aware Adaptations
The algorithm adaptively adjusts its thermodynamic parameters based on the specific dimensions of the TV scheduling instance (e.g., small geographical instances like `Germany` vs. massive datasets like `USA` or `YouTube`).

1. **Temperature Scaling**:
   - **Small Instances (< 1000 total programs)**: The search space is smaller and the initial Beam Search is highly accurate. Thus, SA starts with a lower initial temperature ($T=50$). This prevents excessive disruption of an already strong heuristic mapping while still allowing localized optimization.
   - **Large Instances (>= 1000 total programs)**: The landscape is notoriously rugged with deep, complex local optima. SA starts with a substantially higher initial temperature ($T=500$) to allow much broader exploration and widespread architectural changes early in the search.

2. **Cooling Calibration**: 
   - The cooling rate is mathematically formulated at runtime: `cooling_rate = (target_end_temp / initial_temp) ** (1.0 / max_iterations)`. This ensures that regardless of initial temperature or total iterations, the system gracefully cools down to a solid freeze (`0.05`) right at the end of the execution block.

### Perturbation Strategy (Neighborhood Operators)
The perturbation mechanism (`_perturb` method) randomly leverages multiple operators rooted in Large Neighborhood Search (LNS) principles. Because constraint violations are strictly forbidden, these operators act purely destructively ("Destroy Phase"), clearing out specific blocks of time. An operator is chosen uniformly at random (each with $\sim$25% probability) per iteration:

1. **Segment Destroy and Rebuild (25% probability)**:
   - Removes a localized, random contiguous segment (1-5 programs) from the schedule.
   - **Purpose**: Ideal for fine-grained tuning, letting the algorithm swap out a couple of sub-optimal programs for slightly better ones without destroying the entire day's flow.

2. **Large Neighborhood Search (25% probability)**:
   - Aggressively removes a much larger chunk of contiguous programs (5-15 programs).
   - **Purpose**: A highly disruptive perturbation designed to thoroughly escape deep local optima by forcing the reconstruction phase to find a completely different sequence of shows for a major portion of the day.

3. **Channel Block Swap (25% probability)**:
   - Targets a specific, randomly chosen channel and removes a segment of exclusively its scheduled programs.
   - **Purpose**: Facilitates shifting intense programming logic across different channels effortlessly, helping the scheduler balance constraints like genre repetition across parallel broadcasting streams.

4. **Targeted Fitness Removal (25% probability)**:
   - Scans the entirety of the current schedule to identify the specific program yielding the absolute lowest fitness/viewership score.
   - Actively removes a surrounding time window (up to 10 programs) centered strictly around this weak link.
   - **Purpose**: Decisively penalizes and roots out poor branching choices made in previous iterations, ensuring the most inefficient slots are repeatedly optimized.

### Target Reconstruction (Mini-Beam Search)
Immediately after the destroy phase frees up a gap in the schedule, the empty block cannot be filled blindly due to strict rules (No Overlap, Genre Repetition limits, Priority Blocks, Time Windows). The algorithm utilizes a hyper-fast, localized "Mini-Beam Search" to rapidly rebuild the unassigned gap:

- **Tight Beam Width**: Maintains a heavily restricted beam width of 3 (for small instances) or 5 (for large instances) to ensure near-instantaneous reconstruction speed (run thousands of times per second).
- **Density-Driven Fill**: Greedily evaluates candidate programs based on a slightly randomized "Points per Minute" density heuristic to insert highly efficient, high-value programs back into the void.
- **100% Feasibility Guarantee**: By routing the reconstruction through the native beam tree, it guarantees that all strict domain constraints are perfectly preserved flawlessly. SA instances *never* operate on invalid schedules.

### Initial Solution Generation (Beam Search)
The starting solution is natively generated using the `BeamSearchScheduler`. This guarantees that SA does not waste enormous compute time traversing completely invalid or deeply low-quality areas of the search space from scratch.

1. **Beam Strategy**: Evaluates and maintains a set of the $N$ best partial schedules at each minute step (Standard Beam Width = 100).
2. **Lookahead Mechanism**: Evaluates the future impact of current scheduling decisions up to 4 levels deep. This prevents high-value blockbusters from being accidentally locked out because of naive greedy genre-repetition violations.
3. **Density Heuristic**: Evaluates the potential of future remaining time slots using a robust score density heuristic (points per minute), deliberately targeting the top 25% percentile of the available catalog to estimate remaining potential.

## Usage / Execution

To execute the algorithm leveraging Simulated Annealing, specify the target input JSON using the `--input` flag:

```bash
python main.py --input data/input/australia.json
```

You can optionally explicitly define the number of SA iterations to perform if you wish to allow the algorithm more time to explore (Default is 5000):
```bash
python main.py --input data/input/australia.json --iterations 15000
```

The application will immediately establish the baseline schedule via Beam Search, subsequently apply intense optimizations using the Simulated Annealing engine, track the best global score across all perturbations, and save the final optimized solution directly into the `data/output/` directory natively.
