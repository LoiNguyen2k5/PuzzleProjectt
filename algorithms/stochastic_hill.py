import random
import math

def manhattan_distance(state, goal_state):
    total = 0
    for i in range(9):
        if state[i] != 9:
            curr_row, curr_col = divmod(i, 3)
            goal_pos = goal_state.index(state[i])
            goal_row, goal_col = divmod(goal_pos, 3)
            total += abs(curr_row - goal_row) + abs(curr_col - goal_col)
    return total

def get_neighbors(state):
    neighbors = []
    s = list(state)
    blank_index = s.index(9)
    row, col = divmod(blank_index, 3)
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in moves:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_index = new_row * 3 + new_col
            new_s = s[:]
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbors.append(tuple(new_s))
    return neighbors

def solve(start_state, goal_state, max_iterations=10000, temperature=10.0, cooling_rate=0.995):
    current_state = start_state
    current_score = manhattan_distance(current_state, goal_state)
    path = [current_state]
    visited = set([current_state])
    iterations = 0
    current_temp = temperature
    
    best_state = current_state
    best_score = current_score
    no_improvement_count = 0
    
    while current_state != goal_state and iterations < max_iterations:
        iterations += 1
        neighbors = get_neighbors(current_state)
        if not neighbors:
            break
        next_state = random.choice(neighbors)
        next_score = manhattan_distance(next_state, goal_state)
        delta = current_score - next_score
        if delta > 0 or random.random() < math.exp(delta / current_temp):
            current_state = next_state
            current_score = next_score
            path.append(current_state)
            visited.add(current_state)
            if current_score < best_score:
                best_state = current_state
                best_score = current_score
                no_improvement_count = 0
            else:
                no_improvement_count += 1
        current_temp *= cooling_rate
        
        if no_improvement_count > 100:
            current_state = best_state
            current_score = best_score
            current_temp = temperature * 0.5
            no_improvement_count = 0
        
        if current_state == goal_state:
            return path
    
    return None