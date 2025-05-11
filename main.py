import pygame
import sys
import importlib
import os
from collections import deque
import time
import traceback 
import subprocess


try:
    from algorithms import ALGORITHM_LIST
except ImportError:
    ALGORITHM_LIST = [
        ("Greedy Search", "greedy"), ("Greedy Search (Double Moves)", "greedy_double"),
        ("A* Search (Manhattan)", "a_star_manhattan"), ("A* Search (Manhattan, Double)", "a_star_manhattan_double"),
        ("A* Search (Misplaced)", "a_star_misplaced"), ("A* Search (Misplaced, Double)", "a_star_misplaced_double"),
        ("BFS (Breadth-First Search)", "bfs"), ("BFS (Double Moves)", "bfs_double"),
        ("UCS (Uniform Cost Search)", "ucs"), ("UCS (Double Moves)", "ucs_double"),
        ("Hill Climbing", "hill_climbing"), ("Hill Climbing (Double)", "hill_climbing_double"),
        ("Stochastic Hill Climbing", "stochastic_hc"), ("Stochastic Hill Climbing (Double)", "stochastic_hc_double"),
        ("DFS (Depth-First Search)", "dfs"), ("DFS (Double Moves)", "dfs_double"),
        ("Steepest Ascent Hill Climbing", "steepest_hc"), ("Steepest Ascent Hill Climbing (Double)", "steepest_hc_double"),
        ("IDDFS (Iterative Deepening DFS)", "iddfs"), ("IDDFS (Double Moves)", "iddfs_double"),
        ("IDA* Search", "ida_star"), ("IDA* (Double Moves)", "ida_star_double"),
        ("Beam Search", "beam_search"), ("QLearning", "q_learning"),
    ]
    print("Warning: Could not import ALGORITHM_LIST from algorithms package. Using default list.")
    if not os.path.exists('algorithms'): print("Error: 'algorithms' directory not found.")


DARK_BG = (44, 62, 80)         
PRIMARY = (26, 188, 156)       
PRIMARY_DARK = (22, 160, 133)  
SECONDARY = (236, 240, 241)    
GRAY = (52, 73, 94)            
LIGHT_GRAY = (149, 165, 166)   
TILE_BG = (63, 81, 107)        
TILE_SOLVED = (46, 204, 113)   
RED = (231, 76, 60)            


APPLE_MUSIC_RED_START = (255, 45, 85)  
APPLE_MUSIC_RED_END = (230, 25, 65)    

TILE_GRADIENTS = {
    1: (APPLE_MUSIC_RED_START, APPLE_MUSIC_RED_END), 
    2: ((100, 200, 255), (50, 150, 200)),    
    3: ((255, 180, 100), (200, 130, 50)),    
    4: ((103, 58, 183), (69, 39, 160)),     
    5: ((200, 150, 255), (150, 100, 200)),   
    6: ((255, 255, 100), (200, 200, 50)),    
    7: ((160, 82, 45), (120, 60, 30)),       
    8: ((255, 150, 200), (200, 100, 150)),   
}

GRADIENT_TILE_SOLVED_START_MAIN = (66, 224, 133) 
GRADIENT_TILE_SOLVED_END_MAIN = (26, 184, 93)   

GRADIENT_TILE_BG_START_MAIN = (83, 101, 127) 
GRADIENT_TILE_BG_END_MAIN = (43, 61, 87)     


DROPDOWN_ITEM_BG = (44, 62, 80)
DROPDOWN_ITEM_HOVER_BG = (70, 98, 127)
DROPDOWN_ITEM_SELECTED_BG = PRIMARY
DROPDOWN_BG = (52, 73, 94) 


GLOBAL_MARGIN = 20
TOP_BAR_HEIGHT = 70


PATH_DISPLAY_BOX_MARGIN_TOP = 20; PATH_DISPLAY_BOX_MARGIN_BOTTOM_FROM_BUTTONS = 20
PATH_DISPLAY_BOX_PADDING = 10; PATH_DISPLAY_MAX_VISIBLE_STEPS = 3
PATH_DISPLAY_LINE_SPACING = 5; MIN_PATH_BOX_HEIGHT = 80


SLIDER_TRACK_HEIGHT = 12
SLIDER_HANDLE_WIDTH = 30
SLIDER_HANDLE_HEIGHT = 24
SLIDER_PUZZLE_AREA_MARGIN_TOP = 20
SLIDER_WIDTH_PERCENTAGE = 0.4
MIN_ANIMATION_SPEED = 1
MAX_ANIMATION_SPEED = 1000
DEFAULT_ANIMATION_SPEED = 50


def get_inversions(state):
    state_without_blank = [x for x in state if x != 9]; inversions = 0
    for i in range(len(state_without_blank)):
        for j in range(i + 1, len(state_without_blank)):
            if state_without_blank[i] > state_without_blank[j]: inversions += 1
    return inversions
def is_solvable(state):
    if 9 not in state or len(state) != 9: return False
    return get_inversions(state) % 2 == 0
def is_valid_puzzle_state(state):
    return isinstance(state, (list, tuple)) and len(state) == 9 and sorted(state) == list(range(1, 10))
def get_neighbors(state):
    neighbors = []; s = list(state)
    try: blank_index = s.index(9)
    except ValueError: return []
    row, col = divmod(blank_index, 3); moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for dr, dc in moves:
        new_row, new_col = row + dr, col + dc
        if 0 <= new_row < 3 and 0 <= new_col < 3:
            new_index = new_row * 3 + new_col; new_s = s[:]
            new_s[blank_index], new_s[new_index] = new_s[new_index], new_s[blank_index]
            neighbors.append(tuple(new_s))
    return neighbors

class MessageBox:
    def __init__(self, width, height, title, message, button_text="OK"):
        self.rect = pygame.Rect((WIDTH - width) // 2, (HEIGHT - height) // 2, width, height)
        self.title = title; self.message = message; self.border_radius = 10; self.active = False
        button_width = 100; button_height = 40
        button_x = self.rect.x + (self.rect.width - button_width) // 2
        button_y = self.rect.bottom - button_height - 20
        self.ok_button = Button(button_x, button_y, button_width, button_height, button_text)
    def draw(self, screen, title_font, font, button_font):
        if not self.active: return
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 128)); screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, GRAY, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(screen, DARK_BG, self.rect.inflate(-4, -4), border_radius=self.border_radius)
        title_surface = title_font.render(self.title, True, SECONDARY); title_rect = title_surface.get_rect(centerx=self.rect.centerx, y=self.rect.y + 20); screen.blit(title_surface, title_rect)
        lines = self.message.split('\n'); start_y = self.rect.y + 70
        for i, line in enumerate(lines): msg_surf = font.render(line, True, LIGHT_GRAY); msg_rect = msg_surf.get_rect(centerx=self.rect.centerx, y=start_y + i * 30); screen.blit(msg_surf, msg_rect)
        self.ok_button.draw(screen, button_font)
    def check_hover(self, mouse_pos):
        if not self.active: return False
        return self.ok_button.check_hover(mouse_pos)
    def handle_event(self, event):
        if not self.active: return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ok_button.is_clicked(event.pos, True): self.active = False; return True
        return False

