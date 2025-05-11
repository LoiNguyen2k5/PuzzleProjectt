import pygame
import sys
import random
from collections import deque
import time
import copy


DARK_BG = (44, 62, 80)         
PRIMARY = (26, 188, 156)       
PRIMARY_DARK = (22, 160, 133)  
SECONDARY = (236, 240, 241)    
GRAY = (52, 73, 94)            
LIGHT_GRAY = (149, 165, 166)   
TILE_BG = (52, 73, 94)         
TILE_SOLVED = (46, 204, 113)   
RED = (231, 76, 60)            
TILE_POST_ALGORITHM_RED = (200, 30, 30) 


SHAKE_DURATION = 200; SHAKE_MAGNITUDE = 5


TARGET_GOAL_STATES = {
    (1, 2, 3, 4, 5, 6, 7, 8, 9), (1, 4, 7, 2, 5, 8, 3, 6, 9),
    (1, 2, 3, 8, 9, 4, 7, 6, 5)}
TARGET_GOAL_LIST = list(TARGET_GOAL_STATES)


try:
    if not pygame.display.get_init(): pygame.display.init()
    screen_info = pygame.display.Info()
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
except pygame.error: WIDTH, HEIGHT = 1280, 720 

def get_inversions(state):
    state_without_blank = [x for x in state if x != 9]
    inversions = 0
    for i in range(len(state_without_blank)):
        for j in range(i + 1, len(state_without_blank)):
            if state_without_blank[i] > state_without_blank[j]:
                inversions += 1
    return inversions

def is_solvable(state):
    if 9 not in state or len(state) != 9: return False
    return get_inversions(state) % 2 == 0

def apply_move(state, move_direction):
    s = list(state)
    try: blank_index = s.index(9)
    except ValueError: return None
    row, col = divmod(blank_index, 3)
    dr, dc = 0, 0
    if move_direction == 'Up': dr = -1
    elif move_direction == 'Down': dr = 1
    elif move_direction == 'Left': dc = -1
    elif move_direction == 'Right': dc = 1
    else: return None
    new_row, new_col = row + dr, col + dc
    if 0 <= new_row < 3 and 0 <= new_col < 3:
        new_index = new_row * 3 + new_col
        s[blank_index], s[new_index] = s[new_index], s[blank_index]
        return tuple(s)
    else:
        return None

