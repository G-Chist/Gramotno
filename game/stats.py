from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

@dataclass
class CardStats:
    card_id: int
    correct_count: int = 0
    incorrect_count: int = 0
    total_attempts: int = 0
    avg_response_time_ms: float = 0.0
    std_dev_response_time_ms: float = 0.0
    _M: float = 0.0
    _S: float = 0.0
    _count: int = 0

    def record_attempt(self, correct: bool, response_time_ms: float) -> None:
        self._count += 1
        self.total_attempts += 1
        
        if correct:
            self.correct_count += 1
        else:
            self.incorrect_count += 1
        
        if response_time_ms > 0:
            x = response_time_ms
            if self._count == 1:
                self._M = x
                self._S = 0.0
            else:
                prev_M = self._M
                self._M = prev_M + (x - prev_M) / self._count
                self._S = self._S + (x - prev_M) * (x - self._M)
            
            if self._count >= 2:
                variance = self._S / (self._count - 1)
                self.std_dev_response_time_ms = variance ** 0.5
            self.avg_response_time_ms = self._M

    def merge_from_db(self, db_stats: 'CardStats') -> None:
        if db_stats._count > 0:
            self._M = db_stats.avg_response_time_ms
            self._S = db_stats.std_dev_response_time_ms ** 2 * (db_stats._count - 1) if db_stats._count > 1 else 0.0
            self._count = db_stats._count
            self.correct_count = db_stats.correct_count
            self.incorrect_count = db_stats.incorrect_count
            self.total_attempts = db_stats.total_attempts
            self.avg_response_time_ms = db_stats.avg_response_time_ms
            self.std_dev_response_time_ms = db_stats.std_dev_response_time_ms

    def error_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.incorrect_count / self.total_attempts


class GameStats:
    def __init__(self):
        self._stats: dict[int, CardStats] = {}
        self._start_times: dict[int, datetime] = {}

    def start_card_timer(self, card_id: int) -> None:
        self._start_times[card_id] = datetime.now(timezone.utc)

    def record_result(self, card_id: int, correct: bool) -> None:
        response_time_ms = 0.0
        if card_id in self._start_times:
            elapsed = datetime.now(timezone.utc) - self._start_times[card_id]
            response_time_ms = elapsed.total_seconds() * 1000
            del self._start_times[card_id]
        
        if card_id not in self._stats:
            self._stats[card_id] = CardStats(card_id=card_id)
        
        self._stats[card_id].record_attempt(correct, response_time_ms)

    def get_stats(self, card_id: int) -> Optional[CardStats]:
        return self._stats.get(card_id)

    def get_all_stats(self) -> dict[int, CardStats]:
        return self._stats.copy()

    def load_from_db(self, session) -> None:
        from models.schema import Progress
        db_progress_list = session.query(Progress).all()
        
        for db_progress in db_progress_list:
            card_stats = CardStats(card_id=db_progress.card_id)
            card_stats.correct_count = db_progress.correct_count
            card_stats.incorrect_count = db_progress.incorrect_count
            card_stats.total_attempts = db_progress.total_attempts
            card_stats.avg_response_time_ms = db_progress.avg_response_time_ms or 0.0
            card_stats.std_dev_response_time_ms = db_progress.std_dev_response_time_ms or 0.0
            
            if card_stats.total_attempts > 0:
                card_stats._count = card_stats.total_attempts
                if card_stats._count >= 1:
                    card_stats._M = card_stats.avg_response_time_ms
                if card_stats._count >= 2:
                    card_stats._S = (card_stats.std_dev_response_time_ms ** 2) * (card_stats._count - 1)
            
            self._stats[db_progress.card_id] = card_stats

    def persist_to_db(self, session) -> None:
        from models.schema import Progress, Card
        
        for card_id, stats in self._stats.items():
            db_progress = session.query(Progress).filter_by(card_id=card_id).first()
            
            if db_progress is None:
                card = session.query(Card).filter_by(id=card_id).first()
                if card is None:
                    continue
                db_progress = Progress(card_id=card_id)
                session.add(db_progress)
            
            db_progress.correct_count = stats.correct_count
            db_progress.incorrect_count = stats.incorrect_count
            db_progress.total_attempts = stats.total_attempts
            db_progress.avg_response_time_ms = stats.avg_response_time_ms if stats._count > 0 else None
            db_progress.std_dev_response_time_ms = stats.std_dev_response_time_ms if stats._count > 1 else None
        
        session.commit()
