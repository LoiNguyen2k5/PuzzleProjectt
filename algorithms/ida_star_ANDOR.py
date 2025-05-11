from typing import List, Tuple, Optional, Set, Dict
import sys

# Tăng giới hạn đệ quy nếu cần cho các bài toán khó
# sys.setrecursionlimit(3000)

State = Tuple[int, ...]

def manhattan_distance(state: State, goal_state: State) -> int:
    # ... (Giữ nguyên hàm manhattan_distance) ...
    total = 0
    try:
        size = int(len(state)**0.5)
        if size * size != len(state) or len(goal_state) != len(state): return float('inf')
        blank_tile = size * size
        goal_map = {tile: i for i, tile in enumerate(goal_state)}
    except (ValueError, TypeError): return float('inf')

    for i in range(len(state)):
        tile = state[i]
        if tile != blank_tile:
            curr_row, curr_col = divmod(i, size)
            goal_pos = goal_map.get(tile)
            if goal_pos is None: return float('inf')
            goal_row, goal_col = divmod(goal_pos, size)
            total += abs(curr_row - goal_row) + abs(curr_col - goal_col)
    return total

# --- Dán hàm get_neighbors_with_double_moves vào đây ---
def get_neighbors_with_double_moves(state: State) -> List[State]:
    neighbors: Set[State] = set(); s_list = list(state)
    try:
        size = int(len(state)**0.5);
        if size * size != len(state): return []
        blank_tile = size * size; blank_index = s_list.index(blank_tile)
    except (ValueError, TypeError): return []
    row, col = divmod(blank_index, size); moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    single_move_intermediates: List[Tuple[State, int]] = []
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < size and 0 <= new_col < size:
            new_index = new_row * size + new_col; new_s = s_list[:]; new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbor_state = tuple(new_s); neighbors.add(neighbor_state); single_move_intermediates.append((neighbor_state, new_index))
    for intermediate_state, intermediate_blank_index in single_move_intermediates:
        s_intermediate = list(intermediate_state); row1, col1 = divmod(intermediate_blank_index, size)
        for dr, dc in moves:
            new_row2, new_col2 = row1 + dr, col1 + dc
            if 0 <= new_row2 < size and 0 <= new_col2 < size:
                new_index2 = new_row2 * size + new_col2
                if new_index2 == blank_index: continue
                new_s2 = s_intermediate[:]; new_s2[intermediate_blank_index], new_s2[new_index2] = new_s2[new_index2], new_s2[intermediate_blank_index]
                neighbor2_state = tuple(new_s2); neighbors.add(neighbor2_state)
    return list(neighbors)
# --- Kết thúc hàm get_neighbors_with_double_moves ---

def reconstruct_path(state: State, parent: Dict[State, Optional[State]]) -> List[State]:
    # ... (Giữ nguyên hàm reconstruct_path) ...
    path: List[State] = []
    current: Optional[State] = state
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path

# Hàm tìm kiếm đệ quy cho IDA*
def search(current_state: State, goal_state: State, g_cost: int, threshold: int, path: List[State], visited_in_path: Set[State]) -> Tuple[Optional[List[State]], int]:
    """
    Hàm tìm kiếm đệ quy giới hạn bởi ngưỡng f_cost.

    Args:
        current_state: Trạng thái hiện tại.
        goal_state: Trạng thái đích.
        g_cost: Chi phí thực tế từ trạng thái bắt đầu đến trạng thái hiện tại (số hành động).
        threshold: Ngưỡng f_cost = g_cost + h_cost hiện tại.
        path: Danh sách các trạng thái trên đường đi hiện tại.
        visited_in_path: Set các trạng thái trong đường đi hiện tại để tránh chu trình.

    Returns:
        Tuple: (Danh sách đường đi nếu tìm thấy đích, hoặc None, ngưỡng f_cost nhỏ nhất vượt quá threshold)
    """
    h_cost = manhattan_distance(current_state, goal_state)
    f_cost = g_cost + h_cost

    # Nếu chi phí ước tính vượt ngưỡng, dừng nhánh này và trả về f_cost đó
    if f_cost > threshold:
        return None, f_cost

    # Nếu tìm thấy đích
    if current_state == goal_state:
        return path, f_cost # Trả về đường đi và f_cost cuối cùng

    min_f_cost_over_threshold = float('inf')

    # Mở rộng hàng xóm (bao gồm di chuyển kép)
    neighbors = get_neighbors_with_double_moves(current_state)
    # Sắp xếp hàng xóm theo heuristic có thể giúp tìm đích nhanh hơn (tùy chọn)
    neighbors.sort(key=lambda s: manhattan_distance(s, goal_state))

    for next_state in neighbors:
        # Chỉ đi tiếp nếu trạng thái chưa có trong đường đi hiện tại (tránh chu trình)
        if next_state not in visited_in_path:
            path.append(next_state)
            visited_in_path.add(next_state)

            # Gọi đệ quy cho trạng thái tiếp theo
            # g_cost tăng 1 vì mỗi bước (đơn hoặc kép) được coi là 1 hành động
            found_path, next_min_f = search(next_state, goal_state, g_cost + 1, threshold, path, visited_in_path)

            # Nếu tìm thấy đường đi từ lời gọi đệ quy, trả về ngay lập tức
            if found_path:
                return found_path, threshold # Trả về threshold hiện tại khi tìm thấy

            # Cập nhật ngưỡng f_cost nhỏ nhất vượt quá threshold hiện tại
            min_f_cost_over_threshold = min(min_f_cost_over_threshold, next_min_f)

            # Backtrack: Xóa trạng thái khỏi đường đi và visited_in_path
            path.pop()
            visited_in_path.remove(next_state)

    # Nếu không tìm thấy đích trong nhánh này, trả về ngưỡng f nhỏ nhất đã gặp
    return None, min_f_cost_over_threshold

