from typing import List, Tuple, Optional, Set, Dict

# Định nghĩa kiểu dữ liệu cho trạng thái (một tuple các số nguyên)
State = Tuple[int, ...]

def get_neighbors_with_double_moves(state: State) -> List[State]:
    """
    Tạo ra các trạng thái hàng xóm có thể có, bao gồm cả di chuyển đơn và kép.
    Trả về danh sách các trạng thái duy nhất.
    """
    neighbors: Set[State] = set() # Sử dụng set để tự động loại bỏ trùng lặp
    s_list = list(state)
    try:
        size = int(len(state)**0.5)
        if size * size != len(state):
             return [] # Không phải bảng vuông
        blank_tile = size * size
        blank_index = s_list.index(blank_tile)
    except (ValueError, TypeError):
        # print(f"Lỗi: Không tìm thấy ô trống hoặc trạng thái không hợp lệ trong {state}")
        return [] # Trạng thái không hợp lệ

    row, col = divmod(blank_index, size)
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)] # Lên, Xuống, Trái, Phải

    # --- Di chuyển đơn ---
    single_move_intermediates: List[Tuple[State, int]] = [] # Lưu (trạng thái, vị trí ô trống mới)
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < size and 0 <= new_col < size:
            new_index = new_row * size + new_col
            new_s = s_list[:]
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbor_state = tuple(new_s)
            neighbors.add(neighbor_state) # Thêm hàng xóm di chuyển đơn
            single_move_intermediates.append((neighbor_state, new_index))

    # --- Di chuyển kép ---
    for intermediate_state, intermediate_blank_index in single_move_intermediates:
        s_intermediate = list(intermediate_state)
        row1, col1 = divmod(intermediate_blank_index, size)
        for dr, dc in moves:
            new_row2, new_col2 = row1 + dr, col1 + dc
            if 0 <= new_row2 < size and 0 <= new_col2 < size:
                new_index2 = new_row2 * size + new_col2
                # Bước thứ hai không được quay lại vị trí ban đầu
                if new_index2 == blank_index:
                    continue

                new_s2 = s_intermediate[:]
                new_s2[intermediate_blank_index], new_s2[new_index2] = new_s2[new_index2], new_s2[intermediate_blank_index]
                neighbor2_state = tuple(new_s2)
                neighbors.add(neighbor2_state) # Thêm hàng xóm di chuyển kép (set xử lý trùng lặp)

    # DFS thường khám phá theo thứ tự ngược lại với BFS/A*
    # Trả về list theo thứ tự có thể ảnh hưởng đến đường đi tìm thấy đầu tiên
    return list(neighbors)

def reconstruct_path(state: State, parent: Dict[State, Optional[State]]) -> List[State]:
    """
    Xây dựng lại đường đi từ trạng thái đích ngược về trạng thái bắt đầu.
    """
    path: List[State] = []
    current: Optional[State] = state
    while current is not None:
        path.append(current)
        current = parent.get(current)
    path.reverse()
    return path

def solve(start_state: State, goal_state: State) -> Optional[List[State]]:
    """
    Tìm kiếm theo chiều sâu (DFS) với khả năng di chuyển kép.
    Tìm một đường đi đến đích (không đảm bảo tối ưu).

    Args:
        start_state (tuple): Trạng thái bắt đầu.
        goal_state (tuple): Trạng thái đích.

    Returns:
        list: Đường đi (list các tuple trạng thái) nếu tìm thấy, None nếu không.
              Đường đi này thường không tối ưu.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    if start_state == goal_state:
        return [start_state]

    stack: List[State] = [start_state]
    visited: Set[State] = {start_state}
    parent: Dict[State, Optional[State]] = {start_state: None}

    # Giới hạn độ sâu để tránh bị kẹt trong nhánh vô hạn (tùy chọn nhưng nên có)
    MAX_DEPTH = 50 # Điều chỉnh giá trị này nếu cần
    depth_map: Dict[State, int] = {start_state: 0}

    while stack:
        current_state = stack.pop()

        # Kiểm tra mục tiêu khi lấy ra khỏi stack
        if current_state == goal_state:
            return reconstruct_path(goal_state, parent)

        current_depth = depth_map[current_state]
        if current_depth >= MAX_DEPTH:
            continue # Bỏ qua nếu đã đạt giới hạn độ sâu

        # Tạo các hàng xóm (bao gồm cả di chuyển đơn và kép)
        # Thứ tự duyệt hàng xóm có thể ảnh hưởng đến kết quả của DFS
        neighbors = get_neighbors_with_double_moves(current_state)
        # Đảo ngược thứ tự để stack hoạt động giống đệ quy hơn (tùy chọn)
        # neighbors.reverse()

        for next_state in neighbors:
            if next_state not in visited:
                visited.add(next_state)
                parent[next_state] = current_state
                depth_map[next_state] = current_depth + 1 # Lưu độ sâu
                stack.append(next_state) # Thêm vào stack

    # Nếu không tìm thấy sau khi duyệt hết
    return None