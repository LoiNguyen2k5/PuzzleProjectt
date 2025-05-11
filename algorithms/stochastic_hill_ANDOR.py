import random
import math # Không cần math cho stochastic hill climbing đơn giản
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

def solve(start_state: State, goal_state: State, max_iterations=10000, max_restarts=20) -> Optional[List[State]]:
    """
    Giải 8-Puzzle bằng Stochastic Hill Climbing với di chuyển kép.
    Chọn ngẫu nhiên trong số các hàng xóm tốt hơn.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if not is_solvable(start_state, goal_state):
        print("Stochastic Hill (Double): Trạng thái không giải được.")
        return None

    best_state_overall = start_state
    best_score_overall = manhattan_distance(start_state, goal_state)
    overall_path = []

    for restart in range(max_restarts):
        if restart == 0:
            current_state = start_state
        else:
             # Khởi động lại ngẫu nhiên hoặc từ điểm tốt nhất
             if random.random() < 0.6 and best_score_overall < manhattan_distance(start_state, goal_state):
                 current_state = best_state_overall
             else:
                 current_state = start_state # Luôn có thể quay lại trạng thái ban đầu

        current_score = manhattan_distance(current_state, goal_state)
        path = [current_state]
        local_visited = {current_state} # Tránh vòng lặp

        iterations = 0
        stuck_counter = 0
        while current_state != goal_state and iterations < max_iterations:
            iterations += 1
            # Lấy hàng xóm (bao gồm di chuyển kép)
            neighbors = get_neighbors_with_double_moves(current_state)
            uphill_neighbors = [] # Danh sách các hàng xóm tốt hơn (heuristic thấp hơn)

            # Tìm tất cả các hàng xóm tốt hơn chưa thăm
            for neighbor in neighbors:
                 if neighbor not in local_visited:
                      neighbor_score = manhattan_distance(neighbor, goal_state)
                      if neighbor_score < current_score:
                           uphill_neighbors.append(neighbor)

            next_state = None
            if uphill_neighbors:
                 # Chọn ngẫu nhiên một trong số các hàng xóm tốt hơn
                 next_state = random.choice(uphill_neighbors)
                 stuck_counter = 0
            else:
                 # Bị kẹt, không có hàng xóm nào tốt hơn
                 stuck_counter += 1
                 if stuck_counter > 10 : # Thoát nếu bị kẹt quá lâu
                      break
                 # Tùy chọn: thực hiện bước đi ngẫu nhiên để thoát kẹt
                 unvisited = [n for n in neighbors if n not in local_visited]
                 if unvisited:
                     next_state = random.choice(unvisited)
                 else:
                     break # Không còn nước đi

            if next_state is None:
                 break

            # Di chuyển đến trạng thái đã chọn
            current_state = next_state
            current_score = manhattan_distance(current_state, goal_state)
            path.append(current_state)
            local_visited.add(current_state)

            # Cập nhật trạng thái/điểm tốt nhất toàn cục
            if current_score < best_score_overall:
                best_state_overall = current_state
                best_score_overall = current_score

            # Kiểm tra mục tiêu
            if current_state == goal_state:
                # print(f"Stochastic Hill (Double): Found goal in restart {restart+1}.")
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
        # print(f"Stochastic Hill (Double): Did not reach goal. Best score: {best_score_overall}")
        # return overall_path # Tùy chọn trả về đường đi tốt nhất
        return None