def is_solvable(state, goal_state=(1, 2, 3, 4, 5, 6, 7, 8, 9)):
     # ... (Copy hàm is_solvable từ hill_climbing_ANDOR.py) ...
    try:
        state_list = [x for x in state if x != 9]; goal_list = [x for x in goal_state if x != 9]
        if len(state_list) != 8 or len(goal_list) != 8: return False
        inversions = 0
        for i in range(len(state_list)):
            for j in range(i + 1, len(state_list)):
                if state_list[i] > state_list[j]: inversions += 1
        goal_inversions = 0
        for i in range(len(goal_list)):
            for j in range(i + 1, len(goal_list)):
                if goal_list[i] > goal_list[j]: goal_inversions += 1
        return (inversions % 2) == (goal_inversions % 2)
    except: return False

def solve(start_state: State, goal_state: State) -> Optional[List[State]]:
    """
    Giải 8-Puzzle bằng IDA* với di chuyển kép.

    Args:
        start_state (tuple): Trạng thái bắt đầu.
        goal_state (tuple): Trạng thái đích.

    Returns:
        list: Đường đi tối ưu về số hành động (list các tuple trạng thái) nếu tìm thấy, None nếu không.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if not is_solvable(start_state, goal_state):
         print("IDA* (Double): Trạng thái không giải được.")
         return None

    # Ngưỡng f_cost ban đầu là heuristic của trạng thái bắt đầu
    threshold = manhattan_distance(start_state, goal_state)

    if threshold == float('inf'):
         print("IDA* (Double): Lỗi tính heuristic ban đầu.")
         return None
    if threshold == 0 and start_state == goal_state:
         return [start_state]

    iteration = 0
    max_iterations = 100 # Giới hạn số lần tăng ngưỡng để tránh chạy quá lâu

    while iteration < max_iterations :
        iteration += 1
        # print(f"IDA* (Double): Iteration {iteration}, Threshold = {threshold}")

        # Bắt đầu tìm kiếm với ngưỡng hiện tại
        path = [start_state]
        visited_in_path = {start_state} # Chỉ cần theo dõi visited trong đường đi hiện tại cho mỗi lần search
        found_path, next_threshold = search(start_state, goal_state, 0, threshold, path, visited_in_path)

        # Nếu tìm thấy đường đi, trả về
        if found_path:
            # print(f"IDA* (Double): Found solution with threshold {threshold}.")
            return found_path

        # Nếu next_threshold là vô cực, nghĩa là không có nút nào có thể mở rộng -> không có giải pháp
        if next_threshold == float('inf'):
            # print("IDA* (Double): No solution found (search space exhausted).")
            return None

        # Nếu không tìm thấy, cập nhật ngưỡng cho lần lặp tiếp theo
        threshold = next_threshold

    print(f"IDA* (Double): No solution found within {max_iterations} iterations.")
    return None # Không tìm thấy giải pháp sau giới hạn lần lặp
