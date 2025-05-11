# blind.py
import pygame
import sys
import random
from collections import deque
import time
import copy # For deep copying states if necessary

# --- Constants and Colors ---
DARK_BG = (18, 27, 18)
PRIMARY = (52, 168, 83)
PRIMARY_DARK = (39, 125, 61)
SECONDARY = (255, 255, 255)
GRAY = (75, 99, 85)
LIGHT_GRAY = (156, 175, 163)
TILE_BG = (30, 59, 41)
TILE_SOLVED = (34, 197, 94)
RED = (209, 49, 49)

# --- Target Goal States ---
TARGET_GOAL_STATES = {
    (1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 4, 7, 2, 5, 8, 3, 6, 9),
    (1, 2, 3, 8, 9, 4, 7, 6, 5)
}

# --- Screen Dimensions ---
try:
    pygame.display.init() # Ensure display is initialized to get info
    screen_info = pygame.display.Info()
    WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
except pygame.error:
    print("Warning: Pygame display error getting screen info. Using default 800x600.")
    WIDTH, HEIGHT = 800, 600


# --- Helper Functions ---

def get_inversions(state):
    """Helper to count inversions."""
    state_without_blank = [x for x in state if x != 9]
    inversions = 0
    for i in range(len(state_without_blank)):
        for j in range(i + 1, len(state_without_blank)):
            if state_without_blank[i] > state_without_blank[j]:
                inversions += 1
    return inversions

def is_solvable(state):
    """Checks solvability for standard goal (1..9)."""
    if 9 not in state or len(state) != 9: return False
    inversions = get_inversions(state)
    return inversions % 2 == 0

def apply_move(state, move_direction):
    """Applies a move to the blank tile (9). Returns new tuple or None."""
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
    return None

def generate_random_solvable_state():
    """Generates a random, solvable state where state[0] == 1."""
    while True:
        remaining_tiles = list(range(2, 10))
        random.shuffle(remaining_tiles)
        state = tuple([1] + remaining_tiles)
        if is_solvable(state):
            return state

# --- Classes ---

class AnimatedTile:
    # (Keep the AnimatedTile class definition exactly as before)
    def __init__(self, value, x, y, size):
        self.value = value
        self.size = size
        self.inner_size = int(size * 0.94)
        self.rect = pygame.Rect(x, y, size, size)
        self.inner_rect = pygame.Rect(x + (size - self.inner_size)//2,
                                      y + (size - self.inner_size)//2,
                                      self.inner_size,
                                      self.inner_size)
        self.current_x = float(x)
        self.current_y = float(y)
        self.target_x = float(x)
        self.target_y = float(y)
        self.speed = 0.2

    def set_target(self, x, y):
        self.target_x = float(x)
        self.target_y = float(y)

    def update(self):
        dx = self.target_x - self.current_x
        dy = self.target_y - self.current_y
        if abs(dx) < 1 and abs(dy) < 1:
            self.current_x = self.target_x
            self.current_y = self.target_y
        else:
            self.current_x += dx * self.speed
            self.current_y += dy * self.speed
        self.rect.x = int(self.current_x)
        self.rect.y = int(self.current_y)
        self.inner_rect.x = self.rect.x + (self.size - self.inner_size) // 2
        self.inner_rect.y = self.rect.y + (self.size - self.inner_size) // 2

    def draw(self, screen, font, is_solved_pos=False):
        if self.value == 9: return
        bg_color = TILE_SOLVED if is_solved_pos else TILE_BG
        pygame.draw.rect(screen, bg_color, self.inner_rect, border_radius=10)
        text = font.render(str(self.value), True, SECONDARY)
        text_rect = text.get_rect(center=self.inner_rect.center)
        screen.blit(text, text_rect)

    def is_at_target(self):
        return abs(self.current_x - self.target_x) < 1 and abs(self.current_y - self.target_y) < 1

