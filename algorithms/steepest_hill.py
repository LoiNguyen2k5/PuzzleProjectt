import random

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

def is_solvable(state, goal_state=(1, 2, 3, 4, 5, 6, 7, 8, 9)):
    state_list = [x for x in state if x != 9]
    inversions = 0
    for i in range(len(state_list)):
        for j in range(i + 1, len(state_list)):
            if state_list[i] > state_list[j]:
                inversions += 1
    blank_row_state = state.index(9) // 3
    blank_row_goal = goal_state.index(9) // 3
    parity_state = inversions % 2
    parity_blank = (blank_row_state - blank_row_goal) % 2
    return parity_state == parity_blank

def solve(start_state, goal_state, max_iterations=1000, max_restarts=50):
    if not is_solvable(start_state, goal_state):
        return None
    
    best_state_overall = start_state
    best_score_overall = manhattan_distance(start_state, goal_state)
    overall_path = []
    
    for restart in range(max_restarts):
        if restart == 0:
            current_state = start_state
        else:
            if random.random() < 0.7 and best_score_overall < manhattan_distance(start_state, goal_state):
                current_state = best_state_overall
            else:
                current_state = start_state
        
        current_score = manhattan_distance(current_state, goal_state)
        path = [current_state]
        visited = set([current_state])
        
        iterations = 0
        stuck_count = 0
        
        while current_state != goal_state and iterations < max_iterations:
            iterations += 1
            neighbors = get_neighbors(current_state)
            best_neighbor = None
            best_neighbor_score = float('inf')
            neighbor_scores = []
            
            for neighbor in neighbors:
                if neighbor not in visited:
                    score = manhattan_distance(neighbor, goal_state)
                    neighbor_scores.append((neighbor, score))
            
            neighbor_scores.sort(key=lambda x: x[1])
            if neighbor_scores:
                best_neighbor, best_neighbor_score = neighbor_scores[0]
            else:
                best_neighbor = None
                best_neighbor_score = float('inf')
            
            if best_neighbor is None or best_neighbor_score >= current_score:
                stuck_count += 1
                if stuck_count >= 3:
                    break
                unvisited_neighbors = [n for n in neighbors if n not in visited]
                if unvisited_neighbors:
                    best_neighbor = random.choice(unvisited_neighbors)
                    best_neighbor_score = manhattan_distance(best_neighbor, goal_state)
                else:
                    break
            else:
                stuck_count = 0
            
            current_state = best_neighbor
            current_score = best_neighbor_score
            path.append(current_state)
            visited.add(current_state)
            
            if current_score < best_score_overall:
                best_state_overall = current_state
                best_score_overall = current_score
            
            if current_state == goal_state:
                return path
        
        if path[-1] != path[0]:
            if not overall_path:
                overall_path = path
            elif manhattan_distance(path[-1], goal_state) < manhattan_distance(overall_path[-1], goal_state):
                overall_path = path
    
    if overall_path and len(overall_path) > 1:
        return overall_path
    return None