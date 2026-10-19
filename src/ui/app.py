"""Main Tkinter Application window for Battleship Solitaire with Drag & Drop Fleet Dock."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, List, Tuple

from .game_controller import GameController, DockShip
from .board_canvas import BoardCanvas
from .fleet_dock_canvas import FleetDockCanvas
from .drawing_utils import draw_ship_segment, ShipSegmentType
from ..core.generator import Difficulty


class BattleshipApp(tk.Tk):
    """Main window for '發現小船' (Battleship Solitaire) with Drag & Drop."""

    def __init__(self):
        super().__init__()
        self.title("發現小船 (Battleship Solitaire)")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        # Initialize game controller with EASY difficulty by default
        self.controller = GameController(difficulty=Difficulty.EASY)

        # Drag & Drop State
        self.dragging_ship: Optional[DockShip] = None
        self.drag_orientation: bool = True
        self.drag_avatar: Optional[tk.Toplevel] = None
        self.current_preview_target: Optional[Tuple[int, int]] = None

        # Build UI layout
        self._setup_styles()
        self._create_header()
        self._create_main_area()

        # Keyboard shortcuts
        self.bind("<space>", self._on_spacebar_pressed)

        # Initial render
        self._refresh_all()

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background="#f8fafc")
        style.configure("Header.TFrame", background="#0f172a")
        style.configure("Header.TLabel", background="#0f172a", foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background="#0f172a", foreground="#94a3b8", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#ffffff", relief="ridge", borderwidth=1)
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#0f172a", font=("Segoe UI", 11, "bold"))
        style.configure("Action.TButton", font=("Segoe UI", 10), padding=5)

    def _create_header(self) -> None:
        header_frame = ttk.Frame(self, style="Header.TFrame", padding=(16, 12))
        header_frame.pack(fill="x")

        title_label = ttk.Label(
            header_frame,
            text="⛵ 發現小船 (Battleship Solitaire)",
            style="Header.TLabel"
        )
        title_label.pack(side="left")

        subtitle_label = ttk.Label(
            header_frame,
            text="拖曳船艦至海域，以邏輯解開謎題",
            style="SubHeader.TLabel"
        )
        subtitle_label.pack(side="left", padx=(12, 0))

        # Difficulty Selector in Header
        diff_frame = ttk.Frame(header_frame, style="Header.TFrame")
        diff_frame.pack(side="right")

        self.diff_var = tk.StringVar(value=Difficulty.EASY.value)
        for text, val in [("6x6 入門", Difficulty.EASY.value), ("8x8 進階", Difficulty.MEDIUM.value), ("10x10 經典", Difficulty.HARD.value)]:
            rb = tk.Radiobutton(
                diff_frame,
                text=text,
                value=val,
                variable=self.diff_var,
                command=self._on_change_difficulty,
                bg="#0f172a",
                fg="#e2e8f0",
                selectcolor="#1e293b",
                activebackground="#0f172a",
                activeforeground="#ffffff",
                font=("Segoe UI", 10, "bold"),
            )
            rb.pack(side="left", padx=4)

    def _create_main_area(self) -> None:
        main_frame = ttk.Frame(self, padding=16)
        main_frame.pack(fill="both", expand=True)

        # Left Column: Canvas Board
        board_card = ttk.Frame(main_frame, style="Card.TFrame", padding=10)
        board_card.pack(side="left", fill="both", expand=True)

        self.canvas = BoardCanvas(
            board_card,
            controller=self.controller,
            on_cell_change=self._on_cell_updated
        )
        self.canvas.pack()

        # Operation instructions below board
        tips_label = ttk.Label(
            board_card,
            text="🖱️ 操作：【拖曳船隻】放上棋盤 | 【雙擊船塢】切換水平/垂直 | 【右鍵】標記海水波浪 | 【點擊船身】移除收回",
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 9)
        )
        tips_label.pack(pady=(8, 0))

        # Right Column: Side Panel (Fleet Dock & Actions)
        side_panel = ttk.Frame(main_frame, width=280, padding=(16, 0, 0, 0))
        side_panel.pack(side="left", fill="both")

        # 1. Graphical Fleet Dock Card
        fleet_card = ttk.Frame(side_panel, style="Card.TFrame", padding=12)
        fleet_card.pack(fill="x", pady=(0, 10))

        fleet_header = ttk.Frame(fleet_card, style="Card.TFrame")
        fleet_header.pack(fill="x", pady=(0, 6))
        ttk.Label(fleet_header, text="🚢 艦隊整備塢 (拖曳上盤)", style="CardTitle.TLabel").pack(side="left")
        ttk.Label(fleet_header, text="雙擊旋轉", background="#ffffff", foreground="#0284c7", font=("Segoe UI", 9, "bold")).pack(side="right")

        self.dock_canvas = FleetDockCanvas(
            fleet_card,
            controller=self.controller,
            on_drag_start=self._start_dragging,
            on_drag_move=self._move_dragging,
            on_drag_release=self._stop_dragging,
            on_ship_double_click=self._on_dock_ship_rotated,
            width=260,
        )
        self.dock_canvas.pack(fill="x")

        # 2. Action Buttons Card
        action_card = ttk.Frame(side_panel, style="Card.TFrame", padding=12)
        action_card.pack(fill="x", pady=(0, 10))

        ttk.Label(action_card, text="⚡ 遊戲控制", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        btn_row1 = ttk.Frame(action_card, style="Card.TFrame")
        btn_row1.pack(fill="x", pady=2)
        ttk.Button(btn_row1, text="🎲 新遊戲", style="Action.TButton", command=self._on_new_game).pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(btn_row1, text="🔄 重玩本局", style="Action.TButton", command=self._on_restart).pack(side="left", fill="x", expand=True, padx=(2, 0))

        btn_row2 = ttk.Frame(action_card, style="Card.TFrame")
        btn_row2.pack(fill="x", pady=2)
        ttk.Button(btn_row2, text="↩ 復原一步", style="Action.TButton", command=self._on_undo).pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(btn_row2, text="💡 提示一步", style="Action.TButton", command=self._on_hint).pack(side="left", fill="x", expand=True, padx=(2, 0))

        ttk.Button(action_card, text="🔍 檢查盤面狀態", style="Action.TButton", command=self._on_check_solution).pack(fill="x", pady=(4, 0))

        # 3. Status Banner Card
        self.status_card = ttk.Frame(side_panel, style="Card.TFrame", padding=12)
        self.status_card.pack(fill="x")

        self.status_title = ttk.Label(self.status_card, text="📌 當前狀態", style="CardTitle.TLabel")
        self.status_title.pack(anchor="w", pady=(0, 4))

        self.status_text = tk.Label(
            self.status_card,
            text="按住上方艦隊中的船隻，直接拖曳至左側棋盤中擺放！",
            wraplength=250,
            justify="left",
            bg="#ffffff",
            fg="#475569",
            font=("Segoe UI", 9)
        )
        self.status_text.pack(anchor="w")

    # ================= Drag and Drop System =================

    def _start_dragging(self, dock_ship: DockShip, root_x: int, root_y: int) -> None:
        self.dragging_ship = dock_ship
        self.drag_orientation = dock_ship.is_horizontal
        self.current_preview_target = None

        # Create a floating borderless transparent drag avatar
        self.drag_avatar = tk.Toplevel(self)
        self.drag_avatar.overrideredirect(True)
        self.drag_avatar.attributes("-topmost", True)
        self.drag_avatar.config(bg="#f1f5f9")

        cs = 32
        length = dock_ship.length
        if self.drag_orientation:
            w = length * cs
            h = cs
        else:
            w = cs
            h = length * cs

        avatar_canvas = tk.Canvas(self.drag_avatar, width=w, height=h, bg="#f1f5f9", highlightthickness=0)
        avatar_canvas.pack()

        # Render avatar pieces
        if length == 1:
            draw_ship_segment(avatar_canvas, 0, 0, cs, cs, ShipSegmentType.SUBMARINE, fill_color="#15324d", outline_color="#0f172a", inset=2)
        elif self.drag_orientation:
            for i in range(length):
                cx1 = i * cs
                cx2 = cx1 + cs
                seg = ShipSegmentType.CAP_LEFT if i == 0 else (ShipSegmentType.CAP_RIGHT if i == length - 1 else ShipSegmentType.MIDDLE_HORIZ)
                draw_ship_segment(avatar_canvas, cx1, 0, cx2, cs, seg, fill_color="#15324d", outline_color="#0f172a", inset=2)
        else:
            for i in range(length):
                cy1 = i * cs
                cy2 = cy1 + cs
                seg = ShipSegmentType.CAP_TOP if i == 0 else (ShipSegmentType.CAP_BOTTOM if i == length - 1 else ShipSegmentType.MIDDLE_VERT)
                draw_ship_segment(avatar_canvas, 0, cy1, cs, cy2, seg, fill_color="#15324d", outline_color="#0f172a", inset=2)

        self.drag_avatar.geometry(f"{w}x{h}+{root_x - w // 2}+{root_y - h // 2}")

    def _move_dragging(self, root_x: int, root_y: int) -> None:
        if self.drag_avatar is None or self.dragging_ship is None:
            return

        w = self.drag_avatar.winfo_width()
        h = self.drag_avatar.winfo_height()
        self.drag_avatar.geometry(f"+{root_x - w // 2}+{root_y - h // 2}")

        # Check if cursor is over board canvas
        bx = self.canvas.winfo_rootx()
        by = self.canvas.winfo_rooty()
        bw = self.canvas.winfo_width()
        bh = self.canvas.winfo_height()

        if bx <= root_x <= bx + bw and by <= root_y <= by + bh:
            canvas_x = root_x - bx
            canvas_y = root_y - by
            cell = self.canvas.get_cell_at_xy(canvas_x, canvas_y)
            if cell is not None:
                r, c = cell
                ignore = set(self.dragging_ship.placed_coords) if self.dragging_ship.is_placed else set()
                is_legal, cells = self.controller.can_place_ship_at(
                    length=self.dragging_ship.length,
                    is_horizontal=self.drag_orientation,
                    start_r=r,
                    start_c=c,
                    ignore_cells=ignore,
                )
                self.current_preview_target = (r, c)
                self.canvas.set_drag_preview(cells, is_legal)
                return

        self.current_preview_target = None
        self.canvas.clear_drag_preview()

    def _stop_dragging(self, root_x: int, root_y: int) -> None:
        if self.drag_avatar is not None:
            self.drag_avatar.destroy()
            self.drag_avatar = None

        self.canvas.clear_drag_preview()

        if self.dragging_ship is not None and self.current_preview_target is not None:
            r, c = self.current_preview_target
            # Attempt placement
            success = self.controller.place_dock_ship(
                ship_id=self.dragging_ship.id,
                start_r=r,
                start_c=c,
                is_horizontal=self.drag_orientation,
            )
            if success:
                self.status_text.config(
                    text=f"已成功放置 {self.dragging_ship.length} 格船艦！",
                    fg="#15803d"
                )
                self._on_cell_updated()
            else:
                self.status_text.config(
                    text="⚠️ 放置位置非法（超出界線或與現有船隻碰撞）！",
                    fg="#b91c1c"
                )

        self.dragging_ship = None
        self.current_preview_target = None
        self._refresh_all()

    def _on_spacebar_pressed(self, event: tk.Event) -> None:
        """Rotates dragged ship when spacebar is pressed during dragging."""
        if self.dragging_ship is not None and self.drag_avatar is not None:
            self.drag_orientation = not self.drag_orientation
            # Recreate avatar with rotated orientation
            rx = self.winfo_pointerx()
            ry = self.winfo_pointery()
            ship = self.dragging_ship
            self.drag_avatar.destroy()
            self.drag_avatar = None
            self._start_dragging(ship, rx, ry)
            self._move_dragging(rx, ry)

    def _on_dock_ship_rotated(self, dock_ship: DockShip) -> None:
        orient_str = "水平" if dock_ship.is_horizontal else "垂直"
        self.status_text.config(
            text=f"🔄 {dock_ship.length} 格船隻已切換為【{orient_str}】朝向！",
            fg="#0369a1"
        )

    # ================= Game Actions =================

    def _on_change_difficulty(self) -> None:
        val = self.diff_var.get()
        diff = Difficulty(val)
        self.controller.new_game(difficulty=diff)
        self._refresh_all()

    def _on_new_game(self) -> None:
        diff = Difficulty(self.diff_var.get())
        self.controller.new_game(difficulty=diff)
        self.status_text.config(text="已開啟新題目！請以滑鼠拖曳船隻擺放。", fg="#475569")
        self._refresh_all()

    def _on_restart(self) -> None:
        self.controller.restart_game()
        self.status_text.config(text="本局已重設回初始狀態！", fg="#475569")
        self._refresh_all()

    def _on_undo(self) -> None:
        if self.controller.undo():
            self.status_text.config(text="已復原上一步操作。", fg="#475569")
            self._refresh_all()

    def _on_hint(self) -> None:
        hint_result = self.controller.give_hint()
        if hint_result is not None:
            r, c, state = hint_result
            self.status_text.config(
                text=f"💡 已提示第 {r + 1} 列、第 {c + 1} 行！",
                fg="#0284c7"
            )
            self._refresh_all()
        else:
            self.status_text.config(
                text="已無可提示的空格或錯誤！",
                fg="#64748b"
            )

    def _on_check_solution(self) -> None:
        val_res = self.controller.validate_current()
        if val_res.is_complete:
            self.status_text.config(text="🎉 太棒了！您已成功找出所有船艦！", fg="#15803d")
            messagebox.showinfo("勝利！", "恭喜您成功解開本道謎題！🎉")
        elif not val_res.is_valid:
            first_err = val_res.errors[0] if val_res.errors else "盤面存在違反規則的配置！"
            self.status_text.config(text=f"⚠️ {first_err}", fg="#b91c1c")
        else:
            self.status_text.config(text="目前的擺放均合法，但尚未完全滿足所有線索！", fg="#0369a1")

    def _on_cell_updated(self) -> None:
        self.dock_canvas.redraw()
        if self.controller.is_won:
            self.status_text.config(text="🎉 太棒了！您已成功找出所有船艦！", fg="#15803d")
            messagebox.showinfo("勝利！", "恭喜您成功解開本道謎題！🎉")
        else:
            in_prog = self.controller.validate_current()
            if in_prog.row_errors or in_prog.col_errors or in_prog.invalid_components:
                self.status_text.config(text="⚠️ 注意：盤面有線索超標或船隻相碰！", fg="#b91c1c")
            else:
                self.status_text.config(text="邏輯清晰，繼續保持！可隨時右鍵標記水域。", fg="#475569")

    def _refresh_all(self) -> None:
        self.canvas.update_sizing()
        self.canvas.redraw()
        self.dock_canvas.redraw()


def run_app():
    app = BattleshipApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
