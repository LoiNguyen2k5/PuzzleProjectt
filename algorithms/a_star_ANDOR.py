from heapq import heappush, heappop
from typing import List, Tuple, Optional, Dict, Set

# Định nghĩa kiểu dữ liệu cho trạng thái (một tuple các số nguyên)
State = Tuple[int, ...]

def manhattan_distance(state: State, goal_state: State) -> int:
    """
    Tính tổng khoảng cách Manhattan cho tất cả các ô (trừ ô trống)
    đến vị trí mục tiêu của chúng.
    """
    total = 0
    try:
        size = int(len(state)**0.5) # Giả sử là bảng vuông (ví dụ: 3x3)
        if size * size != len(state) or len(goal_state) != len(state):
             # print("Cảnh báo: Trạng thái không hợp lệ cho tính Manhattan distance.")
             return float('inf') # Trạng thái không hợp lệ
        blank_tile = size * size # Giá trị đại diện cho ô trống (ví dụ: 9 cho 3x3)
    except TypeError:
        # print("Cảnh báo: Đầu vào không hợp lệ cho tính Manhattan distance.")
        return float('inf') # Đầu vào không phải dạng list/tuple

    goal_map = {tile: i for i, tile in enumerate(goal_state)} # Tạo map để tra cứu vị trí đích nhanh hơn

    for i in range(len(state)):
        tile = state[i]
        if tile != blank_tile:
            current_row, current_col = divmod(i, size)
            goal_pos = goal_map.get(tile) # Tra cứu vị trí đích

            if goal_pos is None:
                # Ô này không có trong trạng thái đích? Điều này không nên xảy ra với puzzle hợp lệ.
                # print(f"Cảnh báo: Ô {tile} không tìm thấy trong trạng thái mục tiêu.")
                return float('inf') # Trả về vô cực nếu không hợp lệ

            goal_row, goal_col = divmod(goal_pos, size)
            total += abs(current_row - goal_row) + abs(current_col - goal_col)
    return total

def get_neighbors_with_costs(state: State) -> List[Tuple[State, int]]:
    """
    Tạo ra các trạng thái hàng xóm có thể có cùng với chi phí di chuyển.
    - Di chuyển đơn: chi phí 1
    - Di chuyển kép liên tiếp: chi phí 2
    """
    neighbors: List[Tuple[State, int]] = []
    s_list = list(state)
    try:
        size = int(len(state)**0.5)
        if size * size != len(state):
             return [] # Không phải bảng vuông
        blank_tile = size * size
        blank_index = s_list.index(blank_tile)
    except (ValueError, TypeError):
        # print(f"Lỗi: Không tìm thấy ô trống ({blank_tile}) hoặc trạng thái không hợp lệ trong {state}")
        return [] # Trạng thái không hợp lệ hoặc không tìm thấy ô trống

    row, col = divmod(blank_index, size)
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)] # Các hướng di chuyển (dr, dc)

    # --- Di chuyển đơn (chi phí 1) ---
    single_move_intermediates: List[Tuple[State, int]] = [] # Lưu (trạng thái, vị trí ô trống mới)
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < size and 0 <= new_col < size:
            new_index = new_row * size + new_col
            new_s = s_list[:] # Tạo bản sao
            # Hoán đổi ô trống với ô lân cận
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbor_state = tuple(new_s)
            neighbors.append((neighbor_state, 1)) # Thêm hàng xóm với chi phí 1
            single_move_intermediates.append((neighbor_state, new_index))

    # --- Di chuyển kép (chi phí 2) ---
    # Từ mỗi trạng thái trung gian sau 1 bước, thực hiện bước thứ 2
    for intermediate_state, intermediate_blank_index in single_move_intermediates:
        s_intermediate = list(intermediate_state)
        row1, col1 = divmod(intermediate_blank_index, size)
        for dr, dc in moves:
            new_row2, new_col2 = row1 + dr, col1 + dc
            if 0 <= new_row2 < size and 0 <= new_col2 < size:
                new_index2 = new_row2 * size + new_col2
                # Quan trọng: Bước di chuyển thứ hai không được quay lại vị trí ban đầu của ô trống
                if new_index2 == blank_index:
                    continue

                # Tạo trạng thái sau bước di chuyển thứ hai
                new_s2 = s_intermediate[:]
                new_s2[intermediate_blank_index], new_s2[new_index2] = new_s2[new_index2], new_s2[intermediate_blank_index]
                neighbor2_state = tuple(new_s2)
                # Thêm hàng xóm di chuyển kép với chi phí 2
                # Kiểm tra xem trạng thái này đã tồn tại trong neighbors chưa (có thể có chi phí khác)
                # A* sẽ tự xử lý việc chọn chi phí tốt hơn, nên có thể thêm trực tiếp
                neighbors.append((neighbor2_state, 2))

    return neighbors

