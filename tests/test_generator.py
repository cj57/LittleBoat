"""Tests for Generator and Solver."""
import unittest
from src.models.cell import CellState
from src.models.board import Board
from src.core.validator import Validator
from src.core.solver import Solver
from src.core.generator import Generator, Difficulty


class TestGeneratorAndSolver(unittest.TestCase):
    def test_generate_easy_puzzle(self):
        puzzle = Generator.generate_puzzle(difficulty=Difficulty.EASY, seed=42)
        self.assertEqual(puzzle.board.rows, 6)
        self.assertEqual(puzzle.board.cols, 6)
        self.assertEqual(puzzle.difficulty, "easy")

        # Total ship cells must match fleet spec (3*1 + 2*2 + 1*3 = 10)
        self.assertEqual(sum(puzzle.board.row_clues), 10)
        self.assertEqual(sum(puzzle.board.col_clues), 10)

        # Validate ground truth solution using Validator
        test_board = Board(
            rows=6,
            cols=6,
            row_clues=puzzle.board.row_clues,
            col_clues=puzzle.board.col_clues,
            fleet_spec=puzzle.board.fleet_spec,
        )
        for r in range(6):
            for c in range(6):
                test_board.set_cell(r, c, puzzle.solution[r][c])

        val_res = Validator.validate_solution(test_board)
        self.assertTrue(val_res.is_valid)
        self.assertTrue(val_res.is_complete)
        self.assertEqual(val_res.found_ships, {3: 1, 2: 2, 1: 3})

    def test_generate_medium_and_hard_puzzles(self):
        # Medium 8x8
        med_puzzle = Generator.generate_puzzle(difficulty=Difficulty.MEDIUM, seed=123)
        self.assertEqual(med_puzzle.board.rows, 8)
        self.assertEqual(med_puzzle.board.cols, 8)
        self.assertEqual(sum(med_puzzle.board.row_clues), 14)

        # Hard 10x10
        hard_puzzle = Generator.generate_puzzle(difficulty=Difficulty.HARD, seed=456)
        self.assertEqual(hard_puzzle.board.rows, 10)
        self.assertEqual(hard_puzzle.board.cols, 10)
        self.assertEqual(sum(hard_puzzle.board.row_clues), 20)

    def test_hints_generation(self):
        puzzle = Generator.generate_puzzle(
            difficulty=Difficulty.EASY,
            hints_count=3,
            seed=999,
        )
        self.assertEqual(len(puzzle.hints), 3)
        for (r, c), state in puzzle.hints.items():
            # Board cell must reflect hint
            self.assertEqual(puzzle.board.get_cell(r, c), state)
            # Hint must match ground truth
            self.assertEqual(puzzle.solution[r][c], state)

    def test_deterministic_seed(self):
        p1 = Generator.generate_puzzle(difficulty=Difficulty.EASY, seed=777)
        p2 = Generator.generate_puzzle(difficulty=Difficulty.EASY, seed=777)
        self.assertEqual(p1.board.row_clues, p2.board.row_clues)
        self.assertEqual(p1.board.col_clues, p2.board.col_clues)
        self.assertEqual(p1.solution, p2.solution)

    def test_solver_finds_valid_solution(self):
        puzzle = Generator.generate_puzzle(difficulty=Difficulty.EASY, seed=101)
        solver = Solver(puzzle.board)
        solved_grid = solver.solve()
        self.assertIsNotNone(solved_grid)

        # Verify solved grid with Validator
        test_board = Board(
            rows=puzzle.board.rows,
            cols=puzzle.board.cols,
            row_clues=puzzle.board.row_clues,
            col_clues=puzzle.board.col_clues,
            fleet_spec=puzzle.board.fleet_spec,
        )
        for r in range(test_board.rows):
            for c in range(test_board.cols):
                test_board.set_cell(r, c, solved_grid[r][c])

        val_res = Validator.validate_solution(test_board)
        self.assertTrue(val_res.is_valid)
        self.assertTrue(val_res.is_complete)

    def test_solver_unsolvable_puzzle(self):
        # Impossible row clue: target is 5 on a row, but col clues sum to 0
        board = Board(
            rows=3,
            cols=3,
            row_clues=[5, 0, 0],
            col_clues=[0, 0, 0],
            fleet_spec={1: 1},
        )
        solver = Solver(board)
        self.assertIsNone(solver.solve())


if __name__ == "__main__":
    unittest.main()