def generate_specific_solvable_states(num_states, max_reverse_depth=15, required_start_value=1):
    generated_states = set()
    attempts = 0
    max_attempts = num_states * 100
    while len(generated_states) < num_states and attempts < max_attempts:
        attempts += 1
        current_state = random.choice(TARGET_GOAL_LIST)
        depth = random.randint(max(1, max_reverse_depth // 2), max_reverse_depth)
        temp_state = current_state
        move_list = ['Up', 'Down', 'Left', 'Right']
        valid_sequence = True
        for _ in range(depth):
            possible_next_states = {}
            for m in move_list:
                next_s = apply_move(temp_state, m)
                if next_s is not None: possible_next_states[m] = next_s
            if not possible_next_states: valid_sequence = False; break
            chosen_move = random.choice(list(possible_next_states.keys()))
            temp_state = possible_next_states[chosen_move]
        if not valid_sequence: continue
        if temp_state[0] == required_start_value and is_solvable(temp_state):
            generated_states.add(temp_state)
    if len(generated_states) < num_states:
        print(f"Warning: Only generated {len(generated_states)} states after {max_attempts} attempts.")
        if not generated_states:
             print("Error: Failed to generate any states. Using default.")
             return [(1, 2, 3, 4, 5, 9, 7, 8, 6)]
    return list(generated_states)[:num_states]

class AnimatedTile:
    def __init__(self, value, x, y, size):
        self.value = value; self.size = size; self.inner_size = int(size * 0.94)
        self.rect = pygame.Rect(x, y, size, size)
        self.inner_rect = pygame.Rect(x + (size - self.inner_size)//2, y + (size - self.inner_size)//2, self.inner_size, self.inner_size)
        self.current_x = float(x); self.current_y = float(y); self.target_x = float(x); self.target_y = float(y)
        self.speed = 0.25; self.is_shaking = False; self.shake_start_time = 0
        self.shake_duration = SHAKE_DURATION; self.shake_magnitude = SHAKE_MAGNITUDE
        self.original_x = float(x); self.original_y = float(y)
    def set_target(self, x, y):
        if not self.is_shaking:
            self.target_x = float(x); self.target_y = float(y)
            self.original_x = self.current_x; self.original_y = self.current_y
    def shake(self):
        if not self.is_shaking:
            self.is_shaking = True; self.shake_start_time = pygame.time.get_ticks()
            self.original_x = self.current_x; self.original_y = self.current_y
            self.target_x = self.original_x; self.target_y = self.original_y
    def update(self):
        now = pygame.time.get_ticks()
        if self.is_shaking:
            elapsed_shake = now - self.shake_start_time
            if elapsed_shake >= self.shake_duration:
                self.is_shaking = False; self.current_x = self.original_x; self.current_y = self.original_y
            else:
                offset_x = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                offset_y = random.uniform(-self.shake_magnitude, self.shake_magnitude)
                self.current_x = self.original_x + offset_x; self.current_y = self.original_y + offset_y
        else:
            dx = self.target_x - self.current_x; dy = self.target_y - self.current_y
            if abs(dx) > 0.5 or abs(dy) > 0.5:
                self.current_x += dx * self.speed; self.current_y += dy * self.speed
            else:
                self.current_x = self.target_x; self.current_y = self.target_y
        self.rect.x = int(self.current_x); self.rect.y = int(self.current_y)
        self.inner_rect.x = self.rect.x + (self.size - self.inner_size)//2
        self.inner_rect.y = self.rect.y + (self.size - self.inner_size)//2

    def draw(self, screen, font, is_in_final_goal_pos=False, overall_algorithm_finished=False):
        if self.value == 9: 
            if self.is_shaking:
                 shake_rect = self.rect.inflate(2,2)
                 pygame.draw.rect(screen, LIGHT_GRAY, shake_rect, border_radius=10, width=1)
            return

        bg_color = TILE_BG 
        if is_in_final_goal_pos: 
            if overall_algorithm_finished:
                bg_color = TILE_POST_ALGORITHM_RED 
            else: 
                bg_color = TILE_SOLVED

        pygame.draw.rect(screen, bg_color, self.inner_rect, border_radius=10)
        text = font.render(str(self.value), True, SECONDARY)
        screen.blit(text, text.get_rect(center=self.inner_rect.center))

    def is_at_target(self):
        if self.is_shaking: return False
        return abs(self.current_x - self.target_x) < 1 and abs(self.current_y - self.target_y) < 1

class Button:
     def __init__(self, x, y, width, height, text, color=PRIMARY, hover_color=PRIMARY_DARK):
         self.rect = pygame.Rect(x, y, width, height); self.text = text; self.color = color
         self.hover_color = hover_color; self.is_hovered = False; self.border_radius = 8
     def draw(self, screen, font):
         color = self.hover_color if self.is_hovered else self.color
         pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
         text_surface = font.render(self.text, True, SECONDARY) 
         screen.blit(text_surface, text_surface.get_rect(center=self.rect.center))
     def check_hover(self, mouse_pos): self.is_hovered = self.rect.collidepoint(mouse_pos); return self.is_hovered
     def is_clicked(self, mouse_pos, mouse_click): return self.rect.collidepoint(mouse_pos) and mouse_click

def find_common_path(initial_belief_states, target_goals_set):
    if not initial_belief_states: return None
    initial_belief_tuple = tuple(sorted(initial_belief_states))
    if all(state in target_goals_set for state in initial_belief_tuple): return []
    queue = deque([(initial_belief_tuple, [])])
    visited = {initial_belief_tuple}
    move_directions = ['Up', 'Down', 'Left', 'Right']
    max_iterations = 300000; iterations = 0; start_time = time.time()
    while queue:
        iterations += 1
        if iterations > max_iterations: return None
        current_belief_tuple, current_path = queue.popleft()
        for move in move_directions:
            next_belief_list = []
            for state in current_belief_tuple:
                next_state = apply_move(state, move)
                next_belief_list.append(next_state if next_state is not None else state)
            next_belief_tuple = tuple(sorted(next_belief_list))
            if next_belief_tuple not in visited:
                 if all(state in target_goals_set for state in next_belief_tuple):
                     return current_path + [move]
                 visited.add(next_belief_tuple)
                 queue.append((next_belief_tuple, current_path + [move]))
    return None

def run_blind_search():
    global WIDTH, HEIGHT
    local_WIDTH, local_HEIGHT = WIDTH, HEIGHT

    if not pygame.get_init(): pygame.init()
    if not pygame.font.get_init(): pygame.font.init()
    try:
        screen = pygame.display.get_surface()
        if screen is None:
             screen = pygame.display.set_mode((local_WIDTH, local_HEIGHT), pygame.FULLSCREEN if pygame.display.Info().current_w == local_WIDTH else 0)
        else:
             local_WIDTH, local_HEIGHT = screen.get_size()
             pygame.display.set_caption("Blind Search - 8 Puzzle")
    except pygame.error as e:
        print(f"Screen setup error: {e}. Using fallback.")
        local_WIDTH, local_HEIGHT = 1280, 720
        screen = pygame.display.set_mode((local_WIDTH, local_HEIGHT))
        pygame.display.set_caption("Blind Search - 8 Puzzle")
    clock = pygame.time.Clock()
    try:
        font_name = "Arial"; font = pygame.font.SysFont(font_name, 24)
        title_font = pygame.font.SysFont(font_name, 36, bold=True)
        puzzle_font_small = pygame.font.SysFont(font_name, 30, bold=True) 
        puzzle_font_large = pygame.font.SysFont(font_name, 50, bold=True) 
        info_font = pygame.font.SysFont(font_name, 20); move_font = pygame.font.SysFont(font_name, 28, bold=True)
        path_font = pygame.font.SysFont(font_name, 18)
    except: 
        font, title_font = pygame.font.Font(None, 24), pygame.font.Font(None, 36)
        puzzle_font_small, puzzle_font_large = pygame.font.Font(None, 30), pygame.font.Font(None, 50)
        info_font, move_font, path_font = pygame.font.Font(None, 20), pygame.font.Font(None, 28), pygame.font.Font(None, 18)

    state = "generating" 
    initial_states = []
    common_path = None
    all_animating_puzzles = [] 
    current_animated_state_tuples = [] 
    current_move_index = 0
    time_per_move = 0.4; last_anim_update = 0
    message = "Searching for solvable configuration..."
    num_initial_states_to_gen = 2; generation_max_depth = 12
    max_retries = 10; retry_count = 0
    back_button = Button(local_WIDTH - 130, local_HEIGHT - 60, 110, 40, "Back to Menu")

    total_start_time = time.time()
    generation_successful = False

    while common_path is None and retry_count < max_retries:
        print(f"\n--- Attempt {retry_count + 1}/{max_retries} ---")
        screen.fill(DARK_BG)
        title_surf = title_font.render("Blind Search", True, SECONDARY)
        screen.blit(title_surf, title_surf.get_rect(centerx=local_WIDTH // 2, y=HEIGHT // 3))
        search_msg = f"Searching for solvable configuration... (Attempt {retry_count + 1})"
        msg_surf = font.render(search_msg, True, LIGHT_GRAY)
        screen.blit(msg_surf, msg_surf.get_rect(centerx=local_WIDTH // 2, y=HEIGHT // 3 + 60))
        pygame.display.flip(); pygame.time.delay(50)
        for _ in pygame.event.get(): pass

        print(f"Generating {num_initial_states_to_gen} states...")
        start_gen_time = time.time()
        initial_states = generate_specific_solvable_states(num_initial_states_to_gen, generation_max_depth, 1)
        print(f"Generated {len(initial_states)} states in {time.time() - start_gen_time:.2f}s.")

        if not initial_states:
             print("Fatal: Failed to generate initial states."); message = "Error: Generation Failed."; state = "no_path"; generation_successful = False; break
        generation_successful = True
        for i, s_val in enumerate(initial_states): print(f"  State {i+1}: {s_val}")

        print(f"Finding common path..."); start_path_time = time.time()
        current_attempt_path = find_common_path(initial_states, TARGET_GOAL_STATES)
        print(f"Path finding attempt took {time.time() - start_path_time:.2f}s.")

        if current_attempt_path is not None:
            common_path = current_attempt_path; print("Common path FOUND!")
        else:
            retry_count += 1; print(f"Attempt {retry_count}/{max_retries} failed. Retrying..." if retry_count < max_retries else "Max retries reached.")

    total_duration = time.time() - total_start_time
    print(f"\n--- Search Finished (Total Time: {total_duration:.2f}s) ---")

    if common_path is not None:
        state = "animating" 
        message = f"Animating common path ({len(common_path)} moves)..." if common_path else "Already at goal states. Animating..."
        print(f"Final Path: {' -> '.join(common_path)}")

        all_animating_puzzles = []
        current_animated_state_tuples = list(initial_states) 

        num_puzzles = len(initial_states)
        total_padding = 100 
        available_width = local_WIDTH - total_padding
        puzzle_area_width = available_width / num_puzzles
        puzzle_area_height = local_HEIGHT * 0.6 

        max_tile_size = 150
        min_tile_size = 30
        anim_tile_size = max(min_tile_size, min(puzzle_area_width / 3, puzzle_area_height / 3, max_tile_size)) * 0.9
        anim_puzzle_size = anim_tile_size * 3 
        puzzle_spacing = (available_width - anim_puzzle_size * num_puzzles) / max(1, num_puzzles + 1) 

        overall_start_x = puzzle_spacing 

        for i, init_state in enumerate(initial_states):
            anim_start_x = overall_start_x + i * (anim_puzzle_size + puzzle_spacing)
            anim_start_y = (local_HEIGHT - anim_puzzle_size) / 2 - 60 

            puzzle_tiles = []
            for idx, val in enumerate(init_state):
                r, c = divmod(idx, 3)
                x = anim_start_x + c * anim_tile_size
                y = anim_start_y + r * anim_tile_size
                tile = AnimatedTile(val, x, y, anim_tile_size)
                puzzle_tiles.append(tile)
            all_animating_puzzles.append(puzzle_tiles)

        last_anim_update = pygame.time.get_ticks() 

    elif not generation_successful:
         state = "no_path" 
         print("Exiting due to generation failure.")
    else:
         message = f"Could not find common path after {max_retries} attempts."
         state = "no_path"
         print("Exiting: Max retries reached.")

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: mouse_click = True

        if mouse_click:
            if back_button.is_clicked(mouse_pos, mouse_click): running = False

        screen.fill(DARK_BG)
        final_title = "Blind Search Results" if state != "generating" else "Blind Search"
        title_surf = title_font.render(final_title, True, SECONDARY)
        screen.blit(title_surf, title_surf.get_rect(centerx=local_WIDTH // 2, y=30))
        msg_surf = font.render(message, True, LIGHT_GRAY) 
        screen.blit(msg_surf, msg_surf.get_rect(centerx=local_WIDTH // 2, y=80))
        back_button.check_hover(mouse_pos); back_button.draw(screen, font)

        if state == "no_path":
            if generation_successful and initial_states:
                grid_cols = min(len(initial_states), 5)
                grid_rows = (len(initial_states) + grid_cols - 1) // grid_cols
                total_grid_w = local_WIDTH * 0.85; total_grid_h = local_HEIGHT * 0.5
                puzzle_w = total_grid_w / grid_cols * 0.9; puzzle_h = total_grid_h / grid_rows * 0.9
                tile_size = min(puzzle_w, puzzle_h) / 3
                h_spacing = (total_grid_w / grid_cols) * 0.1; v_spacing = (total_grid_h / grid_rows) * 0.1
                start_x_grid = (local_WIDTH - total_grid_w) / 2; start_y_grid = 150
                for i, init_state_val in enumerate(initial_states):
                    row = i // grid_cols; col = i % grid_cols
                    px = start_x_grid + col * (puzzle_w + h_spacing) + h_spacing/2
                    py = start_y_grid + row * (puzzle_h + v_spacing) + v_spacing/2
                    for idx, val_tile in enumerate(init_state_val):
                        r_tile, c_tile = divmod(idx, 3)
                        x_tile = px + c_tile * tile_size; y_tile = py + r_tile * tile_size
                        tile_rect = pygame.Rect(x_tile + 1, y_tile + 1, tile_size - 2, tile_size - 2)
                        bg_color = TILE_BG if val_tile != 9 else GRAY 
                        pygame.draw.rect(screen, bg_color, tile_rect, border_radius=3)
                        if val_tile != 9:
                            text_tile = puzzle_font_small.render(str(val_tile), True, SECONDARY)
                            screen.blit(text_tile, text_tile.get_rect(center=tile_rect.center))
            error_y_pos = start_y_grid + total_grid_h + 40 if generation_successful and initial_states else local_HEIGHT // 2
            error_surf = font.render(message, True, RED) 
            screen.blit(error_surf, error_surf.get_rect(center=(local_WIDTH // 2, error_y_pos)))

        elif state == "animating" or state == "finished":
            all_tiles_globally_settled = True 
            current_time = pygame.time.get_ticks()
            shake_triggered_overall = False

            if state == "animating" and common_path and current_move_index < len(common_path):
                 if current_time - last_anim_update >= time_per_move * 1000:
                      all_ready = True
                      for puzzle_tiles_list in all_animating_puzzles:
                           blank_tile = next((t for t in puzzle_tiles_list if t.value == 9), None)
                           if blank_tile and blank_tile.is_shaking:
                               all_ready = False; break
                      if all_ready:
                          for puzzle_tiles_list in all_animating_puzzles:
                              if not all(tile.is_at_target() for tile in puzzle_tiles_list if not tile.is_shaking):
                                  all_ready = False; break

                      if all_ready:
                           move_to_apply = common_path[current_move_index]
                           needs_target_update_indices = [] 

                           for i_puzzle in range(len(current_animated_state_tuples)):
                               current_puzzle_state = current_animated_state_tuples[i_puzzle]
                               puzzle_tiles_list = all_animating_puzzles[i_puzzle]
                               blank_tile = next((t for t in puzzle_tiles_list if t.value == 9), None)
                               next_state_tuple = apply_move(current_puzzle_state, move_to_apply)
                               if next_state_tuple: 
                                   current_animated_state_tuples[i_puzzle] = next_state_tuple
                                   needs_target_update_indices.append(i_puzzle)
                               else: 
                                   if blank_tile:
                                       blank_tile.shake()
                                       shake_triggered_overall = True 
                           if needs_target_update_indices:
                                num_puzzles_val = len(initial_states)
                                total_padding_val = 100; available_width_val = local_WIDTH - total_padding_val
                                anim_tile_size_val = all_animating_puzzles[0][0].size 
                                anim_puzzle_size_val = anim_tile_size_val * 3
                                puzzle_spacing_val = (available_width_val - anim_puzzle_size_val * num_puzzles_val) / max(1, num_puzzles_val + 1)
                                overall_start_x_val = puzzle_spacing_val

                                for puzzle_idx in needs_target_update_indices:
                                    anim_start_x_curr = overall_start_x_val + puzzle_idx * (anim_puzzle_size_val + puzzle_spacing_val)
                                    anim_start_y_curr = (local_HEIGHT - anim_puzzle_size_val) / 2 - 60
                                    puzzle_tiles_to_update = all_animating_puzzles[puzzle_idx]
                                    target_state = current_animated_state_tuples[puzzle_idx]
                                    value_pos_map = {val: idx for idx, val in enumerate(target_state)}
                                    for tile in puzzle_tiles_to_update:
                                        if tile.value in value_pos_map:
                                            new_idx = value_pos_map[tile.value]
                                            r, c = divmod(new_idx, 3)
                                            target_x = anim_start_x_curr + c * anim_tile_size_val
                                            target_y = anim_start_y_curr + r * anim_tile_size_val
                                            tile.set_target(target_x, target_y)
                           current_move_index += 1
                           last_anim_update = current_time

            all_puzzles_in_goal = True 
            for i_puzzle_draw in range(len(all_animating_puzzles)):
                puzzle_tiles_draw = all_animating_puzzles[i_puzzle_draw]
                puzzle_state_draw = current_animated_state_tuples[i_puzzle_draw]
                if puzzle_state_draw not in TARGET_GOAL_STATES:
                    all_puzzles_in_goal = False 
                is_this_puzzle_goal = (state=="finished" or (state=="animating" and current_move_index == len(common_path))) and (puzzle_state_draw in TARGET_GOAL_STATES)
                for tile_draw in puzzle_tiles_draw:
                    tile_draw.update()
                    if not tile_draw.is_at_target() and not tile_draw.is_shaking:
                        all_tiles_globally_settled = False 
                    is_final_pos = False
                    if is_this_puzzle_goal:
                         current_idx_tile = -1
                         try: current_idx_tile = list(puzzle_state_draw).index(tile_draw.value)
                         except ValueError: pass
                         if current_idx_tile != -1 and tile_draw.value != 9:
                             for goal_state_check in TARGET_GOAL_STATES:
                                 if goal_state_check[current_idx_tile] == tile_draw.value: is_final_pos = True; break
                    tile_draw.draw(screen, puzzle_font_large, is_final_pos, (state == "finished"))

            if common_path:
                 move_text = ""
                 is_final_step_completed = (state == "finished" or (state == "animating" and current_move_index == len(common_path)))
                 all_logically_goal = all(p_state in TARGET_GOAL_STATES for p_state in current_animated_state_tuples)

                 if current_move_index < len(common_path):
                     move_text = f"Move {current_move_index + 1}/{len(common_path)}: {common_path[current_move_index]}"
                     if shake_triggered_overall: move_text += " (Shake!)" 
                 elif is_final_step_completed and all_logically_goal:
                     move_text = f"Reached Goal States! ({len(common_path)} Moves)"
                 elif is_final_step_completed: 
                     move_text = "Animation finished (End State Error)"

                 if move_text:
                    color_move_text = RED if "Shake" in move_text or "Error" in move_text else \
                            (PRIMARY if (is_final_step_completed and all_logically_goal) else SECONDARY)
                    move_surf = move_font.render(move_text, True, color_move_text)
                    screen.blit(move_surf, move_surf.get_rect(center=(local_WIDTH // 2, local_HEIGHT - 100)))

            if state == "animating" and current_move_index == len(common_path) and all_tiles_globally_settled:
                 any_shaking = any(tile.is_shaking for puzzle in all_animating_puzzles for tile in puzzle)
                 if not any_shaking:
                      if all_logically_goal:
                          state = "finished"
                          message = f"All states reached a goal!"
                          print("Animation finished successfully.")
                      else:
                          state = "finished"
                          message = f"Animation finished (End State Error!)"
                          print(f"Error: Animation finished, but final states are: {current_animated_state_tuples}")
        pygame.display.flip()
        clock.tick(60)
    print("Exiting blind search view.")

if __name__ == "__main__":
    if not pygame.get_init(): pygame.init()
    if not pygame.font.get_init(): pygame.font.init()
    run_blind_search()
    pygame.quit()
    sys.exit()