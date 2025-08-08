import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer
import pyautogui
import cv2
import numpy as np
import threading
import time
import win32gui
import win32con
import webbrowser
# === GLOBAL STATE ===
zoom_enabled = False
always_on_top = True
zoom_factor = 4
zoom_thread = None
zoom_running = False
settings_window_pos = [50, 50]
overlay_window_pos = [1600, 50]
settings_window_size = [300, 275]
settings_x_input = settings_window_pos[0]
settings_y_input = settings_window_pos[1]
temp_x = settings_window_pos[0]
temp_y = settings_window_pos[1]
# === ZOOM WINDOW ===
def apply_nexus_style():
    style = imgui.get_style()
    imgui.style_colors_dark()

    # Spacing and layout
    style.window_padding = (12, 12)
    style.frame_padding = (6, 4)
    style.item_spacing = (10, 8)
    style.item_inner_spacing = (6, 4)

    # Rounded edges
    style.window_rounding = 10.0
    style.child_rounding = 8.0
    style.frame_rounding = 6.0
    style.popup_rounding = 6.0
    style.grab_rounding = 6.0
    style.frame_padding = (6, 4)       # smaller padding inside widgets
    style.window_padding = (8, 6)      # tighter outer spacing
    style.window_title_align = (0.5, 0.5)  # center the title text
    # Borders
    style.window_border_size = 1.0
    style.frame_border_size = 1.0
    style.tab_border_size = 1.0

    # Font (optional: load custom font for even closer match)
    # io = imgui.get_io()
    # io.fonts.add_font_from_file_ttf("path/to/font.ttf", 16)

    # Color palette
    colors = style.colors
    colors[imgui.COLOR_WINDOW_BACKGROUND]           = (0.08, 0.08, 0.10, 1.00)
    colors[imgui.COLOR_BORDER]                      = (0.20, 0.20, 0.25, 1.0)
    colors[imgui.COLOR_FRAME_BACKGROUND]            = (0.10, 0.10, 0.15, 1.00)
    colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED]    = (0.15, 0.15, 0.25, 1.00)
    colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE]     = (0.20, 0.20, 0.30, 1.00)
    colors[imgui.COLOR_BUTTON]                      = (0.20, 0.25, 0.35, 1.00)
    colors[imgui.COLOR_BUTTON_HOVERED]              = (0.30, 0.35, 0.45, 1.00)
    colors[imgui.COLOR_BUTTON_ACTIVE]               = (0.35, 0.40, 0.55, 1.00)
    colors[imgui.COLOR_SLIDER_GRAB]                 = (0.35, 0.55, 0.85, 1.00)
    colors[imgui.COLOR_SLIDER_GRAB_ACTIVE]          = (0.45, 0.65, 0.95, 1.00)
    colors[imgui.COLOR_CHECK_MARK]                  = (0.45, 0.75, 0.90, 1.00)
    colors[imgui.COLOR_TEXT]                        = (0.85, 0.85, 0.90, 1.00)
    colors[imgui.COLOR_TEXT_DISABLED]               = (0.50, 0.50, 0.55, 1.00)
    colors[imgui.COLOR_TITLE_BACKGROUND]             = (0.10, 0.10, 0.10, 1.00)
    colors[imgui.COLOR_TITLE_BACKGROUND_ACTIVE]      = (0.15, 0.15, 0.15, 1.00)
    colors[imgui.COLOR_TITLE_BACKGROUND_COLLAPSED]   = (0.08, 0.08, 0.08, 1.00)
def open_link_after_delay():
    def delayed_open():
        time.sleep(10)
        webbrowser.open("https://e-z.bio/skysserpent")

    threading.Thread(target=delayed_open, daemon=True).start()
def run_zoom_overlay():
    global zoom_running
    win_name = "ZoomOverlay"
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
    hwnd = win32gui.FindWindow(None, win_name)

    # Remove window decorations
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME))

    # Set always on top and initial pos
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST if always_on_top else win32con.HWND_NOTOPMOST,
                          overlay_window_pos[0], overlay_window_pos[1], 50 * zoom_factor, 50 * zoom_factor, 0)

    zoom_running = True

    while zoom_enabled:
        screen_w, screen_h = pyautogui.size()
        center_x = screen_w // 2
        center_y = screen_h // 2
        half_size = 25

        region = (center_x - half_size, center_y - half_size, 50, 50)
        img = pyautogui.screenshot(region=region)
        img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        img = cv2.resize(img, (50 * zoom_factor, 50 * zoom_factor), interpolation=cv2.INTER_CUBIC)

        hwnd = win32gui.FindWindow(None, win_name)
        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST if always_on_top else win32con.HWND_NOTOPMOST,
                              overlay_window_pos[0], overlay_window_pos[1], 50 * zoom_factor, 50 * zoom_factor, 0)

        cv2.imshow(win_name, img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyWindow(win_name)
    zoom_running = False

# === ZOOM CONTROL ===
def show_zoom():
    global zoom_enabled, zoom_thread
    if not zoom_enabled:
        zoom_enabled = True
        zoom_thread = threading.Thread(target=run_zoom_overlay, daemon=True)
        zoom_thread.start()

def hide_zoom():
    global zoom_enabled
    zoom_enabled = False

# === SETTINGS UI ===
def run_settings_window():
    global zoom_factor, always_on_top
    global temp_x, temp_y

    if not glfw.init():
        return

    glfw.window_hint(glfw.DECORATED, glfw.FALSE)
    glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)

    window = glfw.create_window(settings_window_size[0], settings_window_size[1], "", None, None)
    glfw.set_window_pos(window, settings_window_pos[0], settings_window_pos[1])
    glfw.make_context_current(window)

    imgui.create_context()
    apply_nexus_style()
    impl = GlfwRenderer(window)

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        imgui.new_frame()

        imgui.set_next_window_position(0, 0)
        imgui.set_next_window_size(settings_window_size[0], settings_window_size[1])

        imgui.begin("Zoom Settings", flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_SAVED_SETTINGS)



        changed, always_on_top = imgui.checkbox("Always on Top", always_on_top)

        imgui.push_item_width(185)
        changed, zoom_factor = imgui.slider_int("Overlay Size", zoom_factor, 1, 10)
        imgui.pop_item_width()
        imgui.push_item_width(200)
        changed_x, temp_x = imgui.input_int("##input_settings_x", temp_x)
        imgui.same_line()
        if imgui.button("Set X"):
            settings_window_pos[0] = temp_x
            glfw.set_window_pos(window, settings_window_pos[0], settings_window_pos[1])

        changed_y, temp_y = imgui.input_int("##input_settings_y", temp_y)
        imgui.same_line()
        if imgui.button("Set Y"):
            settings_window_pos[1] = temp_y
            glfw.set_window_pos(window, settings_window_pos[0], settings_window_pos[1])

        changed, overlay_window_pos[0] = imgui.slider_int("Overlay X", overlay_window_pos[0], 0, 2560)
        changed, overlay_window_pos[1] = imgui.slider_int("Overlay Y", overlay_window_pos[1], 0, 1440)

        imgui.pop_item_width()

        if imgui.button("Show Zoom", width=135):
            show_zoom()
        imgui.same_line()
        if imgui.button("Hide Zoom", width=135):
            hide_zoom()

        if imgui.button("Exit", width=280):
            hide_zoom()
            break

        imgui.end()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()

if __name__ == "__main__":
    open_link_after_delay()
    run_settings_window()