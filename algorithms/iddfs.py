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

def reconstruct_path(state, parent):
    path = []
    while state is not None:
        path.append(state)
        state = parent[state]
    path.reverse()
    return path

def depth_limited_dfs(start_state, goal_state, max_depth, visited, parent, depth):
    stack = [(start_state, 0)]
    while stack:
        current, curr_depth = stack.pop()
        if curr_depth > max_depth:
            continue
        if current == goal_state:
            return reconstruct_path(current, parent)
        if current not in visited:
            visited.add(current)
            for next_state in get_neighbors(current):
                if next_state not in visited:
                    parent[next_state] = current
                    stack.append((next_state, curr_depth + 1))
    return None

def solve(start_state, goal_state, max_depth=20):
    for depth in range(max_depth + 1):
        visited = set()
        parent = {start_state: None}
        result = depth_limited_dfs(start_state, goal_state, depth, visited, parent, 0)
        if result is not None:
            return result
    return None