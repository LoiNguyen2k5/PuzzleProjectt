# algorithms/simulated_annealing.py
import random
import math

def solve(start, goal, initial_temperature=100, cooling_rate=0.003):
    """
    Giải 8-Puzzle bằng thuật toán Simulated Annealing.

    Args:
        start (tuple): Trạng thái ban đầu của puzzle.
        goal (tuple): Trạng thái đích của puzzle.
        initial_temperature (float): Nhiệt độ ban đầu.
        cooling_rate (float): Tốc độ làm mát (giảm nhiệt độ).

    Returns:
        list: Danh sách các trạng thái từ trạng thái ban đầu đến trạng thái đích (nếu tìm thấy),
              hoặc None nếu không tìm thấy giải pháp.
    """

    def get_neighbors(state):
        """Tìm các trạng thái kế cận của một trạng thái."""
        empty_index = state.index(9)
        row, col = empty_index // 3, empty_index % 3
        neighbors = []

        moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]  # Phải, Trái, Xuống, Lên
        for dr, dc in moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 3 and 0 <= new_col < 3:
                new_index = new_row * 3 + new_col
                new_state = list(state)
                new_state[empty_index], new_state[new_index] = new_state[new_index], new_state[empty_index]
                neighbors.append(tuple(new_state))
        return neighbors

    def heuristic(state):
        """Tính heuristic (Manhattan distance) từ trạng thái hiện tại đến trạng thái đích."""
        distance = 0
        for i in range(9):
            if state[i] != 9:  # Không tính ô trống
                goal_index = goal.index(state[i])
                row1, col1 = i // 3, i % 3
                row2, col2 = goal_index // 3, goal_index % 3
                distance += abs(row1 - row2) + abs(col1 - col2)
        return distance

    current_state = start
    path = [current_state]
    current_heuristic = heuristic(current_state)
    temperature = initial_temperature

    while current_state != goal:
        if temperature <= 0.0001:  # Dừng khi nhiệt độ quá thấp
            return None

        neighbors = get_neighbors(current_state)
        if not neighbors:
            return None

        next_state = random.choice(neighbors)
        next_heuristic = heuristic(next_state)
        delta_e = next_heuristic - current_heuristic

        # Chấp nhận trạng thái tốt hơn hoặc trạng thái xấu hơn với xác suất nhất định
        if delta_e < 0 or random.random() < math.exp(-delta_e / temperature):
            current_state = next_state
            path.append(current_state)
            current_heuristic = next_heuristic

        # Làm mát hệ thống
        temperature *= (1 - cooling_rate)

    return path