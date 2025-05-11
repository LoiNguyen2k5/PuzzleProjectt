
import heapq
from typing import List, Tuple, Optional, Set, Dict

# Định nghĩa kiểu dữ liệu cho trạng thái (một tuple các số nguyên)
State = Tuple[int, ...]

def manhattan_distance(state: State, goal_state: State) -> int:
    """
    Tính tổng khoảng cách Manhattan cho tất cả các ô (trừ ô trống)
    đến vị trí mục tiêu của chúng. (Heuristic)
    """
    total = 0
    try:
        size = int(len(state)**0.5)
        if size * size != len(state) or len(goal_state) != len(state):
             return float('inf') # Trạng thái không hợp lệ
        blank_tile = size * size
    except TypeError:
        return float('inf') # Đầu vào không phải dạng list/tuple

    goal_map = {tile: i for i, tile in enumerate(goal_state)} # Map để tra cứu vị trí đích

    for i in range(len(state)):
        tile = state[i]
        if tile != blank_tile:
            current_row, current_col = divmod(i, size)
            goal_pos = goal_map.get(tile)
            if goal_pos is None:
                return float('inf') # Ô không có trong trạng thái đích
            goal_row, goal_col = divmod(goal_pos, size)
            total += abs(current_row - goal_row) + abs(current_col - goal_col)
    return total

def get_neighbors_with_double_moves(state: State) -> List[State]:
    """
    Tạo ra các trạng thái hàng xóm có thể có, bao gồm cả di chuyển đơn và kép.
    Không trả về chi phí, chỉ trả về danh sách các trạng thái.
    """
    neighbors: List[State] = []
    s_list = list(state)
    try:
        size = int(len(state)**0.5)
        if size * size != len(state):
             return [] # Không phải bảng vuông
        blank_tile = size * size
        blank_index = s_list.index(blank_tile)
    except (ValueError, TypeError):
        return [] # Trạng thái không hợp lệ hoặc không tìm thấy ô trống

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
            neighbors.append(neighbor_state) # Thêm hàng xóm di chuyển đơn
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
                neighbors.append(neighbor2_state) # Thêm hàng xóm di chuyển kép

    # Loại bỏ trùng lặp (tùy chọn, vì visited set sẽ xử lý)
    # neighbors = list(set(neighbors)) # Có thể thêm nếu muốn tối ưu một chút
    return neighbors

def solve(start_state: State, goal_state: State, beam_width: int = 10) -> Optional[List[State]]:
    """
    Giải 8-Puzzle sử dụng thuật toán Beam Search với di chuyển kép.

    Args:
        start_state (tuple): Trạng thái ban đầu của puzzle.
        goal_state (tuple): Trạng thái đích của puzzle.
        beam_width (int): Độ rộng của beam (số lượng trạng thái tốt nhất được giữ lại).

    Returns:
        list: Danh sách các trạng thái (tuples) từ trạng thái ban đầu đến trạng thái đích
              (nếu tìm thấy), hoặc None nếu không tìm thấy giải pháp.
              Lưu ý: Đường đi có thể không tối ưu về số bước tuyệt đối do bản chất của Beam Search.
    """
    start_state = tuple(start_state)
    goal_state = tuple(goal_state)

    # Tính heuristic ban đầu
    start_h = manhattan_distance(start_state, goal_state)
    if start_h == float('inf'):
        print("Lỗi: Trạng thái bắt đầu hoặc kết thúc không hợp lệ.")
        return None

    # Khởi tạo beam với trạng thái bắt đầu
    # Beam lưu trữ: (heuristic, state, path_to_state)
    beam: List[Tuple[int, State, List[State]]] = [(start_h, start_state, [start_state])]

    # Set để lưu trữ các trạng thái đã được khám phá trong các beam trước đó
    # để tránh đi vào vòng lặp hoặc khám phá lại các nhánh đã bị loại bỏ.
    visited: Set[State] = {start_state}

    max_depth = 100 # Giới hạn độ sâu để tránh chạy vô hạn nếu bị kẹt
    depth = 0

    while beam and depth < max_depth:
        depth += 1
        new_beam_candidates: List[Tuple[int, State, List[State]]] = []

        # Mở rộng tất cả các trạng thái trong beam hiện tại
        for h_current, current_state, current_path in beam:
            # Kiểm tra mục tiêu trước khi mở rộng
            if current_state == goal_state:
                print(f"Tìm thấy giải pháp ở độ sâu {len(current_path) - 1} (số hành động)")
                return current_path

            # Lấy các trạng thái hàng xóm (bao gồm cả di chuyển đơn và kép)
            neighbors = get_neighbors_with_double_moves(current_state)

            for neighbor in neighbors:
                # Chỉ xem xét các trạng thái chưa từng xuất hiện trong beam trước đó
                if neighbor not in visited:
                    visited.add(neighbor) # Đánh dấu đã thăm ngay khi đưa vào xem xét cho beam tiếp theo
                    neighbor_h = manhattan_distance(neighbor, goal_state)
                    if neighbor_h != float('inf'):
                        new_path = current_path + [neighbor]
                        # Sử dụng heapq để có thể dễ dàng lấy phần tử tốt nhất sau này
                        heapq.heappush(new_beam_candidates, (neighbor_h, neighbor, new_path))

        # Chọn ra beam_width trạng thái tốt nhất (heuristic thấp nhất) từ tất cả các ứng viên
        # Sử dụng heapq.nsmallest để hiệu quả
        beam = heapq.nsmallest(beam_width, new_beam_candidates)

        if not beam:
             # print(f"Beam trống ở độ sâu {depth}. Không tìm thấy giải pháp.")
             break # Dừng nếu không còn trạng thái nào trong beam

    print("Không tìm thấy giải pháp trong giới hạn độ sâu hoặc beam bị trống.")
    return None # Không tìm thấy giải pháp