class Button:
    # (Keep the Button class definition exactly as before)
     def __init__(self, x, y, width, height, text, color=PRIMARY, hover_color=PRIMARY_DARK):
         self.rect = pygame.Rect(x, y, width, height)
         self.text = text
         self.color = color
         self.hover_color = hover_color
         self.is_hovered = False
         self.border_radius = 8

     def draw(self, screen, font):
         color = self.hover_color if self.is_hovered else self.color
         pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
         text_surface = font.render(self.text, True, SECONDARY)
         text_rect = text_surface.get_rect(center=self.rect.center)
         screen.blit(text_surface, text_rect)

     def check_hover(self, mouse_pos):
         self.is_hovered = self.rect.collidepoint(mouse_pos)
         return self.is_hovered

     def is_clicked(self, mouse_pos, mouse_click):
         return self.rect.collidepoint(mouse_pos) and mouse_click


# --- Blind Search Algorithm ---
def find_common_path(initial_belief_states, target_goals):
    """BFS on belief state space (expects exactly 2 states)."""
    if not initial_belief_states or len(initial_belief_states) != 2:
        print("Error: find_common_path requires exactly 2 states.")
        return None

    initial_belief_tuple = tuple(initial_belief_states)
    target_goals_set = set(target_goals)

    if all(state in target_goals_set for state in initial_belief_tuple):
        return [] # Already solved

    queue = deque([(initial_belief_tuple, [])])
    visited = {initial_belief_tuple}
    move_directions = ['Up', 'Down', 'Left', 'Right']
    max_iterations = 150000
    iterations = 0
    start_time = time.time()

    while queue and iterations < max_iterations:
        iterations += 1
        current_belief_tuple, current_path = queue.popleft()

        if iterations % 20000 == 0: # Less frequent updates
            elapsed = time.time() - start_time
            print(f"BFS iter {iterations}, queue: {len(queue)}, path len: {len(current_path)}, time: {elapsed:.1f}s")

        for move in move_directions:
            state1, state2 = current_belief_tuple
            next_state1 = apply_move(state1, move)
            next_state2 = apply_move(state2, move)

            if next_state1 is not None and next_state2 is not None:
                next_belief_tuple = (next_state1, next_state2)
                if next_belief_tuple not in visited:
                    if all(state in target_goals_set for state in next_belief_tuple):
                        elapsed = time.time() - start_time
                        print(f"Common path found! Iter: {iterations}, Len: {len(current_path) + 1}, Time: {elapsed:.2f}s")
                        return current_path + [move]

                    visited.add(next_belief_tuple)
                    queue.append((next_belief_tuple, current_path + [move]))

    elapsed = time.time() - start_time
    print(f"BFS failed for pair after {iterations} iterations. Time: {elapsed:.2f}s")
    return None

