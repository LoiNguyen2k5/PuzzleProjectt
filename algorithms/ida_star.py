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

def is_solvable(state, goal_state):
    state_list = [num for num in state if num != 9]
    goal_list = [num for num in goal_state if num != 9]
    state_inversions = sum(1 for i in range(len(state_list)) for j in range(i + 1, len(state_list)) if state_list[i] > state_list[j])
    goal_inversions = sum(1 for i in range(len(goal_list)) for j in range(i + 1, len(goal_list)) if goal_list[i] > goal_list[j])
    return state_inversions % 2 == goal_inversions % 2

def reconstruct_path(state, parent):
    path = []
    while state is not None:
        path.append(state)
        state = parent[state]
    path.reverse()
    return path

def search(state, goal_state, g_value, threshold, parent, visited, min_f_value):
    f_value = g_value + manhattan_distance(state, goal_state)
    if f_value > threshold:
        min_f_value[0] = min(min_f_value[0], f_value)
        return None
    if state == goal_state:
        return state
    visited.add(state)
    for next_state in get_neighbors(state):
        if next_state not in visited:
            parent[next_state] = state
            result = search(next_state, goal_state, g_value + 1, threshold, parent, visited, min_f_value)
            if result is not None:
                return result
    visited.remove(state)
    return None

def solve(start_state, goal_state):
    if not is_solvable(start_state, goal_state):
        return None
    threshold = manhattan_distance(start_state, goal_state)
    parent = {start_state: None}
    while threshold < 100:
        min_f_value = [float('inf')]
        visited = set()
        result = search(start_state, goal_state, 0, threshold, parent, visited, min_f_value)
        if result is not None:
            return reconstruct_path(result, parent)
        if min_f_value[0] == float('inf'):
            return None
        threshold = min_f_value[0]
    return None