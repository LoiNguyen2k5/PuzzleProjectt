from heapq import heappush, heappop
from typing import List, Tuple, Optional, Set, Dict

State = Tuple[int, ...]

# --- Dán hàm get_neighbors_with_costs vào đây ---
def get_neighbors_with_costs(state: State) -> List[Tuple[State, int]]:
    neighbors_with_cost: List[Tuple[State, int]] = []
    added_states: Set[State] = set()
    s_list = list(state)
    try:
        size = int(len(state)**0.5)
        if size * size != len(state): return []
        blank_tile = size * size; blank_index = s_list.index(blank_tile)
    except (ValueError, TypeError): return []
    row, col = divmod(blank_index, size); moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    single_move_intermediates: List[Tuple[State, int]] = []
    for dr, dc in moves: # Single moves (cost 1)
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < size and 0 <= new_col < size:
            new_index = new_row * size + new_col; new_s = s_list[:]; new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbor_state = tuple(new_s)
            if neighbor_state not in added_states:
                 neighbors_with_cost.append((neighbor_state, 1)); added_states.add(neighbor_state)
            single_move_intermediates.append((neighbor_state, new_index))
    for intermediate_state, intermediate_blank_index in single_move_intermediates: # Double moves (cost 2)
        s_intermediate = list(intermediate_state); row1, col1 = divmod(intermediate_blank_index, size)
        for dr, dc in moves:
            new_row2, new_col2 = row1 + dr, col1 + dc
            if 0 <= new_row2 < size and 0 <= new_col2 < size:
                new_index2 = new_row2 * size + new_col2
                if new_index2 == blank_index: continue
                new_s2 = s_intermediate[:]; new_s2[intermediate_blank_index], new_s2[new_index2] = new_s2[new_index2], new_s2[intermediate_blank_index]
                neighbor2_state = tuple(new_s2)
                if neighbor2_state not in added_states: # Chỉ thêm nếu chưa có trong KQ
                    neighbors_with_cost.append((neighbor2_state, 2)); added_states.add(neighbor2_state)
    return neighbors_with_cost
# --- Kết thúc hàm get_neighbors_with_costs ---

def reconstruct_path(state: State, parent: Dict[State, Optional[State]]) -> List[State]:
    # ... (Giữ nguyên hàm reconstruct_path) ...
    path: List[State] = []
    current: Optional[State] = state
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path

def solve(start_state: State, goal_state: State) -> Optional[List[State]]:
    """
    Giải 8-Puzzle bằng Uniform Cost Search (UCS) với di chuyển kép có chi phí.
    Tìm đường đi có tổng chi phí (1 cho đơn, 2 cho kép) thấp nhất.

    Args:
        start_state (tuple): Trạng thái bắt đầu.
        goal_state (tuple): Trạng thái đích.

    Returns:
        list: Đường đi tối ưu về chi phí (list các tuple trạng thái) nếu tìm thấy, None nếu không.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    # Hàng đợi ưu tiên lưu trữ (current_cost, state)
    pq: List[Tuple[int, State]] = [(0, start_state)]

    # Dictionary lưu chi phí thấp nhất đã biết để đến mỗi trạng thái
    costs: Dict[State, int] = {start_state: 0}
    # Dictionary lưu trạng thái cha để dựng lại đường đi
    parent: Dict[State, Optional[State]] = {start_state: None}

    # Set các trạng thái đã được lấy ra khỏi pq và xử lý hoàn toàn (tối ưu hóa)
    # closed_set: Set[State] = set() # Không hoàn toàn cần thiết cho UCS chuẩn, nhưng có thể giúp

    while pq:
        # Lấy trạng thái có chi phí thấp nhất từ hàng đợi
        current_cost, current_state = heappop(pq)

        # Nếu đã tìm thấy đường đi tốt hơn đến trạng thái này trước đó, bỏ qua
        # (Điều này xảy ra nếu cùng 1 trạng thái được thêm vào pq nhiều lần với chi phí khác nhau)
        if current_cost > costs.get(current_state, float('inf')):
            continue

        # Nếu đã đến đích, trả về đường đi
        if current_state == goal_state:
            return reconstruct_path(goal_state, parent)

        # Đánh dấu đã xử lý (nếu dùng closed_set)
        # closed_set.add(current_state)

        # Khám phá các hàng xóm (lấy cả trạng thái và chi phí di chuyển)
        for next_state, move_cost in get_neighbors_with_costs(current_state):
            # Tính chi phí mới để đến trạng thái hàng xóm
            new_cost = current_cost + move_cost

            # Nếu tìm thấy đường đi mới hoặc đường đi tốt hơn đến next_state
            if new_cost < costs.get(next_state, float('inf')):
                # Cập nhật chi phí và cha
                costs[next_state] = new_cost
                parent[next_state] = current_state
                # Thêm vào hàng đợi ưu tiên với chi phí mới
                heappush(pq, (new_cost, next_state))

    # Không tìm thấy giải pháp
    return None
