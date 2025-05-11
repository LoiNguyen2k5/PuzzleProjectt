import random
from typing import List, Tuple, Optional, Set, Dict

State = Tuple[int, ...]

def manhattan_distance(state: State, goal_state: State) -> int:
    # ... (Giữ nguyên hàm manhattan_distance từ file gốc) ...
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
     # ... (Giữ nguyên hàm is_solvable từ file gốc nếu có) ...
     # Đảm bảo dùng logic kiểm tra tính giải được phù hợp với 3x3
    try:
        state_list = [x for x in state if x != 9]
        goal_list = [x for x in goal_state if x != 9] # Cần goal nếu khác chuẩn
        if len(state_list) != 8 or len(goal_list) != 8: return False # Chỉ cho 3x3

        inversions = 0
        for i in range(len(state_list)):
            for j in range(i + 1, len(state_list)):
                if state_list[i] > state_list[j]:
                    inversions += 1

        # Logic cho 3x3: tính chẵn lẻ của số nghịch thế
        # Nếu chiều rộng là lẻ (như 3x3), trạng thái giải được nếu số nghịch thế là chẵn.
        # (Giả định ô trống ở vị trí cuối cùng trong goal_state chuẩn)
        # Nếu goal_state khác, cần xem xét vị trí ô trống. Cách đơn giản nhất:
        # Số nghịch thế của start và goal phải cùng tính chẵn/lẻ.
        goal_inversions = 0
        for i in range(len(goal_list)):
            for j in range(i + 1, len(goal_list)):
                if goal_list[i] > goal_list[j]:
                    goal_inversions += 1
        return (inversions % 2) == (goal_inversions % 2)
    except:
        return False # Lỗi trạng thái

def solve(start_state: State, goal_state: State, max_iterations=1000, max_restarts=50) -> Optional[List[State]]:
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if not is_solvable(start_state, goal_state):
        print("Hill Climbing (Double): Trạng thái không giải được.")
        return None

    best_state_overall = start_state
    best_score_overall = manhattan_distance(start_state, goal_state)
    overall_path = [] # Lưu đường đi tốt nhất tìm thấy

    for restart in range(max_restarts):
        # Chọn điểm bắt đầu cho lần khởi động lại
        if restart == 0:
            current_state = start_state
        else:
            # Khởi động lại ngẫu nhiên hoặc từ trạng thái tốt nhất trước đó
            if random.random() < 0.7 and best_score_overall < manhattan_distance(start_state, goal_state):
                 current_state = best_state_overall # Khởi động lại từ điểm tốt nhất đã biết
            else:
                 # Có thể thêm khởi động lại ngẫu nhiên hoàn toàn nếu muốn, nhưng thường bắt đầu lại từ đầu
                 current_state = start_state

        current_score = manhattan_distance(current_state, goal_state)
        path = [current_state]
        local_visited = {current_state} # Tránh vòng lặp trong một lần chạy hill climbing

        iterations = 0
        stuck_counter = 0 # Đếm số lần bị kẹt (không tìm được nước đi tốt hơn)

        while current_state != goal_state and iterations < max_iterations:
            iterations += 1
            # Lấy neighbors bao gồm cả double moves
            neighbors = get_neighbors_with_double_moves(current_state)
            best_neighbor = None
            best_neighbor_score = current_score # Khởi tạo bằng điểm hiện tại

            # Tìm hàng xóm tốt nhất (heuristic thấp nhất) chưa thăm trong lần chạy này
            candidates = []
            for neighbor in neighbors:
                 if neighbor not in local_visited:
                      score = manhattan_distance(neighbor, goal_state)
                      if score < best_neighbor_score:
                           candidates.append((neighbor, score)) # Thu thập các ứng viên tốt hơn

            if candidates:
                 # Chọn hàng xóm tốt nhất trong số các ứng viên tốt hơn
                 candidates.sort(key=lambda x: x[1])
                 best_neighbor, best_neighbor_score = candidates[0]
                 stuck_counter = 0 # Đặt lại bộ đếm kẹt
            else:
                 # Bị kẹt (không có hàng xóm tốt hơn)
                 stuck_counter += 1
                 if stuck_counter >= 5: # Nếu bị kẹt quá lâu, dừng lần chạy này
                      break
                 # Có thể thực hiện bước đi ngang (sideways move) hoặc ngẫu nhiên nếu muốn
                 # Ở đây chỉ đơn giản là dừng nếu không tìm thấy bước tốt hơn
                 unvisited_neighbors = [n for n in neighbors if n not in local_visited]
                 if unvisited_neighbors:
                     # Chọn ngẫu nhiên một nước đi chưa thăm để thử thoát khỏi local optimum
                     best_neighbor = random.choice(unvisited_neighbors)
                     best_neighbor_score = manhattan_distance(best_neighbor, goal_state)
                 else:
                     break # Không còn nước nào để đi

            # Di chuyển đến trạng thái tiếp theo
            if best_neighbor is None: # Thoát nếu không tìm được nước đi nào
                 break
            current_state = best_neighbor
            current_score = best_neighbor_score
            path.append(current_state)
            local_visited.add(current_state)

            # Cập nhật trạng thái tốt nhất toàn cục nếu cần
            if current_score < best_score_overall:
                best_state_overall = current_state
                best_score_overall = current_score
                # print(f"Restart {restart+1}, Iter {iterations}: New best score {best_score_overall}")

            # Kiểm tra mục tiêu
            if current_state == goal_state:
                # print(f"Hill Climbing (Double): Found goal in restart {restart+1} after {iterations} iterations.")
                return path # Trả về đường đi ngay khi tìm thấy đích

        # Kết thúc một lần chạy, cập nhật đường đi tốt nhất nếu cần
        if current_state != goal_state and path: # Chỉ cập nhật nếu có đường đi và không phải là đích
             if not overall_path or current_score < manhattan_distance(overall_path[-1], goal_state):
                  overall_path = path

    # Sau tất cả các lần khởi động lại
    if best_score_overall == 0 and overall_path and overall_path[-1] == goal_state:
        # Trường hợp tìm thấy đích ở lần chạy cuối cùng
        return overall_path
    elif best_score_overall == 0 and not overall_path:
         # Trường hợp start_state == goal_state
         return [start_state]
    elif overall_path:
        # Trả về đường đi tốt nhất tìm được, dù không phải đích
        # print(f"Hill Climbing (Double): Did not reach goal. Returning best path found with score {best_score_overall}.")
        # return overall_path # Quyết định xem có trả về đường đi không tối ưu không
        return None # Hoặc trả về None nếu chỉ chấp nhận giải pháp hoàn chỉnh
    else:
        # print("Hill Climbing (Double): No solution found after restarts.")
        return None
