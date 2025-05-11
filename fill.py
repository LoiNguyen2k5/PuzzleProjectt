import pygame
import sys
import threading
import time
import math
import random
from collections import deque 
import traceback


DARK_BG = (42, 48, 60)          
PRIMARY = (45, 212, 191)        
PRIMARY_DARK = (38, 166, 154)   
SECONDARY = (255, 255, 255)     

LIGHT_GRAY = (148, 163, 184)    

TILE_BG = (71, 85, 105)         
TILE_EMPTY_BG = (62, 76, 95)    

RED = (209, 49, 49)             
YELLOW = (240, 180, 0)          
TILE_SOLVED = PRIMARY           


GRADIENT_TILE_FILL_START = (94, 112, 136)  
GRADIENT_TILE_FILL_END = (58, 70, 89)      

MESSAGE_BOX_OUTER_BG = (51, 58, 76) 


WIDTH, HEIGHT = 0, 0 
screen = None
clock = None
font = None
title_font = None
puzzle_font = None
button_font = None
info_font = None

EMPTY_SLOT = 0 

def is_valid_puzzle_state(state):
    """Kiểm tra xem state có phải hoán vị hợp lệ của 1-9 không."""
    return isinstance(state, (list, tuple)) and len(state) == 9 and sorted(state) == list(range(1, 10))

class Button:
     def __init__(self, x, y, width, height, text, color=PRIMARY, hover_color=PRIMARY_DARK):
         self.rect = pygame.Rect(x, y, width, height); self.text = text; self.color = color
         self.hover_color = hover_color; self.is_hovered = False; self.border_radius = 8
     def draw(self, screen, font):
         color = self.hover_color if self.is_hovered else self.color
         pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
         text_surface = font.render(self.text, True, SECONDARY); text_rect = text_surface.get_rect(center=self.rect.center); screen.blit(text_surface, text_rect)
     def check_hover(self, mouse_pos): self.is_hovered = self.rect.collidepoint(mouse_pos); return self.is_hovered
     def is_clicked(self, mouse_pos, mouse_click): return self.is_hovered and mouse_click

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
        pygame.draw.rect(screen, MESSAGE_BOX_OUTER_BG, self.rect, border_radius=self.border_radius)
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

