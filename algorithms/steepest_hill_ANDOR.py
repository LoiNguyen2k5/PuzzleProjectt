import random
from typing import List, Tuple, Optional, Set, Dict

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

def solve(start_state: State, goal_state: State, max_iterations=1000, max_restarts=50) -> Optional[List[State]]:
    """
    Giải 8-Puzzle bằng Steepest Ascent Hill Climbing với di chuyển kép.
    Luôn chọn nước đi có cải thiện heuristic lớn nhất.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if not is_solvable(start_state, goal_state):
        print("Steepest Hill (Double): Trạng thái không giải được.")
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
        local_visited = {current_state} # Tránh vòng lặp cục bộ

        iterations = 0
        while current_state != goal_state and iterations < max_iterations:
            iterations += 1
            # Lấy hàng xóm (bao gồm di chuyển kép)
            neighbors = get_neighbors_with_double_moves(current_state)
            best_neighbor = None
            # Khởi tạo điểm tốt nhất bằng điểm hiện tại để chỉ chấp nhận cải thiện
            best_neighbor_score = current_score

            # Tìm hàng xóm có điểm heuristic thấp nhất (cải thiện nhiều nhất)
            candidates = []
            for neighbor in neighbors:
                 if neighbor not in local_visited:
                      score = manhattan_distance(neighbor, goal_state)
                      # Chỉ xem xét những hàng xóm thực sự tốt hơn
                      if score < best_neighbor_score:
                           candidates.append((neighbor, score))

            if candidates:
                 # Sắp xếp các ứng viên tốt hơn và chọn cái tốt nhất (steepest ascent)
                 candidates.sort(key=lambda x: x[1])
                 best_neighbor, best_neighbor_score = candidates[0]
            else:
                 # Không tìm thấy hàng xóm nào tốt hơn -> Bị kẹt ở local optimum/plateau
                 break # Dừng lần chạy này

            # Di chuyển đến trạng thái tốt nhất tìm được
            current_state = best_neighbor
            current_score = best_neighbor_score
            path.append(current_state)
            local_visited.add(current_state)

            # Cập nhật trạng thái/điểm tốt nhất toàn cục
            if current_score < best_score_overall:
                best_state_overall = current_state
                best_score_overall = current_score

            # Kiểm tra mục tiêu
            if current_state == goal_state:
                # print(f"Steepest Hill (Double): Found goal in restart {restart+1}.")
                return path

        # Cập nhật đường đi tổng thể nếu lần chạy này tốt hơn
        if current_state != goal_state and path:
             if not overall_path or current_score < manhattan_distance(overall_path[-1], goal_state):
                  overall_path = path

    # Sau tất cả các lần khởi động lại
    if best_score_overall == 0 and overall_path and overall_path[-1] == goal_state:
        return overall_path
    elif best_score_overall == 0 and not overall_path:
        return [start_state] # start == goal
    else:
        # print(f"Steepest Hill (Double): Did not reach goal. Best score: {best_score_overall}")
        # return overall_path # Có thể trả về đường đi tốt nhất dù không phải đích
        return None # Hoặc chỉ trả về None nếu không đạt đích
