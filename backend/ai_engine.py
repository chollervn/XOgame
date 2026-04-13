"""
Đây là AI Engine (Đầu não). 
Sử dụng mẫu thiết kế STRATEGY để gọi linh hoạt các thuật toán tùy tình huống.
"""
from backend.game_engine import board_full
from backend.ai_utils import PROFILE_BY_SIZE
from backend.ai_algorithms.rule_based import RuleBasedStrategy
from backend.ai_algorithms.alpha_beta import AlphaBetaStrategy

class AIEngine:
    def __init__(self, difficulty: str, size: int):
        self.difficulty = difficulty
        self.size = size
        self.profile = PROFILE_BY_SIZE[difficulty][size]
        
        # Thiết lập các chiến lược thuật toán mình sẽ dùng
        self.rule_based_strategy = RuleBasedStrategy()
        self.alpha_beta_strategy = AlphaBetaStrategy()

    def get_best_move(self, board: list[list[str]], ai_symbol: str, human_symbol: str) -> tuple[int, int] | None:
        """Đầu não xử lý tình huống"""
        if board_full(board):
            return None

        # 1. Ưu tiên cao nhất: Dùng Rule-based kiểm tra có nước đi Thắng liền / Thua liền (Chặn ngay!)
        critical_move = self.rule_based_strategy.get_move(board, ai_symbol, human_symbol, self.profile)
        if critical_move:
            return critical_move

        # 2. Nếu an toàn, kích hoạt Thuật toán quy hoạch sâu Minimax (Alpha-Beta Pruning)
        main_move = self.alpha_beta_strategy.get_move(board, ai_symbol, human_symbol, self.profile)
        if main_move:
            return main_move
            
        return None

# Interface Hàm tĩnh giữ tương thích với hệ thống ở main.py cũ
def choose_ai_move(board: list[list[str]], ai_symbol: str, human_symbol: str, difficulty: str) -> tuple[int, int] | None:
    size = len(board)
    engine = AIEngine(difficulty=difficulty, size=size)
    return engine.get_best_move(board, ai_symbol, human_symbol)
