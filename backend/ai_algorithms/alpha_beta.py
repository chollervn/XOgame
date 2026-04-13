import time
import random
from backend.game_engine import EMPTY_CELL, check_winner, board_full
from backend.ai_utils import (
    DifficultyProfile, generate_candidate_moves, evaluate_board, quick_move_score, 
    get_zobrist, board_hash, SYMBOL_INDEX, INF, WIN_SCORE, all_empty_moves
)
from backend.ai_algorithms.base import AIStrategy
from backend.ai_algorithms.rule_based import RuleBasedStrategy

class SearchTimeout(Exception):
    pass

class AlphaBetaStrategy(AIStrategy):
    """Thuật toán Minimax kết hợp Alpha-Beta Pruning và Iterative Deepening."""
    
    def __init__(self):
        self.rule_checker = RuleBasedStrategy()

    def get_move(self, board: list[list[str]], ai_symbol: str, human_symbol: str, profile: DifficultyProfile) -> tuple[int, int] | None:
        size = len(board)
        candidates = generate_candidate_moves(board, profile.candidate_radius, profile.max_candidates)
        if not candidates:
            return None

        # Trong các mức khó, tránh nhảy vào chỗ chết
        safe_candidates = self._safe_moves_against_immediate_loss(board, candidates, ai_symbol, human_symbol)
        if safe_candidates:
            candidates = safe_candidates
            
        start_time = time.perf_counter()
        zobrist = get_zobrist(size)
        root_hash = board_hash(board, zobrist)
        tt: dict[tuple[int, int, bool], int] = {}
        
        best_ranked = [(evaluate_board(board, ai_symbol, human_symbol), candidates[0])]
        
        for depth in range(1, profile.max_depth + 1):
            try:
                ranked = self._search_root(board, depth, ai_symbol, human_symbol, -INF, INF, start_time, profile.time_limit_seconds, tt, zobrist, root_hash, profile, candidates)
                if ranked:
                    best_ranked = ranked
            except SearchTimeout:
                break
                
        return self._pick_move_with_noise(best_ranked, profile)

    def _search_root(self, board, depth, ai_symbol, human_symbol, alpha, beta, start_time, time_limit, tt, zobrist, b_hash, profile, candidates):
        self._check_timeout(start_time, time_limit)
        ordered_moves = sorted(candidates, key=lambda m: quick_move_score(board, m, ai_symbol), reverse=True)
        ranked = []
        local_alpha = alpha
        
        for r, c in ordered_moves:
            self._check_timeout(start_time, time_limit)
            board[r][c] = ai_symbol
            try:
                next_hash = b_hash ^ zobrist[r][c][SYMBOL_INDEX[ai_symbol]]
                score = self._alphabeta(board, depth - 1, False, ai_symbol, human_symbol, local_alpha, beta, start_time, time_limit, tt, zobrist, next_hash, profile)
            finally:
                board[r][c] = EMPTY_CELL
                
            ranked.append((score, (r, c)))
            if score > local_alpha:
                local_alpha = score
                
        ranked.sort(key=lambda x: x[0], reverse=True)
        return ranked

    def _alphabeta(self, board, depth, maximizing, ai_symbol, human_symbol, alpha, beta, start_time, time_limit, tt, zobrist, b_hash, profile):
        self._check_timeout(start_time, time_limit)
        winner, _ = check_winner(board)
        if winner == ai_symbol: return WIN_SCORE + depth
        if winner == human_symbol: return -WIN_SCORE - depth
        if board_full(board): return 0
        if depth == 0: return evaluate_board(board, ai_symbol, human_symbol)
        
        key = (b_hash, depth, maximizing)
        if key in tt: return tt[key]
        
        candidates = generate_candidate_moves(board, profile.candidate_radius, profile.max_candidates)
        if not candidates: return evaluate_board(board, ai_symbol, human_symbol)
        
        player = ai_symbol if maximizing else human_symbol
        ordered_moves = sorted(candidates, key=lambda m: quick_move_score(board, m, player), reverse=True)
        
        if maximizing:
            value = -INF
            for r, c in ordered_moves:
                board[r][c] = player
                try:
                    next_hash = b_hash ^ zobrist[r][c][SYMBOL_INDEX[player]]
                    value = max(value, self._alphabeta(board, depth - 1, False, ai_symbol, human_symbol, alpha, beta, start_time, time_limit, tt, zobrist, next_hash, profile))
                finally:
                    board[r][c] = EMPTY_CELL
                alpha = max(alpha, value)
                if beta <= alpha: break
        else:
            value = INF
            for r, c in ordered_moves:
                board[r][c] = player
                try:
                    next_hash = b_hash ^ zobrist[r][c][SYMBOL_INDEX[player]]
                    value = min(value, self._alphabeta(board, depth - 1, True, ai_symbol, human_symbol, alpha, beta, start_time, time_limit, tt, zobrist, next_hash, profile))
                finally:
                    board[r][c] = EMPTY_CELL
                beta = min(beta, value)
                if beta <= alpha: break
                
        tt[key] = value
        return value

    def _check_timeout(self, start_time, time_limit):
        if time.perf_counter() - start_time > time_limit:
            raise SearchTimeout

    def _safe_moves_against_immediate_loss(self, board, candidates, ai_symbol, human_symbol):
        safe_moves = []
        all_empty = all_empty_moves(board)
        for r, c in candidates:
            # Fallback avoid immediate loss
            board[r][c] = ai_symbol
            loss = self.rule_checker._find_winning_move(board, all_empty, human_symbol)
            board[r][c] = EMPTY_CELL
            if not loss:
                safe_moves.append((r, c))
        return safe_moves
        
    def _pick_move_with_noise(self, ranked, profile):
        if not ranked: return None
        if profile.randomness <= 0 or random.random() > profile.randomness:
            return ranked[0][1]
        top_count = min(profile.top_k_random, len(ranked))
        return random.choice(ranked[:top_count])[1]
