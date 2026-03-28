import random
import math
import time
import copy
from typing import List, Set, Optional, Tuple
from models.instance_data import InstanceData
from models.solution import Solution
from models.schedule import Schedule
from models.program import Program
from scheduler.beam_search_scheduler import BeamSearchScheduler
from utils.utils import Utils
from utils.algorithm_utils import AlgorithmUtils
from validator.validator import Validator

class SimulatedAnnealingScheduler:
    def __init__(self, instance_data: InstanceData, 
                 initial_temp: Optional[float] = None, 
                 cooling_rate: Optional[float] = None, 
                 max_iterations: int = 20000,
                 verbose: bool = True):

        self.instance_data = instance_data
        self.max_iterations = max_iterations
        self.verbose = verbose
        
        # Adaptive parameters:
        # For small instances (Germany), use lower T and faster cooling
        # For large instances (USA), use higher T and slower cooling
        self.n_progs = sum(len(ch.programs) for ch in instance_data.channels)
        
        if initial_temp is None:
            if self.n_progs < 1000: # Small
                self.initial_temp = 50.0
            else: # Large
                self.initial_temp = 500.0
        else:
            self.initial_temp = initial_temp
            
        if cooling_rate is None:
            # We want T to reach ~0.01 at the end of max_iterations
            # T_end = T_start * (cooling_rate ^ iterations)
            # cooling_rate = (T_end / T_start) ^ (1 / iterations)
            target_end_temp = 0.05
            self.cooling_rate = (target_end_temp / self.initial_temp) ** (1.0 / self.max_iterations)
        else:
            self.cooling_rate = cooling_rate

        self.beam_scheduler = BeamSearchScheduler(instance_data, beam_width=100, verbose=False)


    def generate_solution(self) -> Solution:
        # 1. Get initial solution
        if self.verbose:
            print("Generating initial solution using Beam Search...")
        current_solution = self.beam_scheduler.generate_solution()
        best_solution = copy.deepcopy(current_solution)
        
        current_score = current_solution.total_score
        best_score = current_score
        
        temp = self.initial_temp
        
        if self.verbose:
            print(f"Initial Score: {current_score}")
            print(f"Starting SA with T={temp}, cooling={self.cooling_rate}, iterations={self.max_iterations}")

        start_time = time.time()
        
        for i in range(self.max_iterations):
            # 2. Perturb solution (Destroy and Rebuild)
            new_solution = self._perturb(current_solution)
            
            if not new_solution:
                continue
                
            new_score = new_solution.total_score
            
            # 3. Acceptance Criteria
            delta = new_score - current_score
            if delta > 0 or random.random() < math.exp(delta / temp):
                current_solution = new_solution
                current_score = new_score
                
                if current_score > best_score:
                    best_solution = copy.deepcopy(current_solution)
                    best_score = current_score
                    if self.verbose:
                        print(f"Iteration {i}: New Best Score: {best_score:.2f} (T={temp:.4f})")
            
            # 4. Cooling
            temp *= self.cooling_rate
            
            # Safety timeout or early exit if needed
            if i % 1000 == 0 and self.verbose:
                elapsed = time.time() - start_time
                print(f"Iteration {i}... Current Best: {best_score:.2f} (Elapsed: {elapsed:.1f}s)")

        if self.verbose:
            print(f"SA Finished. Total Score: {best_score:.2f}")
            
        return best_solution

    def _perturb(self, solution: Solution) -> Optional[Solution]:
        """Apply a random operator to the solution."""
        operator = random.choice([
            self._destroy_and_rebuild,
            self._large_neighborhood_search,
            self._channel_block_swap,
            lambda sol: self._lns_core(sol, destroy_type='targeted')
        ])

        return operator(solution)

    def _destroy_and_rebuild(self, solution: Solution) -> Optional[Solution]:
        """Remove a random segment and re-fill."""
        return self._lns_core(solution, destroy_type='segment')

    def _large_neighborhood_search(self, solution: Solution) -> Optional[Solution]:
        """Remove a larger chunk of programs."""
        return self._lns_core(solution, destroy_type='large')

    def _channel_block_swap(self, solution: Solution) -> Optional[Solution]:
        """Try to swap to a different channel for a period."""
        return self._lns_core(solution, destroy_type='channel')

    def _lns_core(self, solution: Solution, destroy_type: str) -> Optional[Solution]:
        if not solution.scheduled_programs:
            return None
            
        progs = solution.scheduled_programs
        
        if destroy_type == 'segment':
            max_destroy = min(5, len(progs))
            destroy_size = random.randint(1, max_destroy)
            start_idx = random.randint(0, len(progs) - destroy_size)
        elif destroy_type == 'large':
            destroy_size = random.randint(min(5, len(progs)), min(15, len(progs)))
            start_idx = random.randint(0, len(progs) - destroy_size)
        elif destroy_type == 'targeted':
            # Remove the programs with lowest fitness
            # Actually remove a window around the lowest fitness program
            lowest_idx = min(range(len(progs)), key=lambda i: progs[i].fitness)
            destroy_size = random.randint(1, 10)
            start_idx = max(0, lowest_idx - destroy_size // 2)
            destroy_size = min(destroy_size, len(progs) - start_idx)
        elif destroy_type == 'channel':
            ch_ids = list(set(p.channel_id for p in progs))
            target_ch = random.choice(ch_ids)
            indices = [i for i, p in enumerate(progs) if p.channel_id == target_ch]
            if not indices: return self._lns_core(solution, 'segment')
            start_idx = indices[0]
            destroy_size = random.randint(1, len(progs) - start_idx)
        else:
            start_idx = random.randint(0, len(progs) - 1)
        
        prefix = progs[:start_idx]
        current_time = prefix[-1].end if prefix else self.instance_data.opening_time
        
        new_progs = list(prefix)
        used_progs = {p.unique_program_id for p in new_progs}
        
        prev_ch = prefix[-1].channel_id if prefix else None
        prev_genre = ""
        g_streak = 0
        if prefix:
            last_p_id = prefix[-1].unique_program_id
            prog_info = self.beam_scheduler.prog_by_id.get(last_p_id)
            if prog_info:
                prev_genre = prog_info[0].genre
                for j in range(len(prefix)-1, -1, -1):
                    p_info = self.beam_scheduler.prog_by_id.get(prefix[j].unique_program_id)
                    if p_info and p_info[0].genre == prev_genre:
                        g_streak += 1
                    else:
                        break

        time_limit = self.instance_data.closing_time
        
        # Randomize the density heuristic slightly for each rebuild
        rebuild_density = self.beam_scheduler.avg_score_per_min * random.uniform(0.8, 1.2)

        # Mini-beam reconstruction
        beam_width = 3 if self.n_progs < 1000 else 5

        
        # State: (score, current_time, prev_ch, prev_genre, g_streak, used_progs, list_of_scheduled)
        beam = [(0.0, current_time, prev_ch, prev_genre, g_streak, set(used_progs), [])]
        
        while any(b[1] < time_limit for b in beam):
            new_beam = []
            for score, t, p_ch, p_genre, gs, used, scheduled in beam:
                if t >= time_limit:
                    new_beam.append((score, t, p_ch, p_genre, gs, used, scheduled))
                    continue
                
                candidates = self.beam_scheduler._get_candidates(t, p_ch, p_genre, gs, used)
                if not candidates:
                    idx = bisect_right(self.beam_scheduler.times, t)
                    if idx < len(self.beam_scheduler.times):
                        new_beam.append((score, self.beam_scheduler.times[idx], p_ch, p_genre, gs, used, scheduled))
                    else:
                        new_beam.append((score, time_limit, p_ch, p_genre, gs, used, scheduled))
                    continue
                
                # Sort candidates by randomized density
                candidates.sort(key=lambda x: x[0] + (time_limit - x[5]) * rebuild_density * random.uniform(0.9, 1.1), reverse=True)
                
                for cand in candidates[:beam_width]:
                    c_score, ch_idx, ch_id, prog, c_start, c_end = cand
                    new_used = set(used)
                    new_used.add(prog.unique_id)
                    
                    new_gs = gs + 1 if prog.genre == p_genre else 1
                    new_scheduled = scheduled + [Schedule(
                        program_id=prog.program_id,
                        channel_id=ch_id,
                        start=c_start,
                        end=c_end,
                        fitness=c_score,
                        unique_program_id=prog.unique_id
                    )]
                    
                    new_beam.append((score + c_score, c_end, ch_id, prog.genre, new_gs, new_used, new_scheduled))
            
            # Keep top W
            new_beam.sort(key=lambda x: x[0], reverse=True)
            beam = new_beam[:beam_width]
            
            # Break if no progress
            if not beam: break

        best_rebuild = beam[0]
        new_progs.extend(best_rebuild[6])
        current_time = best_rebuild[1]


        total_score = sum(p.fitness for p in new_progs)
        return Solution(new_progs, total_score)


from bisect import bisect_right
