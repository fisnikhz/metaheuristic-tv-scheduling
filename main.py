from parser.file_selector import select_file
from parser.parser import Parser
from serializer.serializer import SolutionSerializer
from scheduler.beam_search_scheduler import BeamSearchScheduler
from scheduler.simulated_annealing_scheduler import SimulatedAnnealingScheduler
from utils.utils import Utils
import argparse
import os
import json


def main():
    parser_arg = argparse.ArgumentParser(description="Run TV scheduling algorithms")
    parser_arg.add_argument("--input", "-i", dest="input_file", help="Path to input JSON (optional)")
    parser_arg.add_argument("--iterations", type=int, default=5000, help="Number of SA iterations")
    parser_arg.add_argument("--target", type=float, help="Explicit target score to beat")

    
    args = parser_arg.parse_args()
    
    if args.input_file:
        file_path = args.input_file
    else:
        file_path = select_file()
        
    parser = Parser(file_path)
    instance = parser.parse()
    Utils.set_current_instance(instance)

    # Establish baseline score to beat using current BeamSearch
    print(f"Establishing baseline score for {file_path}...")
    baseline_scheduler = BeamSearchScheduler(instance, beam_width=100, verbose=False)
    baseline_sol = baseline_scheduler.generate_solution()
    target_score = baseline_sol.total_score
    
    print(f"Baseline Score (Beam Search): {target_score}")
    
    if args.target:
        target_score = max(target_score, args.target)
    
    # Define base_name first
    base_name = os.path.basename(file_path).lower()

    # Target mapping from user spreadsheet
    spreadsheet_targets = {
        "australia": 4117.0,
        "france": 4370.0,
        "spain": 4555.0,
        "uk": 5192.0,
        "china": 2861.0,
        "canada": 4628.0,
        "youtube_gold": 101808.0,
        "youtube_premium": 64093.0,
        "kosovo": 2587.0,
        "usa": 3601.0,
        "singapore": 4316.0,
        "us_iptv": 4361.0
    }

    # Match target from spreadsheet if available
    for key, val in spreadsheet_targets.items():
        if key in base_name:
            target_score = max(target_score, val)
            break

    # Specific override for germany
    if "germany" in base_name:
        target_score = max(target_score, 1553.0)


    print(f"Target score to beat: {target_score}")



    print(f"\nRunning Simulated Annealing optimization (iter={args.iterations})...")
    scheduler = SimulatedAnnealingScheduler(
        instance_data=instance,
        max_iterations=args.iterations,
        verbose=True
    )

    solution = scheduler.generate_solution()
    
    if solution.total_score > target_score:
        print(f"\nSTRICT IMPROVEMENT ACHIEVED! {solution.total_score} > {target_score}")
        algorithm_name = "simulatedannealing"
        serializer = SolutionSerializer(input_file_path=file_path, algorithm_name=algorithm_name)
        serializer.serialize(solution)
        print(f"✓ Solution saved to output file")
        exit(0)
    else:
        print(f"\nNo improvement: {solution.total_score} <= {target_score}.")
        exit(1)


if __name__ == "__main__":
    main()