def reconstruct_path(state: State, parent: Dict[State, Optional[State]]) -> List[State]:
    """
    Xây dựng lại đường đi từ trạng thái đích ngược về trạng thái bắt đầu.
    """
    path: List[State] = []
    current: Optional[State] = state
    while current is not None:
        path.append(current)
        current = parent.get(current) # An toàn hơn nếu current không có trong parent
    path.reverse() # Đảo ngược để có thứ tự từ bắt đầu đến đích
    return path

def solve(start_state: State, goal_state: State) -> Optional[List[State]]:
    """
    Tìm đường đi ngắn nhất từ start_state đến goal_state bằng thuật toán A*,
    cho phép cả di chuyển đơn (chi phí 1) và di chuyển kép (chi phí 2).
    Trả về danh sách các trạng thái (tuples) trên đường đi, hoặc None nếu không tìm thấy.
    """
    # Đảm bảo trạng thái là tuple (mặc dù type hint đã yêu cầu)
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    # Kiểm tra kích thước và tính hợp lệ cơ bản
    n = len(start_state)
    size = int(n**0.5)
    if size * size != n or len(goal_state) != n:
         # print("Lỗi: Trạng thái bắt đầu và/hoặc kết thúc không hợp lệ.")
         return None

    # Hàng đợi ưu tiên lưu trữ (f_value, g_value, state)
    initial_h = manhattan_distance(start_state, goal_state)
    if initial_h == float('inf'):
        # print("Lỗi: Không thể tính heuristic ban đầu. Trạng thái có thể không hợp lệ.")
        return None

    # (priority, cost_so_far, current_node)
    pq: List[Tuple[int, int, State]] = [(initial_h, 0, start_state)]

    # parent[child] = parent -> để dựng lại đường đi
    parent: Dict[State, Optional[State]] = {start_state: None}
    # g_costs[state] = chi phí thực tế (thấp nhất đã tìm thấy) từ start_state đến state
    g_costs: Dict[State, int] = {start_state: 0}

    # Tập các trạng thái đã được xử lý hoàn toàn (đã lấy ra khỏi pq và khám phá hàng xóm)
    closed_set: Set[State] = set()

    # processed_nodes = 0 # Bỏ comment nếu muốn theo dõi số nút xử lý để debug

    while pq:
        # Lấy trạng thái có f_value thấp nhất từ hàng đợi
        _, g_current, current_state = heappop(pq)
        # processed_nodes += 1

        # Nếu trạng thái này đã được xử lý xong với chi phí bằng hoặc tốt hơn, bỏ qua
        if current_state in closed_set:
             continue
        closed_set.add(current_state) # Đánh dấu là đã xử lý xong

        # Kiểm tra xem đã đến đích chưa
        if current_state == goal_state:
            # print(f"Đã tìm thấy đích! Chi phí đường đi (g_value): {g_current}") # Gỡ comment để debug
            # print(f"Số nút đã xử lý: {processed_nodes}") # Gỡ comment để debug
            return reconstruct_path(current_state, parent)

        # Khám phá các hàng xóm
        for next_state, move_cost in get_neighbors_with_costs(current_state):
            # Bỏ qua nếu đã xử lý xong
            if next_state in closed_set:
                continue

            # Tính chi phí mới để đến trạng thái hàng xóm
            new_g = g_current + move_cost

            # Nếu tìm thấy đường đi tốt hơn đến next_state (hoặc đây là lần đầu tiên)
            if new_g < g_costs.get(next_state, float('inf')):
                g_costs[next_state] = new_g
                parent[next_state] = current_state
                h_value = manhattan_distance(next_state, goal_state)
                if h_value == float('inf'):
                    # print(f"Cảnh báo: Heuristic không hợp lệ cho trạng thái {next_state}. Bỏ qua.")
                    continue # Bỏ qua nếu heuristic không hợp lệ
                f_new = new_g + h_value
                # Thêm vào hàng đợi ưu tiên
                heappush(pq, (f_new, new_g, next_state))

    # print(f"Không tìm thấy đường đi đến đích. Số nút đã xử lý: {processed_nodes}") # Gỡ comment để debug
    return None # Không tìm thấy lời giải

