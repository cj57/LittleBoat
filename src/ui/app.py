"""Main Tkinter Application window for Battleship Solitaire."""
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from .game_controller import GameController
from .board_canvas import BoardCanvas
from ..core.generator import Difficulty


class BattleshipApp(tk.Tk):
    """Main window for '發現小船' (Battleship Solitaire)."""

    SHIP_NAMES = {
        4: "戰艦 (4格)",
        3: "巡洋艦 (3格)",
        2: "驅逐艦 (2格)",
        1: "潛水艇 (1格)",
    }

    def __init__(self):
        super().__init__()
        self.title("發現小船 (Battleship Solitaire)")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        # Initialize game controller with EASY difficulty by default
        self.controller = GameController(difficulty=Difficulty.EASY)

        # Build UI layout
        self._setup_styles()
        self._create_header()
        self._create_main_area()

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
            text="以邏輯推導隱藏在海域中的所有船艦",
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

        # Mouse operation instructions below board
        tips_label = ttk.Label(
            board_card,
            text="🖱️ 操作說明：【滑鼠左鍵】標記船隻  |  【滑鼠右鍵】標記海水波浪",
            background="#ffffff",
            foreground="#64748b",
            font=("Segoe UI", 9)
        )
        tips_label.pack(pady=(8, 0))

        # Right Column: Side Panel (Fleet & Actions)
        side_panel = ttk.Frame(main_frame, width=240, padding=(16, 0, 0, 0))
        side_panel.pack(side="left", fill="y")

        # 1. Fleet Specification Card
        fleet_card = ttk.Frame(side_panel, style="Card.TFrame", padding=12)
        fleet_card.pack(fill="x", pady=(0, 12))

        ttk.Label(fleet_card, text="🎯 艦隊清單與進度", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        self.fleet_container = ttk.Frame(fleet_card, style="Card.TFrame")
        self.fleet_container.pack(fill="x")

        # 2. Action Buttons Card
        action_card = ttk.Frame(side_panel, style="Card.TFrame", padding=12)
        action_card.pack(fill="x", pady=(0, 12))

        ttk.Label(action_card, text="⚡ 遊戲控制", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        btn_new = ttk.Button(action_card, text="🎲 開啟新遊戲", style="Action.TButton", command=self._on_new_game)
        btn_new.pack(fill="x", pady=2)

        btn_restart = ttk.Button(action_card, text="🔄 重玩本局", style="Action.TButton", command=self._on_restart)
        btn_restart.pack(fill="x", pady=2)

        btn_undo = ttk.Button(action_card, text="↩ 復原一步 (Undo)", style="Action.TButton", command=self._on_undo)
        btn_undo.pack(fill="x", pady=2)

        btn_hint = ttk.Button(action_card, text="💡 提示一步", style="Action.TButton", command=self._on_hint)
        btn_hint.pack(fill="x", pady=2)

        btn_check = ttk.Button(action_card, text="🔍 檢查當前盤面", style="Action.TButton", command=self._on_check_solution)
        btn_check.pack(fill="x", pady=2)

        # 3. Status Banner Card
        self.status_card = ttk.Frame(side_panel, style="Card.TFrame", padding=12)
        self.status_card.pack(fill="x")

        self.status_title = ttk.Label(self.status_card, text="📌 當前狀態", style="CardTitle.TLabel")
        self.status_title.pack(anchor="w", pady=(0, 4))

        self.status_text = tk.Label(
            self.status_card,
            text="遊戲進行中，請點擊格子找出所有船隻。",
            wraplength=210,
            justify="left",
            bg="#ffffff",
            fg="#475569",
            font=("Segoe UI", 9)
        )
        self.status_text.pack(anchor="w")

    def _on_change_difficulty(self) -> None:
        val = self.diff_var.get()
        diff = Difficulty(val)
        self.controller.new_game(difficulty=diff)
        self._refresh_all()

    def _on_new_game(self) -> None:
        diff = Difficulty(self.diff_var.get())
        self.controller.new_game(difficulty=diff)
        self._refresh_all()

    def _on_restart(self) -> None:
        self.controller.restart_game()
        self._refresh_all()

    def _on_undo(self) -> None:
        if self.controller.undo():
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
        self._update_fleet_display()
        if self.controller.is_won:
            self.status_text.config(text="🎉 太棒了！您已成功找出所有船艦！", fg="#15803d")
            messagebox.showinfo("勝利！", "恭喜您成功解開本道謎題！🎉")
        else:
            # Check immediate violations
            in_prog = self.controller.validate_current()
            if in_prog.row_errors or in_prog.col_errors or in_prog.invalid_components:
                self.status_text.config(text="⚠️ 注意：盤面有線索超標或船隻相碰！", fg="#b91c1c")
            else:
                self.status_text.config(text="進行中... 邏輯清晰，繼續保持！", fg="#475569")

    def _update_fleet_display(self) -> None:
        for child in self.fleet_container.winfo_children():
            child.destroy()

        progress_list = self.controller.get_fleet_progress()
        for p in progress_list:
            name = self.SHIP_NAMES.get(p.length, f"{p.length}格船")
            row_frame = tk.Frame(self.fleet_container, bg="#ffffff")
            row_frame.pack(fill="x", pady=2)

            # Ship icon visual (e.g. ◼◼◼)
            icon = "■" * p.length
            tk.Label(
                row_frame,
                text=icon,
                bg="#ffffff",
                fg="#1e293b",
                font=("Consolas", 10)
            ).pack(side="left")

            tk.Label(
                row_frame,
                text=f" {name}",
                bg="#ffffff",
                fg="#334155",
                font=("Segoe UI", 9)
            ).pack(side="left")

            status_str = f"{p.current} / {p.target}"
            if p.is_satisfied:
                status_str += " ✓"
                status_color = "#15803d"
            elif p.current > p.target:
                status_color = "#b91c1c"
            else:
                status_color = "#64748b"

            tk.Label(
                row_frame,
                text=status_str,
                bg="#ffffff",
                fg=status_color,
                font=("Segoe UI", 9, "bold")
            ).pack(side="right")

    def _refresh_all(self) -> None:
        self.canvas.update_sizing()
        self.canvas.redraw()
        self._update_fleet_display()


def run_app():
    app = BattleshipApp()
    app.mainloop()


if __name__ == "__main__":
    run_app()