class AnimatedTile:
    def __init__(self, value, x, y, size):
        self.value = value; self.size = size; self.inner_size = int(size * 0.94)
        self.rect = pygame.Rect(x, y, size, size); self.inner_rect = pygame.Rect(0, 0, self.inner_size, self.inner_size); self.inner_rect.center = self.rect.center
        self.current_x = float(x); self.current_y = float(y); self.target_x = float(x); self.target_y = float(y)
        self.speed = 0.2
        self.is_solved_position = False 
        self.border_radius = 10
        self.is_final_solved_display = False 
    def set_target(self, x, y): self.target_x = float(x); self.target_y = float(y)
    def update(self):
        dx = self.target_x - self.current_x; dy = self.target_y - self.current_y
        if abs(dx) < 1 and abs(dy) < 1: self.current_x = self.target_x; self.current_y = self.target_y
        else: self.current_x += dx * self.speed; self.current_y += dy * self.speed
        self.rect.topleft = (int(self.current_x), int(self.current_y)); self.inner_rect.center = self.rect.center
    
    def draw(self, screen, font):
        if self.value == 9: return 

        tile_w = self.inner_rect.width
        tile_h = self.inner_rect.height

        is_globally_solved_and_stable = self.is_final_solved_display

        if tile_w <= 0 or tile_h <= 0: 
            if tile_w > 0 and tile_h > 0: 
                solid_color_fallback = TILE_BG 
                if is_globally_solved_and_stable: 
                    solid_color_fallback = TILE_SOLVED
                elif self.value == 1: 
                     solid_color_fallback = APPLE_MUSIC_RED_START
                elif self.is_solved_position: 
                    solid_color_fallback = TILE_SOLVED
                elif self.value in TILE_GRADIENTS:
                    solid_color_fallback = TILE_GRADIENTS[self.value][0]
                pygame.draw.rect(screen, solid_color_fallback, self.inner_rect, border_radius=self.border_radius)
            
            if self.value != 9 and font:
                text_surface = font.render(str(self.value), True, SECONDARY)
                text_rect = text_surface.get_rect(center=self.inner_rect.center)
                screen.blit(text_surface, text_rect)
            return

        if is_globally_solved_and_stable: 
            start_color = GRADIENT_TILE_SOLVED_START_MAIN
            end_color = GRADIENT_TILE_SOLVED_END_MAIN
        elif self.value == 1: 
            start_color = APPLE_MUSIC_RED_START
            end_color = APPLE_MUSIC_RED_END
        elif self.is_solved_position: 
            start_color = GRADIENT_TILE_SOLVED_START_MAIN
            end_color = GRADIENT_TILE_SOLVED_END_MAIN
        else:
            if self.value in TILE_GRADIENTS:
                start_color, end_color = TILE_GRADIENTS[self.value]
            else:
                start_color = GRADIENT_TILE_BG_START_MAIN
                end_color = GRADIENT_TILE_BG_END_MAIN

        gradient_surface = pygame.Surface(self.inner_rect.size)
        
        for y_grad in range(tile_h):
            ratio = y_grad / (tile_h - 1) if tile_h > 1 else 0.0
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            pygame.draw.line(gradient_surface, (r,g,b), (0, y_grad), (tile_w - 1, y_grad))

        gradient_surface = gradient_surface.convert_alpha()

        mask_surface = pygame.Surface(self.inner_rect.size, pygame.SRCALPHA)
        mask_surface.fill((0,0,0,0)) 
        pygame.draw.rect(mask_surface, (255,255,255,255), mask_surface.get_rect(), border_radius=self.border_radius)
        
        gradient_surface.blit(mask_surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        
        screen.blit(gradient_surface, self.inner_rect.topleft)
        
        if self.value != 9 and font:
            text_surface = font.render(str(self.value), True, SECONDARY)
            text_rect = text_surface.get_rect(center=self.inner_rect.center)
            screen.blit(text_surface, text_rect)

    def is_at_target(self): return abs(self.current_x - self.target_x) < 1 and abs(self.current_y - self.target_y) < 1

class Button:
     def __init__(self, x, y, width, height, text, color=PRIMARY, hover_color=PRIMARY_DARK, text_color=SECONDARY, border_radius=8):
         self.rect = pygame.Rect(x, y, width, height); self.text = text; self.color = color
         self.hover_color = hover_color; self.is_hovered = False; self.border_radius = border_radius
         self.text_color = text_color
     def draw(self, screen, font):
         color = self.hover_color if self.is_hovered else self.color
         pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
         text_surface = font.render(self.text, True, self.text_color); text_rect = text_surface.get_rect(center=self.rect.center); screen.blit(text_surface, text_rect)
     def check_hover(self, mouse_pos): self.is_hovered = self.rect.collidepoint(mouse_pos); return self.is_hovered
     def is_clicked(self, mouse_pos, mouse_click): return self.is_hovered and mouse_click

class Dropdown:
    def __init__(self, x, y, width, height, font, main_text_prefix, options_list, selected_index=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.main_text_prefix = main_text_prefix
        self.options = options_list
        self.selected_index = selected_index 
        self.current_display_text = self.options[self.selected_index][0]
        self.is_open = False
        self.hovered_option_index = -1 
        self.option_height = height
        self.border_radius = 8
        self.max_visible_options = 7 
        self.scroll_offset = 0
        self.list_bg_rect_cache = None 

    def get_selected_value(self):
        return self.options[self.selected_index][1]

    def get_selected_display_name(self):
        return self.options[self.selected_index][0]

    def handle_event(self, event, mouse_pos):
        clicked_item_or_toggled_dropdown = False
        
        if self.is_open and self.list_bg_rect_cache and self.list_bg_rect_cache.collidepoint(mouse_pos):
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self.options) - self.max_visible_options)
                self.scroll_offset -= event.y 
                self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
                clicked_item_or_toggled_dropdown = True 

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(mouse_pos):
                self.is_open = not self.is_open
                if not self.is_open: self.scroll_offset = 0 
                clicked_item_or_toggled_dropdown = True
            elif self.is_open:
                start_y = self.rect.bottom + 5
                for i_visible in range(min(len(self.options) - self.scroll_offset, self.max_visible_options)):
                    true_option_index = self.scroll_offset + i_visible
                    
                    option_rect = pygame.Rect(self.rect.x, start_y + i_visible * self.option_height, self.rect.width, self.option_height)
                    if option_rect.collidepoint(mouse_pos):
                        self.selected_index = true_option_index
                        self.current_display_text = self.options[true_option_index][0]
                        self.is_open = False
                        self.scroll_offset = 0 
                        clicked_item_or_toggled_dropdown = True
                        break 
                else: 
                    self.is_open = False
                    self.scroll_offset = 0 
            
        if self.is_open:
            self.hovered_option_index = -1 
            start_y = self.rect.bottom + 5
            if self.list_bg_rect_cache and self.list_bg_rect_cache.collidepoint(mouse_pos):
                 for i_visible in range(min(len(self.options) - self.scroll_offset, self.max_visible_options)):
                    true_option_index_hover = self.scroll_offset + i_visible
                    option_rect_hover = pygame.Rect(self.rect.x, start_y + i_visible * self.option_height, self.rect.width, self.option_height)
                    if option_rect_hover.collidepoint(mouse_pos):
                        self.hovered_option_index = true_option_index_hover
                        break
        
        return clicked_item_or_toggled_dropdown

    def draw(self, screen):
        main_button_color = PRIMARY_DARK if self.is_open else PRIMARY
        pygame.draw.rect(screen, main_button_color, self.rect, border_radius=self.border_radius)
        
        full_text = f"{self.main_text_prefix}: {self.current_display_text}"
        available_text_width = self.rect.width - 30 
        text_surface = self.font.render(full_text, True, SECONDARY)
        if text_surface.get_width() > available_text_width:
            temp_text = self.current_display_text
            while self.font.render(f"{self.main_text_prefix}: {temp_text}...", True, SECONDARY).get_width() > available_text_width and len(temp_text) > 5: 
                temp_text = temp_text[:-1]
            full_text = f"{self.main_text_prefix}: {temp_text}..."
            text_surface = self.font.render(full_text, True, SECONDARY)
        text_rect = text_surface.get_rect(center=self.rect.center); text_rect.left = self.rect.left + 10 
        screen.blit(text_surface, text_rect)

        arrow_points = [(self.rect.right - 20, self.rect.centery - 3), (self.rect.right - 10, self.rect.centery - 3), (self.rect.right - 15, self.rect.centery + 3)]
        if self.is_open: arrow_points = [(self.rect.right - 20, self.rect.centery + 3), (self.rect.right - 10, self.rect.centery + 3), (self.rect.right - 15, self.rect.centery - 3)]
        pygame.draw.polygon(screen, SECONDARY, arrow_points)

        if self.is_open:
            start_y = self.rect.bottom + 5
            num_actually_visible = min(len(self.options), self.max_visible_options)
            list_display_height = num_actually_visible * self.option_height
            
            self.list_bg_rect_cache = pygame.Rect(self.rect.x, start_y, self.rect.width, list_display_height)
            pygame.draw.rect(screen, DROPDOWN_BG, self.list_bg_rect_cache, border_radius=self.border_radius)

            for i_visible in range(min(len(self.options) - self.scroll_offset, self.max_visible_options)):
                true_option_index = self.scroll_offset + i_visible
                if not (0 <= true_option_index < len(self.options)): continue 

                display_name, _ = self.options[true_option_index]
                option_rect = pygame.Rect(self.rect.x, start_y + i_visible * self.option_height, self.rect.width, self.option_height)
                
                bg_color = DROPDOWN_ITEM_BG
                if true_option_index == self.selected_index:
                    bg_color = DROPDOWN_ITEM_SELECTED_BG
                elif true_option_index == self.hovered_option_index:
                    bg_color = DROPDOWN_ITEM_HOVER_BG
                
                current_item_is_first_visible = (i_visible == 0)
                current_item_is_last_visible = (i_visible == min(len(self.options) - self.scroll_offset, self.max_visible_options) - 1)
                
                pygame.draw.rect(screen, bg_color, option_rect,
                                 border_top_left_radius=self.border_radius if current_item_is_first_visible else 0,
                                 border_top_right_radius=self.border_radius if current_item_is_first_visible else 0,
                                 border_bottom_left_radius=self.border_radius if current_item_is_last_visible else 0,
                                 border_bottom_right_radius=self.border_radius if current_item_is_last_visible else 0)

                opt_text_surface = self.font.render(display_name, True, SECONDARY)
                available_opt_text_width = option_rect.width - 20
                if opt_text_surface.get_width() > available_opt_text_width:
                    temp_opt_text = display_name
                    while self.font.render(temp_opt_text + "...", True, SECONDARY).get_width() > available_opt_text_width and len(temp_opt_text) > 3:
                        temp_opt_text = temp_opt_text[:-1]
                    opt_text_surface = self.font.render(temp_opt_text + "...", True, SECONDARY)
                opt_text_rect = opt_text_surface.get_rect(midleft=(option_rect.x + 10, option_rect.centery))
                screen.blit(opt_text_surface, opt_text_rect)