# --- GUI Function ---
def run_blind_search():
    # Initialize Pygame and Modules
    pygame.init()
    pygame.font.init()

    # Setup Screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("Blind Search - 8 Puzzle")
    clock = pygame.time.Clock()

    # Load Fonts
    try:
        font_name = "Arial"
        if font_name not in pygame.font.get_fonts():
            available_fonts = pygame.font.get_fonts()
            common_fonts = ["freesans", "helvetica", "dejavusans", "verdana", "sans"]
            font_name = pygame.font.get_default_font()
            for cf in common_fonts:
                if cf.lower() in [f.lower() for f in available_fonts]: font_name = cf; break
        print(f"Blind search using font: {font_name}")
        font = pygame.font.SysFont(font_name, 24)
        title_font = pygame.font.SysFont(font_name, 36, bold=True)
        puzzle_font_small = pygame.font.SysFont(font_name, 30, bold=True)
        puzzle_font_large = pygame.font.SysFont(font_name, 60, bold=True)
        info_font = pygame.font.SysFont(font_name, 20)
        move_font = pygame.font.SysFont(font_name, 28, bold=True)
        search_font = pygame.font.SysFont(font_name, 28)
    except Exception as e:
        print(f"Blind Font initialization error: {e}. Falling back.")
        font = pygame.font.Font(None, 24); title_font = pygame.font.Font(None, 36)
        puzzle_font_small = pygame.font.Font(None, 30); puzzle_font_large = pygame.font.Font(None, 60)
        info_font = pygame.font.Font(None, 20); move_font = pygame.font.Font(None, 28)
        search_font = pygame.font.Font(None, 28)

    # --- State Variables ---
    current_ui_state = "searching" # searching, selecting, animating, finished
    initial_states = [] # Will hold the SUCCESSFUL pair
    common_path = None
    selected_state_index = -1
    animating_tiles = []
    current_move_index = 0
    time_per_move = 0.6
    message = "Initializing search..."
    search_attempts = 0

    # Buttons
    back_button = Button(WIDTH - 130, HEIGHT - 60, 110, 40, "Back to Menu")

    # --- Main Loop ---
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False

        # --- Event Processing ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
                if back_button.is_clicked(mouse_pos, mouse_click): running = False

                # --- Click Handling when Selecting State ---
                if current_ui_state == "selecting":
                    # Calculate geometry for the two displayed puzzles
                    grid_cols = 2
                    total_grid_w = WIDTH * 0.6
                    puzzle_w = total_grid_w / grid_cols * 0.9
                    puzzle_h = puzzle_w
                    tile_size = puzzle_w / 3 # Needed for inner tile drawing, not click rect
                    spacing_x = (total_grid_w / grid_cols) * 0.1
                    start_x = (WIDTH - total_grid_w) / 2
                    start_y = HEIGHT // 2 - puzzle_h // 2 + 50 # Position below title/path

                    # Iterate only through the 2 states stored
                    if len(initial_states) == 2: # Safety check
                        for i in range(len(initial_states)):
                            col = i # i will be 0 or 1
                            puzzle_origin_x = start_x + col * (puzzle_w + spacing_x)
                            puzzle_origin_y = start_y
                            # Click area is the whole puzzle width/height
                            puzzle_rect = pygame.Rect(puzzle_origin_x, puzzle_origin_y, puzzle_w, puzzle_h)

                            if puzzle_rect.collidepoint(mouse_pos):
                                print(f"Clicked on puzzle index {i}")
                                selected_state_index = i
                                current_move_index = 0
                                current_ui_state = "animating"
                                # Initialize animated tiles for the selected state
                                animating_tiles = []
                                current_animated_state_tuple = initial_states[selected_state_index] # Get the tuple
                                anim_tile_size = min(WIDTH * 0.4, HEIGHT * 0.4) / 3
                                anim_start_x = (WIDTH - anim_tile_size * 3) / 2
                                anim_start_y = (HEIGHT - anim_tile_size * 3) / 2 - 50 # Center vertically

                                for idx, val in enumerate(current_animated_state_tuple):
                                    r, c = divmod(idx, 3)
                                    x = anim_start_x + c * anim_tile_size
                                    y = anim_start_y + r * anim_tile_size
                                    tile = AnimatedTile(val, x, y, anim_tile_size)
                                    animating_tiles.append(tile)
                                message = f"Animating State {selected_state_index + 1}"
                                break # Click handled, exit inner loop

        # --- State Logic: Searching for a Solvable Pair ---
        if current_ui_state == "searching":
            search_attempts += 1
            print(f"\n--- Blind Search Attempt {search_attempts} ---")
            temp_message = f"Attempt {search_attempts}: Generating & Searching..." # Temp msg for drawing

            # Draw "Searching" message immediately
            screen.fill(DARK_BG)
            title_surf = title_font.render("Blind Search", True, SECONDARY)
            screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
            msg_surf = search_font.render(temp_message, True, LIGHT_GRAY)
            screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            back_button.check_hover(mouse_pos)
            back_button.draw(screen, font)
            pygame.display.flip() # Show searching status

            # Generate a new pair
            current_pair = [generate_random_solvable_state() for _ in range(2)]
            print(f"Generated Pair: {current_pair[0]}, {current_pair[1]}")

            # Find path for this specific pair
            path_result = find_common_path(current_pair, TARGET_GOAL_STATES)

            if path_result is not None: # Path found (can be empty list [])
                common_path = path_result # Store the found path
                initial_states = current_pair # Store the SUCCESSFUL pair
                current_ui_state = "selecting" # Transition to next state
                print(f"Success on attempt {search_attempts}.")
                if not common_path:
                    message = "Found pair already in goal states! Click to view."
                else:
                    message = f"Found pair (Attempt {search_attempts})! Path: {len(common_path)} moves. Click a state."
            else:
                # Path not found, loop continues in 'searching' state
                # Pump events to allow exit/prevent freeze
                pygame.event.pump()
                # Optional small delay if search is too fast/CPU intensive
                # pygame.time.delay(10)

        # --- Drawing Logic ---
        screen.fill(DARK_BG) # Clear screen for drawing current state

        # Always Draw: Title, Message, Back Button
        title_surf = title_font.render("Blind Search Results", True, SECONDARY)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 60)))
        msg_surf = font.render(message, True, LIGHT_GRAY) # Use regular font for status msg
        screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH // 2, 100)))
        back_button.check_hover(mouse_pos)
        back_button.draw(screen, font)

        # Draw based on current UI state
        if current_ui_state == "selecting":
            # Draw the two found states side-by-side
            grid_cols = 2
            total_grid_w = WIDTH * 0.6
            puzzle_w = total_grid_w / grid_cols * 0.9
            puzzle_h = puzzle_w
            tile_size = puzzle_w / 3
            spacing_x = (total_grid_w / grid_cols) * 0.1
            start_x = (WIDTH - total_grid_w) / 2
            start_y = HEIGHT // 2 - puzzle_h // 2 # Vertically center the puzzles

            # CONFIRMED: This loop runs only for the items in initial_states (should be 2)
            if len(initial_states) == 2: # Draw only if we have the pair
                print(f"Drawing selection screen with {len(initial_states)} states.") # Debug print
                for i in range(len(initial_states)):
                    init_state = initial_states[i]
                    col = i # 0 or 1
                    puzzle_origin_x = start_x + col * (puzzle_w + spacing_x)
                    puzzle_origin_y = start_y

                    # Draw hover border
                    puzzle_rect_clickable = pygame.Rect(puzzle_origin_x, puzzle_origin_y, puzzle_w, puzzle_h)
                    if puzzle_rect_clickable.collidepoint(mouse_pos):
                         pygame.draw.rect(screen, PRIMARY, puzzle_rect_clickable.inflate(4,4), border_radius=5, width=2)

                    # Draw tiles within the puzzle area
                    for idx, val in enumerate(init_state):
                        r, c = divmod(idx, 3)
                        x_tile = puzzle_origin_x + c * tile_size
                        y_tile = puzzle_origin_y + r * tile_size
                        tile_rect = pygame.Rect(x_tile + 1, y_tile + 1, tile_size - 2, tile_size - 2)
                        if val != 9:
                            pygame.draw.rect(screen, TILE_BG, tile_rect, border_radius=3)
                            text = puzzle_font_small.render(str(val), True, SECONDARY)
                            text_rect = text.get_rect(center=tile_rect.center)
                            screen.blit(text, text_rect)
            else:
                 # This case should not happen if logic is correct
                 error_msg = info_font.render("Error: Incorrect number of states to display.", True, RED)
                 screen.blit(error_msg, error_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


            # Display common path (if not empty)
            if common_path:
                 path_str = "Common Path: " + " -> ".join(common_path)
                 path_surf = info_font.render(path_str, True, PRIMARY)
                 path_rect = path_surf.get_rect(center=(WIDTH // 2, 140)) # Below message
                 screen.blit(path_surf, path_rect)

        elif current_ui_state == "animating" or current_ui_state == "finished":
            # --- Animation / Finished State Drawing & Logic ---
            all_tiles_at_target = True
            if animating_tiles: # Ensure tiles exist
                for tile in animating_tiles:
                    if not tile.is_at_target(): all_tiles_at_target = False
                    tile.update()
                    tile.draw(screen, puzzle_font_large)
            else: # Should not happen in these states
                 error_msg = info_font.render("Error: No tiles to animate.", True, RED)
                 screen.blit(error_msg, error_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


            # Draw current move text during animation
            if current_ui_state == "animating" and common_path and current_move_index < len(common_path):
                 move_text = f"Move {current_move_index + 1}/{len(common_path)}: {common_path[current_move_index]}"
                 move_surf = move_font.render(move_text, True, PRIMARY)
                 move_rect = move_surf.get_rect(center=(WIDTH // 2, HEIGHT - 120))
                 screen.blit(move_surf, move_rect)

            # --- Progress Animation Logic ---
            if current_ui_state == "animating" and all_tiles_at_target and common_path:
                 # Check if there are more moves IN THE PATH to process
                 if current_move_index < len(common_path):
                      # Determine the state *after* the NEXT move to set targets
                      # First, find the state *after* the move that just finished animating
                      current_animated_state_tuple = initial_states[selected_state_index]
                      for move_idx in range(current_move_index + 1): # Apply moves up to and including the one just finished
                           temp_state = apply_move(current_animated_state_tuple, common_path[move_idx])
                           if temp_state is not None: current_animated_state_tuple = temp_state
                           else: print(f"ERROR: Invalid move '{common_path[move_idx]}' @ index {move_idx}"); current_ui_state = "finished"; message = "Anim Error"; break

                      # Increment index for the *next* move/state
                      current_move_index += 1

                      if current_ui_state != "finished" and current_move_index < len(common_path):
                           # Get the state AFTER the move we are about to animate
                           next_move = common_path[current_move_index]
                           next_animated_state_tuple = apply_move(current_animated_state_tuple, next_move)

                           if next_animated_state_tuple:
                               # Set new targets based on next_animated_state_tuple
                               next_animated_state_list = list(next_animated_state_tuple)
                               anim_tile_size = animating_tiles[0].size
                               anim_start_x = (WIDTH - anim_tile_size * 3) / 2
                               anim_start_y = (HEIGHT - anim_tile_size * 3) / 2 - 50
                               value_pos_map = {val: idx for idx, val in enumerate(next_animated_state_list)}

                               for tile in animating_tiles:
                                   if tile.value in value_pos_map:
                                       new_idx = value_pos_map[tile.value]
                                       r, c = divmod(new_idx, 3)
                                       target_x = anim_start_x + c * anim_tile_size
                                       target_y = anim_start_y + r * anim_tile_size
                                       tile.set_target(target_x, target_y)
                           else:
                               print(f"Error: Next move '{next_move}' invalid.")
                               current_ui_state = "finished"; message = "Anim Error"
                      elif current_ui_state != "finished":
                            # Just finished the last move, animation complete
                            current_ui_state = "finished"
                            message = f"State {selected_state_index + 1} animation finished!"
                 else: # current_move_index >= len(common_path) -> Animation finished
                       current_ui_state = "finished"
                       message = f"State {selected_state_index + 1} animation finished!"


        # --- Update Display ---
        pygame.display.flip()
        clock.tick(60)

    # --- End of Main Loop ---
    print("Exiting Blind Search.")


# --- Allow running blind.py directly for testing ---
if __name__ == "__main__":
    run_blind_search()
    pygame.quit()
    sys.exit()