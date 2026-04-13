from abc import ABC, abstractmethod
from backend.ai_utils import DifficultyProfile

class AIStrategy(ABC):
    """Giao diện (Interface) chung cho mọi thuật toán AI."""
    
    @abstractmethod
    def get_move(
        self, 
        board: list[list[str]], 
        ai_symbol: str, 
        human_symbol: str, 
        profile: DifficultyProfile
    ) -> tuple[int, int] | None:
        """
        Nhận vào trạng thái bàn cờ, trả về tọa độ (row, col) 
        hoặc None nếu thuật toán này không tìm được / không áp dụng.
        """
        pass