class AnimatedNumberTile:
    """Tile riêng cho animation điền số, có hiệu ứng nảy."""
    def __init__(self, value, x, y, size):
        self.value = value 
        self.target_value = value 
        self.size = size
        self.inner_size = int(size * 0.94)
        self.rect = pygame.Rect(x, y, size, size)
        self.inner_rect = pygame.Rect(0, 0, self.inner_size, self.inner_size)
        self.inner_rect.center = self.rect.center
        self.border_radius_base = 10 

        self.is_appearing = False
        self.appear_start_time = 0
        self.appear_duration = 0.4 
        self.current_scale = 1.0
        self.current_y_offset = 0
        self.highlight = False 

    def set_value(self, new_value, trigger_animation=False):
        """Đặt giá trị mới và tùy chọn kích hoạt animation."""
        if new_value != self.value:
            self.target_value = new_value
            if trigger_animation and new_value != EMPTY_SLOT:
                self.is_appearing = True
                self.appear_start_time = time.time()
                self.current_scale = 1.5 
                self.current_y_offset = -self.size * 0.2 
                self.highlight = True 
            else:
                self.value = new_value
                self.is_appearing = False


    def update(self):
        """Cập nhật trạng thái animation nảy."""
        if self.is_appearing:
            elapsed = time.time() - self.appear_start_time
            if elapsed >= self.appear_duration:
                self.is_appearing = False
                self.value = self.target_value 
                self.current_scale = 1.0
                self.current_y_offset = 0
            else:
                progress = elapsed / self.appear_duration
                ease_out_factor = 1.0 - (1.0 - progress) ** 3 
                self.current_scale = 1.0 + 0.5 * (1.0 - ease_out_factor)
                self.current_y_offset = -self.size * 0.2 * (1.0 - ease_out_factor)
                self.value = self.target_value

    def draw(self, screen, font):
        """Vẽ tile với hiệu ứng scale, offset và gradient."""
        draw_rect = self.inner_rect.copy()
        scaled_size = int(self.inner_size * self.current_scale)
        draw_rect.width = scaled_size
        draw_rect.height = scaled_size
        draw_rect.centerx = self.inner_rect.centerx
        draw_rect.centery = self.inner_rect.centery + int(self.current_y_offset)
        
        current_border_radius = int(self.border_radius_base * self.current_scale)

        use_gradient = False
        solid_color = None

        if self.value == EMPTY_SLOT:
            solid_color = TILE_EMPTY_BG
        elif self.highlight and not self.is_appearing: 
            solid_color = YELLOW
        else: 
            use_gradient = True
            start_color_grad = GRADIENT_TILE_FILL_START
            end_color_grad = GRADIENT_TILE_FILL_END
        
        if draw_rect.width > 0 and draw_rect.height > 0: 
            if use_gradient:
                gradient_surface = pygame.Surface(draw_rect.size)
                tile_h = draw_rect.height
                for y_grad in range(tile_h):
                    ratio = y_grad / (tile_h - 1) if tile_h > 1 else 0.0
                    r = int(start_color_grad[0] * (1 - ratio) + end_color_grad[0] * ratio)
                    g = int(start_color_grad[1] * (1 - ratio) + end_color_grad[1] * ratio)
                    b = int(start_color_grad[2] * (1 - ratio) + end_color_grad[2] * ratio)
                    pygame.draw.line(gradient_surface, (r, g, b), (0, y_grad), (draw_rect.width - 1, y_grad))
                
                gradient_surface = gradient_surface.convert_alpha()
                mask_surface = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
                mask_surface.fill((0,0,0,0))
                pygame.draw.rect(mask_surface, (255,255,255,255), mask_surface.get_rect(), border_radius=current_border_radius)
                gradient_surface.blit(mask_surface, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
                screen.blit(gradient_surface, draw_rect.topleft)
            elif solid_color:
                pygame.draw.rect(screen, solid_color, draw_rect, border_radius=current_border_radius)

        if self.value != EMPTY_SLOT:
            scaled_font_size = int(font.get_height() * self.current_scale * 1.1)
            if scaled_font_size > 0 : 
                try:
                    scaled_font = pygame.font.SysFont(font.get_name(), scaled_font_size, bold=True)
                except: 
                    scaled_font = pygame.font.Font(None, scaled_font_size)
                text = scaled_font.render(str(self.value), True, SECONDARY) 
                text_rect = text.get_rect(center=draw_rect.center)
                screen.blit(text, text_rect)

        if self.highlight and self.is_appearing:
             if draw_rect.width > 3 and draw_rect.height > 3: 
                pygame.draw.rect(screen, YELLOW, draw_rect, border_radius=current_border_radius, width=3)


animation_path = [] 
backtrack_target_state = []
backtrack_thread = None
backtrack_running = False
backtrack_finished = False
backtrack_success = False

def backtrack_fill_recursive(index, current_grid_state, used_numbers):
    """Hàm đệ quy điền số hướng tới backtrack_target_state."""
    global animation_path, backtrack_target_state, backtrack_running

    if not backtrack_running: return False 

    if index == 9:
        return list(current_grid_state) == list(backtrack_target_state)

    correct_num = backtrack_target_state[index]

    if correct_num in used_numbers:
        print(f"Lỗi logic hoặc target state không hợp lệ: Số {correct_num} đã dùng tại index {index}")
        return False 

    current_grid_state[index] = correct_num
    used_numbers.add(correct_num)
    animation_path.append(list(current_grid_state)) 

    found = backtrack_fill_recursive(index + 1, current_grid_state, used_numbers)

    if found:
        return True 

    if backtrack_running: 
        used_numbers.remove(correct_num)
        current_grid_state[index] = EMPTY_SLOT 
        animation_path.append(list(current_grid_state)) 

    return False 

def run_backtracking_thread(target_state):
    """Chạy backtracking trong một thread riêng."""
    global animation_path, backtrack_target_state, backtrack_running, backtrack_finished, backtrack_success
    backtrack_target_state = target_state
    backtrack_running = True
    backtrack_finished = False
    backtrack_success = False
    animation_path.clear()

    initial_grid = [EMPTY_SLOT] * 9
    used = set()
    animation_path.append(list(initial_grid)) 

    try:
        backtrack_success = backtrack_fill_recursive(0, initial_grid, used)
    except Exception as e:
        print(f"Lỗi trong thread backtracking: {e}")
        traceback.print_exc() 
        backtrack_success = False
    finally:
        backtrack_running = False
        backtrack_finished = True
        print(f"Backtracking finished. Success: {backtrack_success}, Path length: {len(animation_path)}")
        if not animation_path: 
             animation_path.append([EMPTY_SLOT] * 9)


def draw_grid(screen, tiles, puzzle_font):
    """Vẽ lưới các ô số."""
    for tile in tiles:
        tile.draw(screen, puzzle_font)

def draw_target_editor(screen, editor_tiles, editor_state, selected_idx, title_font, font, info_font, puzzle_font, button_font, start_btn, back_btn):
    """Vẽ giao diện chỉnh sửa trạng thái đích."""
    screen.fill(DARK_BG) 
    title = title_font.render("Chọn Trạng Thái Đích", True, SECONDARY) 
    screen.blit(title, title.get_rect(centerx=WIDTH // 2, y=70))
    instructions = ["Click ô để chọn, nhập số (1-9) để thay đổi.",
                   "Số nhập sẽ đổi chỗ với số hiện tại.",
                   "Phải là hoán vị hợp lệ của 1-9.",
                   "Nhấn 'Bắt đầu hoạt ảnh' để xem.",]
    line_y = 120
    for text in instructions: line = info_font.render(text, True, LIGHT_GRAY); screen.blit(line, line.get_rect(centerx=WIDTH // 2, y=line_y)); line_y += 30 

    if not editor_tiles: return

    tile_size = editor_tiles[0].size
    puzzle_width = tile_size * 3; puzzle_height = tile_size * 3
    start_x_editor_grid = (WIDTH - puzzle_width) // 2; start_y_editor_grid = line_y + 40 

    for i, tile in enumerate(editor_tiles):
        row, col = divmod(i, 3)
        tile.rect.topleft = (start_x_editor_grid + col * tile_size, start_y_editor_grid + row * tile_size)
        tile.inner_rect.center = tile.rect.center
        tile.draw(screen, puzzle_font) 
        if i == selected_idx:
            highlight_rect = tile.rect.inflate(6, 6)
            pygame.draw.rect(screen, YELLOW, highlight_rect, border_radius=int(tile.border_radius_base + 2), width=3)


    is_valid = is_valid_puzzle_state(editor_state)
    status_text = "Trạng thái hợp lệ (1-9)" if is_valid else "Trạng thái không hợp lệ (thiếu/trùng số 1-9)"
    status_color = TILE_SOLVED if is_valid else RED 
    status_surf = font.render(status_text, True, status_color)
    status_rect = status_surf.get_rect(center=(WIDTH // 2, start_y_editor_grid + puzzle_height + 40))
    screen.blit(status_surf, status_rect)

    button_y = status_rect.bottom + 30
    button_total_width = start_btn.rect.width + back_btn.rect.width + 20
    start_btn.rect.topleft = (WIDTH // 2 - button_total_width // 2, button_y)
    back_btn.rect.topleft = (start_btn.rect.right + 20, button_y)

    start_btn.check_hover(pygame.mouse.get_pos())
    back_btn.check_hover(pygame.mouse.get_pos())
    start_btn.draw(screen, button_font) 
    back_btn.draw(screen, button_font)

def draw_filling_animation(screen, anim_tiles, current_step, total_steps, target_state, auto_mode, puzzle_font, font, info_font, button_font, auto_btn, next_btn, reset_btn, back_btn):
    """Vẽ giao diện hoạt ảnh điền số."""
    screen.fill(DARK_BG) 
    title_surf = title_font.render("Hoạt ảnh điền số Backtracking", True, SECONDARY) 
    screen.blit(title_surf, title_surf.get_rect(centerx=WIDTH // 2, y=50))

    grid_start_y = 150 
    if anim_tiles:
        tile_s = anim_tiles[0].size
        puzzle_w = tile_s * 3
        puzzle_h = tile_s * 3
        start_x_anim_grid = (WIDTH - puzzle_w) // 2
        
        for i, tile in enumerate(anim_tiles): 
            row, col = divmod(i,3)
            tile.rect.topleft = (start_x_anim_grid + col * tile_s, grid_start_y + row * tile_s)
            tile.inner_rect.center = tile.rect.center
        draw_grid(screen, anim_tiles, puzzle_font) 
        info_y_start = grid_start_y + puzzle_h + 40
    else:
        info_y_start = grid_start_y + 200 

    target_str = ", ".join(map(str, target_state)) if target_state else "N/A"
    info_text_list = [
        f"Trạng thái đích: ({target_str})",
        f"Bước: {current_step} / {total_steps}",
        f"Trạng thái: {'Đang chạy...' if not backtrack_finished else ('Hoàn thành!' if backtrack_success else 'Không thành công/Lỗi')}"
    ]
    for i, text_line in enumerate(info_text_list):
        line_surf = info_font.render(text_line, True, LIGHT_GRAY) 
        screen.blit(line_surf, line_surf.get_rect(centerx=WIDTH // 2, y=info_y_start + i * 30))

    button_y_anim = info_y_start + len(info_text_list) * 30 + 30
    button_total_width_anim = auto_btn.rect.width + next_btn.rect.width + reset_btn.rect.width + back_btn.rect.width + 3 * 20
    start_buttons_x_anim = (WIDTH - button_total_width_anim) // 2

    auto_btn.rect.topleft = (start_buttons_x_anim, button_y_anim)
    next_btn.rect.topleft = (auto_btn.rect.right + 20, button_y_anim)
    reset_btn.rect.topleft = (next_btn.rect.right + 20, button_y_anim)
    back_btn.rect.topleft = (reset_btn.rect.right + 20, button_y_anim)

    auto_btn.text = "Auto: On" if auto_mode else "Auto: Off"

    for btn_item in [auto_btn, next_btn, reset_btn, back_btn]:
        btn_item.check_hover(pygame.mouse.get_pos())
        btn_item.draw(screen, button_font) 

def init_number_tiles(state_list, base_x, base_y, tile_item_size):
    """Khởi tạo danh sách các AnimatedNumberTile."""
    tiles_list = []
    for i, val_item in enumerate(state_list):
        row_idx, col_idx = divmod(i, 3)
        x_pos = base_x + col_idx * tile_item_size
        y_pos = base_y + row_idx * tile_item_size
        tile_obj = AnimatedNumberTile(val_item, x_pos, y_pos, tile_item_size)
        tiles_list.append(tile_obj)
    return tiles_list

def update_animation_tiles(anim_tiles_list, prev_state_list, current_state_list):
    """Cập nhật giá trị và kích hoạt animation cho các ô thay đổi."""
    if not anim_tiles_list or len(prev_state_list) != 9 or len(current_state_list) != 9:
        return

    for i in range(9):
        tile_changed = (prev_state_list[i] != current_state_list[i])
        anim_tiles_list[i].highlight = False 

        if tile_changed:
            is_filling = (prev_state_list[i] == EMPTY_SLOT and current_state_list[i] != EMPTY_SLOT)
            is_emptying = (prev_state_list[i] != EMPTY_SLOT and current_state_list[i] == EMPTY_SLOT)
            
            anim_tiles_list[i].set_value(current_state_list[i], trigger_animation=is_filling)
            
            if is_emptying: 
                anim_tiles_list[i].highlight = True 
            elif is_filling: 
                pass 

def fill_main():
    global screen, clock, font, title_font, puzzle_font, button_font, info_font
    global backtrack_thread, backtrack_running, backtrack_finished, backtrack_success, animation_path

    current_view = "target_editor" 

    target_state_tuple = tuple(range(1, 10)) 
    editable_target_state_list = list(target_state_tuple)
    editor_selected_idx = -1
    
    base_tile_size_editor = min(WIDTH * 0.15, HEIGHT * 0.20) 
    editor_puzzle_w = base_tile_size_editor * 3
    editor_grid_start_x = (WIDTH - editor_puzzle_w) // 2
    editor_grid_start_y = 280 
    editor_tiles_list = init_number_tiles(editable_target_state_list, editor_grid_start_x, editor_grid_start_y, base_tile_size_editor)

    animation_tiles_list = []
    base_tile_size_anim = min(WIDTH * 0.2, HEIGHT * 0.25) 
    anim_puzzle_w = base_tile_size_anim * 3
    anim_grid_start_x = (WIDTH - anim_puzzle_w) // 2
    anim_grid_start_y = 150
    
    current_animation_step_idx = 0
    auto_mode_active = True
    last_switch_time_ms = 0
    switch_interval_ms = 300 

    editor_btn_w = 200; editor_btn_h = 45
    start_anim_btn_obj = Button(0, 0, editor_btn_w, editor_btn_h, "Bắt đầu hoạt ảnh")
    back_main_btn_editor_obj = Button(0, 0, 180, editor_btn_h, "Về Menu Chính")
    
    anim_btn_w = 120; anim_btn_h = 40
    auto_btn_obj = Button(0, 0, anim_btn_w, anim_btn_h, "Auto: On")
    next_btn_obj = Button(0, 0, anim_btn_w, anim_btn_h, "Tiếp theo")
    reset_btn_obj = Button(0, 0, anim_btn_w, anim_btn_h, "Reset")
    back_editor_btn_obj = Button(0, 0, anim_btn_w + 20, anim_btn_h, "Chọn Lại Đích")

    message_box_obj = MessageBox(450, 200, "Thông báo", "") 

    running_loop = True
    while running_loop:
        mouse_pos_current = pygame.mouse.get_pos()
        mouse_btn_click = False

        for event_item in pygame.event.get():
            if event_item.type == pygame.QUIT:
                running_loop = False
                if backtrack_thread and backtrack_thread.is_alive():
                    backtrack_running = False 
                    backtrack_thread.join(timeout=0.5) 

            if message_box_obj.active:
                if message_box_obj.handle_event(event_item): continue

            if event_item.type == pygame.MOUSEBUTTONDOWN and event_item.button == 1:
                mouse_btn_click = True

            if current_view == "target_editor":
                if event_item.type == pygame.KEYDOWN:
                    if event_item.key == pygame.K_ESCAPE:
                        running_loop = False 
                    elif editor_selected_idx != -1 and pygame.K_1 <= event_item.key <= pygame.K_9:
                        new_val_input = event_item.key - pygame.K_0
                        current_val_editor = editable_target_state_list[editor_selected_idx]
                        if new_val_input != current_val_editor:
                            try:
                                swap_idx_editor = editable_target_state_list.index(new_val_input)
                                editable_target_state_list[editor_selected_idx] = new_val_input
                                editable_target_state_list[swap_idx_editor] = current_val_editor
                                editor_tiles_list[editor_selected_idx].set_value(new_val_input, trigger_animation=True) 
                                editor_tiles_list[swap_idx_editor].set_value(current_val_editor, trigger_animation=True)   
                            except ValueError:
                                message_box_obj.message = f"Số {new_val_input} không tồn tại để hoán đổi?"; message_box_obj.active = True
                        editor_selected_idx = -1 

                if mouse_btn_click:
                    if start_anim_btn_obj.is_clicked(mouse_pos_current, True):
                        if is_valid_puzzle_state(editable_target_state_list):
                            target_state_tuple = tuple(editable_target_state_list)
                            if backtrack_thread is None or not backtrack_thread.is_alive():
                                print("Bắt đầu backtracking thread...")
                                animation_path.clear()
                                current_animation_step_idx = 0
                                backtrack_finished = False 
                                backtrack_success = False 
                                backtrack_thread = threading.Thread(target=run_backtracking_thread, args=(target_state_tuple,), daemon=True)
                                backtrack_thread.start()
                                current_view = "filling_animation"
                                animation_tiles_list = init_number_tiles([EMPTY_SLOT] * 9, anim_grid_start_x, anim_grid_start_y, base_tile_size_anim)
                                if animation_tiles_list and animation_path:
                                    update_animation_tiles(animation_tiles_list, [EMPTY_SLOT]*9, animation_path[0])
                            else:
                                print("Thread backtracking đang chạy!")
                        else:
                            message_box_obj.message = "Trạng thái đích không hợp lệ (1-9)."; message_box_obj.active = True
                    elif back_main_btn_editor_obj.is_clicked(mouse_pos_current, True):
                        running_loop = False 
                    else:
                        editor_selected_idx = -1
                        for i, tile_item_editor in enumerate(editor_tiles_list):
                            if tile_item_editor.rect.collidepoint(mouse_pos_current):
                                editor_selected_idx = i
                                break

            elif current_view == "filling_animation":
                if event_item.type == pygame.KEYDOWN:
                    if event_item.key == pygame.K_ESCAPE:
                        current_view = "target_editor" 
                        if backtrack_thread and backtrack_thread.is_alive():
                            backtrack_running = False
                            backtrack_thread.join(timeout=0.5)
                        backtrack_thread = None 
                        backtrack_finished = True 

                if mouse_btn_click:
                    if auto_btn_obj.is_clicked(mouse_pos_current, True):
                        auto_mode_active = not auto_mode_active
                        if auto_mode_active: last_switch_time_ms = time.time() * 1000
                    elif next_btn_obj.is_clicked(mouse_pos_current, True) and not auto_mode_active:
                        if backtrack_finished and animation_path and current_animation_step_idx < len(animation_path) - 1:
                            current_animation_step_idx += 1
                            prev_st_anim = animation_path[current_animation_step_idx - 1]
                            curr_st_anim = animation_path[current_animation_step_idx]
                            update_animation_tiles(animation_tiles_list, prev_st_anim, curr_st_anim)
                    elif reset_btn_obj.is_clicked(mouse_pos_current, True):
                        current_animation_step_idx = 0
                        last_switch_time_ms = time.time() * 1000
                        if animation_path and animation_tiles_list:
                            update_animation_tiles(animation_tiles_list, [EMPTY_SLOT]*9, animation_path[0]) 
                        elif animation_tiles_list: 
                             update_animation_tiles(animation_tiles_list, [EMPTY_SLOT]*9, [EMPTY_SLOT]*9)
                    elif back_editor_btn_obj.is_clicked(mouse_pos_current, True):
                        current_view = "target_editor"
                        if backtrack_thread and backtrack_thread.is_alive():
                            backtrack_running = False
                            backtrack_thread.join(timeout=0.5)
                        backtrack_thread = None
                        backtrack_finished = True 

        if current_view == "target_editor": 
            for tile_item_editor in editor_tiles_list:
                tile_item_editor.update()

        if current_view == "filling_animation":
            for tile_item_anim in animation_tiles_list:
                tile_item_anim.update()

            now_ms_current = time.time() * 1000
            if auto_mode_active and backtrack_finished and animation_path and current_animation_step_idx < len(animation_path) - 1:
                if now_ms_current - last_switch_time_ms >= switch_interval_ms:
                    current_animation_step_idx += 1
                    prev_st_auto = animation_path[current_animation_step_idx - 1]
                    curr_st_auto = animation_path[current_animation_step_idx]
                    update_animation_tiles(animation_tiles_list, prev_st_auto, curr_st_auto)
                    last_switch_time_ms = now_ms_current

        screen.fill(DARK_BG) 

        if current_view == "target_editor":
            draw_target_editor(screen, editor_tiles_list, editable_target_state_list, editor_selected_idx,
                               title_font, font, info_font, puzzle_font, button_font,
                               start_anim_btn_obj, back_main_btn_editor_obj)
        elif current_view == "filling_animation":
            if backtrack_thread and backtrack_thread.is_alive():
                 loading_text_surf = title_font.render("Đang tạo hoạt ảnh...", True, YELLOW) 
                 screen.blit(loading_text_surf, loading_text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
            else:
                 total_steps_anim = max(0, len(animation_path) - 1) if animation_path else 0
                 draw_filling_animation(screen, animation_tiles_list, current_animation_step_idx, total_steps_anim, 
                                        target_state_tuple if target_state_tuple else [], auto_mode_active,
                                        puzzle_font, font, info_font, button_font,
                                        auto_btn_obj, next_btn_obj, reset_btn_obj, back_editor_btn_obj)

        if message_box_obj.active:
            message_box_obj.draw(screen, title_font, font, button_font)

        pygame.display.flip()
        clock.tick(60)

    if backtrack_thread and backtrack_thread.is_alive():
        print("Stopping backtracking thread on exit...")
        backtrack_running = False
        backtrack_thread.join(timeout=0.5)
    pygame.quit()

if __name__ == "__main__":
    pygame.init()
    pygame.font.init()
    try:
        screen_info_obj = pygame.display.Info()
        WIDTH, HEIGHT = screen_info_obj.current_w, screen_info_obj.current_h
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SRCALPHA)
    except pygame.error:
        print("Warning: Fullscreen failed. Using 1280x720 windowed.")
        WIDTH, HEIGHT = 1280, 720
        screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.display.set_caption("Fill Animation Visualizer")
    clock = pygame.time.Clock()

    try:
        font_name_str = "Arial";
        if font_name_str not in pygame.font.get_fonts(): 
            available_fonts = pygame.font.get_fonts(); 
            common_fonts = ["freesans", "helvetica", "dejavusans", "verdana", "sans"]; 
            font_name_str = pygame.font.get_default_font();
            for cf_item in common_fonts:
                 if cf_item.lower() in [f.lower() for f in available_fonts]: font_name_str = cf_item; break
        print(f"Using font: {font_name_str}")
        font = pygame.font.SysFont(font_name_str, 22); title_font = pygame.font.SysFont(font_name_str, 44, bold=True)
        puzzle_font = pygame.font.SysFont(font_name_str, 60, bold=True) 
        button_font = pygame.font.SysFont(font_name_str, 20); info_font = pygame.font.SysFont(font_name_str, 22)
    except Exception as e_font: 
        print(f"Font error: {e_font}. Using default."); 
        font = pygame.font.Font(None, 24); title_font = pygame.font.Font(None, 44); 
        puzzle_font = pygame.font.Font(None, 60); button_font = pygame.font.Font(None, 20); 
        info_font = pygame.font.Font(None, 22)

    fill_main()
    pygame.quit() 
    sys.exit()   