class SpeedSlider:
    def __init__(self, handle_width, handle_height, track_color, handle_color, min_speed_val, max_speed_val, initial_speed_val):
        self.min_speed = min_speed_val
        self.max_speed = max_speed_val
        self.current_speed = initial_speed_val
        self.track_rect = pygame.Rect(0,0,0,0) 
        self.handle_rect = pygame.Rect(0,0, handle_width, handle_height) 
        self.slider_min_x = 0 
        self.slider_max_x = 0 
        self.slider_range_x = 0
        self.track_color = track_color
        self.handle_color = handle_color
        self.is_dragging = False
        self.active = False 

    def update_layout(self, x_track_start, y_center, track_width): 
        self.track_rect = pygame.Rect(x_track_start, y_center - SLIDER_TRACK_HEIGHT // 2, track_width, SLIDER_TRACK_HEIGHT)
        self.slider_min_x = self.track_rect.left + self.handle_rect.width // 2
        self.slider_max_x = self.track_rect.right - self.handle_rect.width // 2
        self.slider_range_x = self.slider_max_x - self.slider_min_x
        if self.slider_range_x <= 0: self.slider_range_x = 1 
        self._update_handle_pos_from_speed() 

    def _update_handle_pos_from_speed(self):
        if not self.track_rect.height: return 
        if self.max_speed == self.min_speed: percentage = 0.5
        else: percentage = (self.current_speed - self.min_speed) / (self.max_speed - self.min_speed)
        handle_center_x = self.slider_min_x + percentage * self.slider_range_x
        self.handle_rect.center = (handle_center_x, self.track_rect.centery)

    def _update_speed_from_handle_pos(self):
        handle_x = self.handle_rect.centerx
        percentage = (handle_x - self.slider_min_x) / self.slider_range_x
        self.current_speed = self.min_speed + percentage * (self.max_speed - self.min_speed)
        self.current_speed = max(self.min_speed, min(self.max_speed, self.current_speed))

    def handle_event(self, event, mouse_pos):
        global switch_time 
        if not self.active: return False
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(mouse_pos):
                self.is_dragging = True; changed = True
            elif self.track_rect.collidepoint(mouse_pos): 
                self.handle_rect.centerx = max(self.slider_min_x, min(mouse_pos[0], self.slider_max_x))
                self._update_speed_from_handle_pos()
                switch_time = int(self.current_speed)
                self.is_dragging = True; changed = True 
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging: self.is_dragging = False; changed = True
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self.handle_rect.centerx = max(self.slider_min_x, min(mouse_pos[0], self.slider_max_x))
                self._update_speed_from_handle_pos()
                switch_time = int(self.current_speed)
                changed = True
        return changed

    def draw(self, screen, font_param):
        if not self.active or not self.track_rect.height: return 
        pygame.draw.rect(screen, self.track_color, self.track_rect, border_radius=SLIDER_TRACK_HEIGHT // 2)
        pygame.draw.rect(screen, self.handle_color, self.handle_rect, border_radius=5)
        speed_text = f"Tốc độ: {int(self.current_speed)}ms"
        text_surf = font_param.render(speed_text, True, LIGHT_GRAY)
        text_rect = text_surf.get_rect(midleft=(self.track_rect.right + 15, self.track_rect.centery))
        screen.blit(text_surf, text_rect)
        fast_label = font_param.render("Nhanh", True, LIGHT_GRAY)
        screen.blit(fast_label, fast_label.get_rect(midright=(self.track_rect.left - 10, self.track_rect.centery)))

    def get_speed(self): return int(self.current_speed)


def draw_top_bar(screen, title_font, game_title_text, algo_dropdown):
    top_bar_rect = pygame.Rect(0, 0, WIDTH, TOP_BAR_HEIGHT)
    pygame.draw.rect(screen, GRAY, top_bar_rect) 

    title_surf = title_font.render(game_title_text, True, SECONDARY)
    title_rect = title_surf.get_rect(midleft=(GLOBAL_MARGIN, TOP_BAR_HEIGHT / 2))
    screen.blit(title_surf, title_rect)

    algo_dropdown.draw(screen)

def draw_main_menu_content(screen, title_font_param, font_param, button_font_param,
                           solve_btn, edit_btn, blind_search_btn, fill_anim_btn,
                           current_start_state):
    content_start_y_offset = TOP_BAR_HEIGHT + GLOBAL_MARGIN
    content_area_width = WIDTH - 2 * GLOBAL_MARGIN
    content_center_x = GLOBAL_MARGIN + content_area_width // 2
    instr_line_height = font_param.get_height()
    num_instr_lines = 3 
    instr_block_height = num_instr_lines * instr_line_height + (num_instr_lines - 1) * 5
    button_height_val = solve_btn.rect.height
    num_buttons = 4
    button_spacing = 15
    button_block_height = num_buttons * button_height_val + (num_buttons - 1) * button_spacing
    preview_label_height = font_param.get_height()
    mini_tile_size = 35
    mini_padding_vert = 2
    mini_tile_total_h = mini_tile_size + mini_padding_vert
    preview_grid_height = mini_tile_total_h * 3 - mini_padding_vert
    spacing_instr_button = 40
    spacing_button_preview_label = 40
    spacing_preview_label_grid = 15
    total_content_height = (instr_block_height + spacing_instr_button +
                            button_block_height + spacing_button_preview_label +
                            preview_label_height + spacing_preview_label_grid + preview_grid_height)
    available_content_height = HEIGHT - content_start_y_offset - GLOBAL_MARGIN
    current_y = content_start_y_offset + max(0, (available_content_height - total_content_height) // 2)
    explanation = ["Nhấn nút 'Bắt đầu' bên dưới để giải.", "Hoặc chọn các nút chức năng khác.", f"(Trạng thái đích: {GOAL_STATE})"]
    instr_y = current_y
    for i, text in enumerate(explanation):
        line = font_param.render(text, True, LIGHT_GRAY)
        line_rect = line.get_rect(centerx=content_center_x, top=instr_y + i * (instr_line_height + 5))
        screen.blit(line, line_rect)
    current_y += instr_block_height + spacing_instr_button
    button_x = content_center_x - solve_btn.rect.width // 2
    solve_btn.rect.topleft = (button_x, current_y)
    edit_btn.rect.topleft = (button_x, solve_btn.rect.bottom + button_spacing)
    blind_search_btn.rect.topleft = (button_x, edit_btn.rect.bottom + button_spacing)
    fill_anim_btn.rect.topleft = (button_x, blind_search_btn.rect.bottom + button_spacing)
    solve_btn.draw(screen, button_font_param); edit_btn.draw(screen, button_font_param)
    blind_search_btn.draw(screen, button_font_param); fill_anim_btn.draw(screen, button_font_param)
    current_y += button_block_height + spacing_button_preview_label
    label = font_param.render("Trạng thái ban đầu hiện tại:", True, SECONDARY)
    label_rect = label.get_rect(centerx=content_center_x, top=current_y)
    screen.blit(label, label_rect)
    current_y += preview_label_height + spacing_preview_label_grid
    mini_width = (mini_tile_size + mini_padding_vert) * 3 - mini_padding_vert
    mini_start_x = content_center_x - mini_width // 2
    mini_start_y = current_y
    for i, val in enumerate(current_start_state):
        row, col = divmod(i, 3)
        x = mini_start_x + col * (mini_tile_size + mini_padding_vert)
        y = mini_start_y + row * (mini_tile_size + mini_padding_vert)
        tile_rect = pygame.Rect(x, y, mini_tile_size, mini_tile_size)
        
        bg_color = TILE_BG if val != 9 else DARK_BG 
        pygame.draw.rect(screen, bg_color, tile_rect, border_radius=5)
        if val != 9:
            text_surf = button_font_param.render(str(val), True, SECONDARY)
            text_rect = text_surf.get_rect(center=tile_rect.center); screen.blit(text_surf, text_rect)

def init_tiles(state):
    info_path_area_width = min(WIDTH * 0.35, 400) + GLOBAL_MARGIN 
    puzzle_area_max_width = WIDTH - info_path_area_width - GLOBAL_MARGIN 
    slider_total_height = SLIDER_HANDLE_HEIGHT + SLIDER_PUZZLE_AREA_MARGIN_TOP
    puzzle_grid_start_y = TOP_BAR_HEIGHT + GLOBAL_MARGIN + slider_total_height
    puzzle_area_height = HEIGHT - puzzle_grid_start_y - GLOBAL_MARGIN - 70 
    tile_size = min(puzzle_area_max_width / 3, puzzle_area_height / 3) * 0.9
    puzzle_grid_width = tile_size * 3
    puzzle_area_left_x = GLOBAL_MARGIN
    start_x = puzzle_area_left_x + (puzzle_area_max_width - puzzle_grid_width) / 2
    start_y = puzzle_grid_start_y
    tiles_list = []
    for i, val in enumerate(state):
        row, col = divmod(i, 3)
        x_tile = start_x + col * tile_size; y_tile = start_y + row * tile_size
        tile_obj = AnimatedTile(val, x_tile, y_tile, tile_size)
        tile_obj.is_solved_position = (val != 9 and val == GOAL_STATE[i])
        tiles_list.append(tile_obj)
    return tiles_list, start_x, start_y, puzzle_grid_width, tile_size

def update_tiles(tiles_list, new_state, goal_state, puzzle_start_x, puzzle_start_y, tile_size_val):
    if not tiles_list: return
    value_pos_map = {val: i for i, val in enumerate(new_state)}
    for tile_obj in tiles_list:
        if tile_obj.value in value_pos_map:
            new_index = value_pos_map[tile_obj.value]; row, col = divmod(new_index, 3)
            target_x = puzzle_start_x + col * tile_size_val
            target_y = puzzle_start_y + row * tile_size_val
            tile_obj.set_target(target_x, target_y); tile_obj.is_solved_position = (tile_obj.value != 9 and tile_obj.value == goal_state[new_index])
        tile_obj.is_final_solved_display = False 

def draw_info_box(screen, font_param, info_font_param, steps_found, path_length, current_step, total_steps, algorithm_name, elapsed_time=None, box_rect_param=None):
    if box_rect_param: info_box_rect = box_rect_param
    else: 
        box_width = min(WIDTH * 0.35, 400); box_height = 350
        box_x = WIDTH - box_width - GLOBAL_MARGIN 
        box_y = TOP_BAR_HEIGHT + GLOBAL_MARGIN    
        info_box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
    pygame.draw.rect(screen, GRAY, info_box_rect, border_radius=10)
    pygame.draw.rect(screen, DARK_BG, info_box_rect.inflate(-4, -4), border_radius=10)
    title_surface = font_param.render("Thông tin giải", True, SECONDARY) 
    title_rect = title_surface.get_rect(centerx=info_box_rect.centerx, y=info_box_rect.y + 20)
    screen.blit(title_surface, title_rect) 
    info_lines = [f"Thuật toán: {algorithm_name}", f"Node đã duyệt: {steps_found if steps_found is not None else 'N/A'}",
                  f"Độ dài đường đi: {path_length if path_length is not None else 'N/A'}",
                  f"Bước hiện tại: {current_step}/{total_steps if total_steps is not None else 'N/A'}"]
    if elapsed_time is not None: info_lines.append(f"Thời gian tìm kiếm: {elapsed_time:.3f} s")
    line_y = info_box_rect.y + 60
    for text in info_lines: line_surf = info_font_param.render(text, True, LIGHT_GRAY); screen.blit(line_surf, (info_box_rect.x + 20, line_y)); line_y += 30
    if total_steps is not None and total_steps > 0:
        progress_rect_bg = pygame.Rect(info_box_rect.x + 20, info_box_rect.bottom - 60, info_box_rect.width - 40, 20)
        pygame.draw.rect(screen, GRAY, progress_rect_bg, border_radius=10)
        progress_ratio = min(1.0, max(0.0, current_step / total_steps)); progress_width = int(progress_ratio * progress_rect_bg.width)
        if progress_width > 0: progress_rect_fg = pygame.Rect(progress_rect_bg.x, progress_rect_bg.y, progress_width, progress_rect_bg.height); pygame.draw.rect(screen, PRIMARY, progress_rect_fg, border_radius=10)

def draw_path_display_box(screen, title_font_param, text_font_param, path_param, current_step_index_param, box_rect_param): 
    if not path_param or not box_rect_param or box_rect_param.height < MIN_PATH_BOX_HEIGHT // 2: return
    pygame.draw.rect(screen, GRAY, box_rect_param, border_radius=10)
    pygame.draw.rect(screen, DARK_BG, box_rect_param.inflate(-4, -4), border_radius=10)
    box_title_surface = title_font_param.render("Các bước giải", True, SECONDARY) 
    box_title_rect = box_title_surface.get_rect(centerx=box_rect_param.centerx, y=box_rect_param.y + PATH_DISPLAY_BOX_PADDING)
    screen.blit(box_title_surface, box_title_rect); line_y = box_title_rect.bottom + 10 
    num_steps_before = (PATH_DISPLAY_MAX_VISIBLE_STEPS - 1) // 2; num_steps_after = PATH_DISPLAY_MAX_VISIBLE_STEPS - 1 - num_steps_before
    start_display_idx = current_step_index_param - num_steps_before; end_display_idx = current_step_index_param + num_steps_after + 1 
    if start_display_idx < 0: end_display_idx += abs(start_display_idx); start_display_idx = 0
    if end_display_idx > len(path_param): start_display_idx -= (end_display_idx - len(path_param)); end_display_idx = len(path_param); start_display_idx = max(0, start_display_idx) 
    displayed_step_indices = list(range(start_display_idx, end_display_idx))
    for step_to_show_idx in displayed_step_indices:
        if not (0 <= step_to_show_idx < len(path_param)): continue
        state = path_param[step_to_show_idx]; state_str = str(state); text_color = LIGHT_GRAY; prefix = f"B{step_to_show_idx}: " 
        if step_to_show_idx == current_step_index_param: prefix = "Hiện tại: "; text_color = PRIMARY 
        full_text = f"{prefix}{state_str}"; available_width = box_rect_param.width - 2 * PATH_DISPLAY_BOX_PADDING
        temp_surface = text_font_param.render(full_text, True, text_color)
        if temp_surface.get_width() > available_width:
            char_width_estimate = text_font_param.size("a")[0]; char_width_estimate = char_width_estimate if char_width_estimate > 0 else 10
            max_state_len = len(state_str) - (temp_surface.get_width() - available_width) // char_width_estimate - 3 
            max_state_len = max(5, max_state_len); short_state_str = state_str[:max_state_len] + "..." if len(state_str) > max_state_len else state_str
            full_text = f"{prefix}{short_state_str}"; temp_surface = text_font_param.render(full_text, True, text_color)
        text_draw_rect = temp_surface.get_rect(left = box_rect_param.x + PATH_DISPLAY_BOX_PADDING, top = line_y)
        if text_draw_rect.bottom > box_rect_param.bottom - PATH_DISPLAY_BOX_PADDING + 5: break 
        screen.blit(temp_surface, text_draw_rect); line_y += text_font_param.get_height() + PATH_DISPLAY_LINE_SPACING

def init_editor_tiles(state, offset_x, offset_y, tile_size): 
    tiles_list = []; 
    for i, val in enumerate(state):
        row, col = divmod(i, 3); x_tile = offset_x + col * tile_size; y_tile = offset_y + row * tile_size
        tile_obj = AnimatedTile(val, x_tile, y_tile, tile_size); 
        tile_obj.is_solved_position = False; 
        tiles_list.append(tile_obj)
    return tiles_list

def draw_editor(screen, editor_tiles_list, editor_state, selected_idx, title_font_param, font_param, info_font_param, puzzle_font_param, button_font_param):
    editor_title_y = TOP_BAR_HEIGHT + GLOBAL_MARGIN + 20
    title_render_editor = title_font_param.render("Chỉnh sửa trạng thái ban đầu", True, SECONDARY)
    screen.blit(title_render_editor, title_render_editor.get_rect(centerx=WIDTH // 2, y=editor_title_y)) 
    instructions = ["Click vào ô để chọn, nhập số (1-9) để thay đổi.", "Số nhập vào sẽ đổi chỗ với số hiện tại trong ô.",
                   "Phải chứa đủ 1-9 và có thể giải được.", "Nhấn ENTER để lưu, ESC để hủy."]
    line_y = editor_title_y + title_render_editor.get_height() + 20
    for text in instructions:
        line = info_font_param.render(text, True, LIGHT_GRAY)
        screen.blit(line, line.get_rect(centerx=WIDTH // 2, y=line_y)); line_y += 30
    
    if not editor_tiles_list: return None, None

    tile_size = editor_tiles_list[0].size; puzzle_width = tile_size * 3; puzzle_height = tile_size * 3
    start_x_editor = (WIDTH - puzzle_width) // 2; start_y_puzzle_editor = line_y + 20 
    
    for i, tile_obj in enumerate(editor_tiles_list): 
         row, col = divmod(i, 3)
         tile_obj.current_x = start_x_editor + col * tile_size
         tile_obj.current_y = start_y_puzzle_editor + row * tile_size
         tile_obj.target_x = tile_obj.current_x 
         tile_obj.target_y = tile_obj.current_y
         tile_obj.update() 
         
         tile_obj.is_solved_position = False
         tile_obj.is_final_solved_display = False 
         tile_obj.draw(screen, puzzle_font_param) 

         if i == selected_idx:
             highlight_rect = tile_obj.rect.inflate(6, 6); pygame.draw.rect(screen, PRIMARY, highlight_rect, border_radius=12, width=3)
    
    is_valid = is_valid_puzzle_state(editor_state); solvable = is_solvable(tuple(editor_state)) if is_valid else False
    status_text = "Trạng thái không hợp lệ (thiếu/trùng số 1-9)" if not is_valid else f"Trạng thái {'CÓ THỂ' if solvable else 'KHÔNG THỂ'} giải được"
    status_color = RED if not is_valid or not solvable else TILE_SOLVED 
    status_surf = font_param.render(status_text, True, status_color)
    status_rect = status_surf.get_rect(center=(WIDTH // 2, start_y_puzzle_editor + puzzle_height + 40)); 
    screen.blit(status_surf, status_rect)
    
    button_width_val = 150; button_height_val = 40; button_y_val = status_rect.bottom + 30
    save_btn = Button(WIDTH // 2 - button_width_val - 10, button_y_val, button_width_val, button_height_val, "Lưu (Enter)")
    cancel_btn = Button(WIDTH // 2 + 10, button_y_val, button_width_val, button_height_val, "Hủy (Esc)")
    save_btn.check_hover(pygame.mouse.get_pos()); cancel_btn.check_hover(pygame.mouse.get_pos())
    save_btn.draw(screen, button_font_param); cancel_btn.draw(screen, button_font_param)
    return save_btn, cancel_btn

def draw_single_puzzle(screen, state, x, y, tile_size, font_param): 
    padding = max(1, int(tile_size * 0.02)); inner_tile_size = tile_size - 2 * padding
    for i, val in enumerate(state):
        row, col = divmod(i, 3); tile_x = x + col * tile_size + padding; tile_y = y + row * tile_size + padding
        tile_rect = pygame.Rect(tile_x, tile_y, inner_tile_size, inner_tile_size)
        bg_color = TILE_BG if val != 9 else DARK_BG 
        pygame.draw.rect(screen, bg_color, tile_rect, border_radius=5)
        if val != 9: text_surf = font_param.render(str(val), True, SECONDARY); text_rect = text_surf.get_rect(center=tile_rect.center); screen.blit(text_surf, text_rect)

def draw_blind_preview(screen, title_font_param, font_param, info_font_param, button_font_param, state1, state2, start_btn, back_btn):
    preview_title_y = TOP_BAR_HEIGHT + GLOBAL_MARGIN + 20
    title_render_blind = title_font_param.render("Xem trước Tìm kiếm Mù", True, SECONDARY)
    screen.blit(title_render_blind, title_render_blind.get_rect(centerx=WIDTH // 2, y=preview_title_y)) 
    explanation = ["Đây là 2 ví dụ về trạng thái ban đầu có thể được sử dụng.", "(Tìm kiếm thực tế sẽ tạo ngẫu nhiên 10 trạng thái tương tự).", "Nhấn 'Bắt đầu' để chạy tìm kiếm mù thực sự."]
    line_y = preview_title_y + title_render_blind.get_height() + 20
    for text in explanation:
        line = info_font_param.render(text, True, LIGHT_GRAY)
        screen.blit(line, line.get_rect(centerx=WIDTH // 2, y=line_y)); line_y += 30
    max_tile_size = 150; preview_tile_size = min(WIDTH * 0.15, HEIGHT * 0.20, max_tile_size); puzzle_size = preview_tile_size * 3
    total_width_needed = puzzle_size * 2 + 100; start_puzzles_x = (WIDTH - total_width_needed) // 2
    puzzle1_x = start_puzzles_x; puzzle2_x = start_puzzles_x + puzzle_size + 100; puzzles_y = line_y + 20 
    draw_single_puzzle(screen, state1, puzzle1_x, puzzles_y, preview_tile_size, puzzle_font); 
    draw_single_puzzle(screen, state2, puzzle2_x, puzzles_y, preview_tile_size, puzzle_font); 
    label1_surf = font_param.render("Trạng thái ví dụ 1", True, SECONDARY); label2_surf = font_param.render("Trạng thái ví dụ 2", True, SECONDARY)
    screen.blit(label1_surf, label1_surf.get_rect(centerx=puzzle1_x + puzzle_size // 2, bottom=puzzles_y - 10))
    screen.blit(label2_surf, label2_surf.get_rect(centerx=puzzle2_x + puzzle_size // 2, bottom=puzzles_y - 10))
    button_y_val = puzzles_y + puzzle_size + 50
    start_btn.rect.centerx = WIDTH // 2 - start_btn.rect.width // 2 - 10; start_btn.rect.y = button_y_val
    back_btn.rect.centerx = WIDTH // 2 + back_btn.rect.width // 2 + 10; back_btn.rect.y = button_y_val
    start_btn.check_hover(pygame.mouse.get_pos()); back_btn.check_hover(pygame.mouse.get_pos()); start_btn.draw(screen, button_font_param); back_btn.draw(screen, button_font_param)

def start_solving(selected_algorithm_index_from_dropdown, start_state, goal_state, message_box): 
    global current_view, path, steps_found, elapsed_time, tiles, current_step, last_switch, puzzle_layout_info, selected_algorithm_index
    selected_algorithm_index = selected_algorithm_index_from_dropdown 
    if not is_valid_puzzle_state(start_state):
        message_box.title="Lỗi Trạng Thái"; message_box.message=f"Trạng thái bắt đầu không hợp lệ:\n{start_state}"; message_box.active=True; return False
    if not is_solvable(start_state):
        message_box.title="Lỗi Trạng Thái"; message_box.message=f"Trạng thái bắt đầu không thể giải:\n{start_state}"; message_box.active=True; return False
    algorithm_name, module_name = ALGORITHM_LIST[selected_algorithm_index] 
    print(f"Attempting solve: {algorithm_name}, State: {start_state}")
    try:
        module = importlib.import_module(f"algorithms.{module_name}")
        start_time_solve = time.time(); solve_result = module.solve(start_state, goal_state); elapsed_time = time.time() - start_time_solve
        path, steps_found = None, None 
        if isinstance(solve_result, tuple) and len(solve_result) > 0:
            path = solve_result[0]; steps_found = solve_result[1] if len(solve_result) > 1 and isinstance(solve_result[1], int) else None
        elif isinstance(solve_result, list): path = solve_result
        if path and isinstance(path, list) and len(path) > 0:
            path_length = len(path) - 1; print(f"Solution found: {path_length} steps. Search took {elapsed_time:.3f}s.")
            if steps_found is None: steps_found = path_length 
            current_view = "solver"
            tiles, p_start_x, p_start_y, p_width, p_tile_size = init_tiles(start_state) 
            puzzle_layout_info = {"x": p_start_x, "y": p_start_y, "width": p_width, "tile_size": p_tile_size} 
            current_step = 0; last_switch = pygame.time.get_ticks(); return True
        else: print(f"No solution found by {algorithm_name}. Search took {elapsed_time:.3f}s."); message_box.title="Không tìm thấy"; message_box.message=f"{algorithm_name} không tìm thấy đường đi."; message_box.active=True; return False
    except ImportError: print(f"Import Error: algorithms.{module_name}"); message_box.title="Lỗi Import"; message_box.message=f"Không thể tải thuật toán:\n'{module_name}'."; message_box.active=True; return False
    except AttributeError: print(f"Attribute Error: 'solve' not in algorithms.{module_name}"); message_box.title="Lỗi Thuật Toán"; message_box.message=f"Thuật toán '{module_name}' thiếu hàm 'solve'."; message_box.active=True; return False
    except Exception as e: print(f"Error solving with {algorithm_name}: {e}"); traceback.print_exc(); message_box.title="Lỗi Thực Thi"; message_box.message=f"Lỗi khi chạy {algorithm_name}:\n{e}"; message_box.active=True; return False

def main():
    global START_STATE, screen, GOAL_STATE, WIDTH, HEIGHT, font, title_font, puzzle_font, button_font, info_font
    global current_view, path, steps_found, elapsed_time, tiles, current_step, last_switch, switch_time 
    global puzzle_layout_info, selected_algorithm_index 

    clock = pygame.time.Clock(); running = True; current_view = "menu"
    path = None; current_step = 0; auto_mode = True; last_switch = 0
    switch_time = DEFAULT_ANIMATION_SPEED 
    tiles = None; steps_found = None; elapsed_time = None; 
    selected_algorithm_index = 0 
    puzzle_layout_info = {} 

    dropdown_options = [(name, idx) for idx, (name, _) in enumerate(ALGORITHM_LIST)]
    dropdown_width = 380 
    dropdown_height = 40
    dropdown_x = WIDTH - dropdown_width - GLOBAL_MARGIN
    dropdown_y = (TOP_BAR_HEIGHT - dropdown_height) // 2
    algorithm_dropdown = Dropdown(dropdown_x, dropdown_y, dropdown_width, dropdown_height,
                                  button_font, "Thuật toán", dropdown_options, selected_algorithm_index)

    current_start_state_editor = list(START_STATE)
    editor_tiles = [] 
    editor_selected_idx = -1; message_box = MessageBox(500, 250, "Thông báo", "") 
    speed_slider = SpeedSlider(SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT, GRAY, PRIMARY,
                               MIN_ANIMATION_SPEED, MAX_ANIMATION_SPEED, DEFAULT_ANIMATION_SPEED)
    solver_button_width = 120; solver_button_height = 40
    buttons_y_bottom = HEIGHT - GLOBAL_MARGIN - solver_button_height
    buttons_total_width = 4 * solver_button_width + 3 * 20
    solver_buttons_start_x = (WIDTH - buttons_total_width) // 2
    auto_btn = Button(solver_buttons_start_x, buttons_y_bottom, solver_button_width, solver_button_height, "Auto: On")
    next_btn = Button(auto_btn.rect.right + 20, buttons_y_bottom, solver_button_width, solver_button_height, "Tiếp theo")
    reset_btn = Button(next_btn.rect.right + 20, buttons_y_bottom, solver_button_width, solver_button_height, "Làm lại")
    back_menu_btn = Button(reset_btn.rect.right + 20, buttons_y_bottom, solver_button_width, solver_button_height, "Quay lại Menu")
    menu_button_width = 280; menu_button_height = 45 
    solve_btn = Button(0, 0, menu_button_width, menu_button_height, "Bắt đầu giải") 
    edit_btn = Button(0, 0, menu_button_width, menu_button_height, "Chỉnh sửa trạng thái")
    blind_search_btn = Button(0, 0, menu_button_width, menu_button_height, "Tìm kiếm mù")
    fill_anim_btn = Button(0, 0, menu_button_width, menu_button_height, "Hoạt ảnh điền số") 
    editor_save_btn = None; editor_cancel_btn = None
    BLIND_PREVIEW_STATE_1 = (1, 2, 3, 4, 5, 6, 7, 9, 8); BLIND_PREVIEW_STATE_2 = (1, 2, 3, 4, 5, 9, 7, 8, 6)
    blind_preview_button_width = 220; blind_preview_button_height = 45
    start_blind_run_btn = Button(0, 0, blind_preview_button_width, blind_preview_button_height, "Bắt đầu Tìm kiếm mù")
    back_menu_from_preview_btn = Button(0, 0, 150, blind_preview_button_height, "Quay lại Menu")
    game_title_text = "8-Puzzle Solver"

    while running:
        mouse_pos = pygame.mouse.get_pos(); mouse_click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            
            dropdown_handled_event = algorithm_dropdown.handle_event(event, mouse_pos)
            if dropdown_handled_event:
                new_selected_idx = algorithm_dropdown.get_selected_value()
                if new_selected_idx != selected_algorithm_index:
                    selected_algorithm_index = new_selected_idx
                    print(f"Selected Algorithm (Dropdown): {ALGORITHM_LIST[selected_algorithm_index][0]}")
                continue 

            if message_box.active:
                if message_box.handle_event(event): continue
            
            if current_view == "solver": speed_slider.handle_event(event, mouse_pos)
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: mouse_click = True
                        
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if current_view == "editor": current_view = "menu"
                    elif current_view == "solver": current_view = "menu"; path = None; tiles = None; speed_slider.active = False
                    elif current_view == "blind_preview": current_view = "menu"
                    else: running = False 
                elif current_view == "editor":
                    if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        if is_valid_puzzle_state(current_start_state_editor) and is_solvable(tuple(current_start_state_editor)): START_STATE = tuple(current_start_state_editor); current_view = "menu"
                        else: message_box.title="Lỗi Lưu"; message_box.message="Trạng thái không hợp lệ hoặc không giải được."; message_box.active = True
                    elif editor_selected_idx != -1 and pygame.K_1 <= event.key <= pygame.K_9:
                        new_val = event.key - pygame.K_0; current_val_at_selected = current_start_state_editor[editor_selected_idx]
                        if new_val != 9 and new_val != current_val_at_selected: 
                            try:
                                existing_idx_of_new_val = current_start_state_editor.index(new_val)
                                current_start_state_editor[existing_idx_of_new_val] = current_val_at_selected
                                current_start_state_editor[editor_selected_idx] = new_val
                                editor_tiles[existing_idx_of_new_val].value = current_val_at_selected
                                editor_tiles[editor_selected_idx].value = new_val
                            except ValueError: pass 
                            editor_selected_idx = -1 
        
        if current_view == "menu": speed_slider.active = False 
        elif current_view == "solver": speed_slider.active = True
        
        if mouse_click and not (algorithm_dropdown.is_open and algorithm_dropdown.list_bg_rect_cache and algorithm_dropdown.list_bg_rect_cache.collidepoint(mouse_pos)):
            if current_view == "editor":
                if editor_save_btn and editor_save_btn.is_clicked(mouse_pos, True):
                     if is_valid_puzzle_state(current_start_state_editor) and is_solvable(tuple(current_start_state_editor)): START_STATE = tuple(current_start_state_editor); current_view = "menu"
                     else: message_box.title="Lỗi Lưu"; message_box.message="Trạng thái không hợp lệ hoặc không giải được."; message_box.active = True
                elif editor_cancel_btn and editor_cancel_btn.is_clicked(mouse_pos, True): current_view = "menu"
                else: 
                    editor_selected_idx = -1
                    if editor_tiles: 
                        for i, tile_obj in enumerate(editor_tiles): 
                            if tile_obj.rect.collidepoint(mouse_pos): editor_selected_idx = i; break
            elif current_view == "menu":
                 if solve_btn.is_clicked(mouse_pos, True):
                     start_solving(algorithm_dropdown.get_selected_value(), START_STATE, GOAL_STATE, message_box)
                 elif edit_btn.is_clicked(mouse_pos, True):
                     current_start_state_editor = list(START_STATE)
                     editor_max_h = HEIGHT - (TOP_BAR_HEIGHT + GLOBAL_MARGIN + 280) 
                     editor_max_w = WIDTH - 2 * GLOBAL_MARGIN - 100 
                     e_tile_size = min(editor_max_w / 3, editor_max_h / 3) * 0.9
                     editor_grid_w = e_tile_size * 3
                     editor_grid_start_x = (WIDTH - editor_grid_w) // 2
                     editor_tiles = init_editor_tiles(current_start_state_editor, editor_grid_start_x, 0, e_tile_size) 
                     editor_selected_idx = -1; current_view = "editor"
                 elif blind_search_btn.is_clicked(mouse_pos, True): current_view = "blind_preview"
                 elif fill_anim_btn.is_clicked(mouse_pos, True): 
                     print("Launching Fill Animation Visualizer (fill.py)...")
                     try: subprocess.Popen([sys.executable, "fill.py"]) 
                     except FileNotFoundError: message_box.title = "Lỗi"; message_box.message = "Không tìm thấy file 'fill.py'."; message_box.active = True
                     except Exception as e: message_box.title = "Lỗi"; message_box.message = f"Lỗi khi chạy fill.py:\n{e}"; message_box.active = True
            elif current_view == "blind_preview":
                 if start_blind_run_btn.is_clicked(mouse_pos, True):
                     print("Launching Blind Search logic...")
                     try: import blind; blind.run_blind_search(); current_view = "menu"; pygame.display.set_caption(game_title_text); print("Returned from Blind Search.")
                     except ImportError: message_box.title="Lỗi Import"; message_box.message="Không tìm thấy file 'blind.py'."; message_box.active=True
                     except Exception as e: print(f"Error running Blind Search: {e}"); traceback.print_exc(); message_box.title="Lỗi Tìm Kiếm Mù"; message_box.message=f"Lỗi xảy ra khi chạy tìm kiếm mù:\n{e}"; message_box.active=True
                 elif back_menu_from_preview_btn.is_clicked(mouse_pos, True): current_view = "menu"
            elif current_view == "solver":
                 if auto_btn.is_clicked(mouse_pos, True): auto_mode = not auto_mode; auto_btn.text = "Auto: On" if auto_mode else "Auto: Off";
                 elif next_btn.is_clicked(mouse_pos, True):
                     if not auto_mode and path and current_step < len(path) - 1: current_step += 1; update_tiles(tiles, path[current_step], GOAL_STATE, puzzle_layout_info["x"], puzzle_layout_info["y"], puzzle_layout_info["tile_size"])
                 elif reset_btn.is_clicked(mouse_pos, True):
                     if path: current_step = 0; last_switch = pygame.time.get_ticks(); update_tiles(tiles, path[0], GOAL_STATE, puzzle_layout_info["x"], puzzle_layout_info["y"], puzzle_layout_info["tile_size"])
                 elif back_menu_btn.is_clicked(mouse_pos, True): current_view = "menu"; path = None; tiles = None; speed_slider.active = False
        
        screen.fill(DARK_BG)
        draw_top_bar(screen, title_font, game_title_text, algorithm_dropdown)

        if current_view == "editor":
            if not editor_tiles: 
                editor_max_h = HEIGHT - (TOP_BAR_HEIGHT + GLOBAL_MARGIN + 280) 
                editor_max_w = WIDTH - 2 * GLOBAL_MARGIN - 100 
                e_tile_size = min(editor_max_w / 3, editor_max_h / 3) * 0.9
                editor_grid_w = e_tile_size * 3
                editor_grid_start_x = (WIDTH - editor_grid_w) // 2
                editor_tiles = init_editor_tiles(current_start_state_editor, editor_grid_start_x, 0, e_tile_size)

            editor_save_btn, editor_cancel_btn = draw_editor(screen, editor_tiles, current_start_state_editor, editor_selected_idx, title_font, font, info_font, puzzle_font, button_font)
        elif current_view == "menu":
            draw_main_menu_content(screen, title_font, font, button_font, solve_btn, edit_btn, blind_search_btn, fill_anim_btn, START_STATE)
            solve_btn.check_hover(mouse_pos); edit_btn.check_hover(mouse_pos); blind_search_btn.check_hover(mouse_pos); fill_anim_btn.check_hover(mouse_pos) 
        elif current_view == "blind_preview":
            draw_blind_preview(screen, title_font, font, info_font, button_font, BLIND_PREVIEW_STATE_1, BLIND_PREVIEW_STATE_2, start_blind_run_btn, back_menu_from_preview_btn)
        elif current_view == "solver":
            info_box_width_val = min(WIDTH * 0.35, 400) 
            info_box_x_val = WIDTH - info_box_width_val - GLOBAL_MARGIN 
            info_box_y_val = TOP_BAR_HEIGHT + GLOBAL_MARGIN 
            info_box_height_val = 350 
            current_info_box_rect = pygame.Rect(info_box_x_val, info_box_y_val, info_box_width_val, info_box_height_val)
            path_display_box_x_val = info_box_x_val
            path_display_box_y_val = current_info_box_rect.bottom + PATH_DISPLAY_BOX_MARGIN_TOP
            solver_buttons_top_y = auto_btn.rect.top 
            path_display_box_bottom_limit = solver_buttons_top_y - PATH_DISPLAY_BOX_MARGIN_BOTTOM_FROM_BUTTONS
            path_display_box_calculated_height = path_display_box_bottom_limit - path_display_box_y_val
            path_display_box_height_val = max(MIN_PATH_BOX_HEIGHT, path_display_box_calculated_height)
            current_path_display_box_rect = None
            if path_display_box_height_val >= MIN_PATH_BOX_HEIGHT: 
                 current_path_display_box_rect = pygame.Rect(path_display_box_x_val, path_display_box_y_val, info_box_width_val, path_display_box_height_val)
            if tiles and puzzle_layout_info: 
                puzzle_actual_start_x = puzzle_layout_info.get("x", GLOBAL_MARGIN + 20) 
                puzzle_grid_actual_width = puzzle_layout_info.get("width", 300) 
                slider_track_width_val = puzzle_grid_actual_width * SLIDER_WIDTH_PERCENTAGE
                slider_center_x = puzzle_actual_start_x + puzzle_grid_actual_width / 2
                slider_track_start_x = slider_center_x - slider_track_width_val / 2
                slider_y_center = TOP_BAR_HEIGHT + GLOBAL_MARGIN + SLIDER_HANDLE_HEIGHT // 2 + SLIDER_PUZZLE_AREA_MARGIN_TOP // 2
                speed_slider.update_layout(slider_track_start_x, slider_y_center, slider_track_width_val)
                speed_slider.draw(screen, button_font)
            if tiles:
                 for tile_obj in tiles: tile_obj.update() 
            now = pygame.time.get_ticks()
            
            is_final_solved_and_stable_state = False
            if path and tiles and current_step == len(path) -1: 
                if all(tile_obj.is_at_target() for tile_obj in tiles if tile_obj):
                     is_final_solved_and_stable_state = True

            if path and tiles and puzzle_layout_info: 
                 all_at_target = all(tile_obj.is_at_target() for tile_obj in tiles if tile_obj) 
                 effective_switch_time = max(1, switch_time)
                 if auto_mode and current_step < len(path) - 1 and all_at_target and (now - last_switch >= effective_switch_time):
                     elapsed_since_last_switch = now - last_switch
                     num_steps_to_advance = 0
                     if effective_switch_time > 0:
                         num_steps_to_advance = elapsed_since_last_switch // effective_switch_time
                     if num_steps_to_advance > 0:
                         for _ in range(num_steps_to_advance):
                             if current_step < len(path) - 1: current_step += 1
                             else: break
                         update_tiles(tiles, path[current_step], GOAL_STATE, puzzle_layout_info["x"], puzzle_layout_info["y"], puzzle_layout_info["tile_size"])
                         last_switch = now 
                     elif elapsed_since_last_switch >= effective_switch_time and effective_switch_time < 16 : 
                         if current_step < len(path) - 1:
                             current_step += 1
                             update_tiles(tiles, path[current_step], GOAL_STATE, puzzle_layout_info["x"], puzzle_layout_info["y"], puzzle_layout_info["tile_size"])
                             last_switch = now
                 for tile_obj in tiles:
                     if tile_obj: 
                        tile_obj.is_final_solved_display = is_final_solved_and_stable_state
                        tile_obj.draw(screen, puzzle_font)
            for btn in [auto_btn, next_btn, reset_btn, back_menu_btn]: btn.check_hover(mouse_pos); btn.draw(screen, button_font)
            if path: 
                path_length = len(path) - 1
                algo_name_for_info = ALGORITHM_LIST[selected_algorithm_index][0] if 0 <= selected_algorithm_index < len(ALGORITHM_LIST) else "N/A"
                draw_info_box(screen, font, info_font, steps_found, path_length, current_step, path_length, algo_name_for_info, elapsed_time, current_info_box_rect)
                if current_path_display_box_rect:
                    draw_path_display_box(screen, font, info_font, path, current_step, current_path_display_box_rect)
        if message_box.active: message_box.draw(screen, title_font, font, button_font); message_box.check_hover(mouse_pos)
        pygame.display.flip(); clock.tick(60)
    pygame.quit(); sys.exit()

if __name__ == "__main__":
    pygame.init(); pygame.font.init()
    try:
        screen_info = pygame.display.Info(); WIDTH, HEIGHT = screen_info.current_w, screen_info.current_h
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
    except pygame.error: print("Warning: Fullscreen failed. Using 1280x720 windowed."); WIDTH, HEIGHT = 1280, 720; screen = pygame.display.set_mode((WIDTH, HEIGHT))
    game_title_main = "8-Puzzle Solver" 
    pygame.display.set_caption(game_title_main)
    try:
        font_name_default = "Arial"; 
        if font_name_default not in pygame.font.get_fonts(): 
            available = pygame.font.get_fonts(); common = ["freesans", "helvetica", "dejavusans", "verdana", "sans"]; font_name_default = pygame.font.get_default_font();
            for cf in common:
                 if cf.lower() in [f.lower() for f in available]: font_name_default = cf; break
        print(f"Using font: {font_name_default}")
        font = pygame.font.SysFont(font_name_default, 22); title_font = pygame.font.SysFont(font_name_default, 32, bold=True) 
        puzzle_font = pygame.font.SysFont(font_name_default, 60, bold=True) 
        button_font = pygame.font.SysFont(font_name_default, 20); info_font = pygame.font.SysFont(font_name_default, 22)
    except Exception as e: print(f"Font error: {e}. Using default."); font = pygame.font.Font(None, 24); title_font = pygame.font.Font(None, 36); puzzle_font = pygame.font.Font(None, 60); button_font = pygame.font.Font(None, 20); info_font = pygame.font.Font(None, 22)
    START_STATE = (1, 8, 2, 9, 4, 3, 7, 6, 5) 
    GOAL_STATE = (1, 2, 3, 4, 5, 6, 7, 8, 9)
    if not is_solvable(START_STATE): print(f"Warning: Default START_STATE {START_STATE} is not solvable!")
    main()