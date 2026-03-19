import pytest
from game.stats import CardStats, GameStats


class TestCardStats:
    def test_online_mean_update(self):
        stats = CardStats(card_id=1)
        
        stats.record_attempt(correct=True, response_time_ms=100.0)
        assert stats.avg_response_time_ms == 100.0
        assert stats._count == 1
        
        stats.record_attempt(correct=True, response_time_ms=200.0)
        assert stats.avg_response_time_ms == 150.0
        assert stats._count == 2
        
        stats.record_attempt(correct=True, response_time_ms=300.0)
        assert stats.avg_response_time_ms == 200.0
        assert stats._count == 3
    
    def test_online_variance_update(self):
        stats = CardStats(card_id=1)
        
        stats.record_attempt(correct=True, response_time_ms=100.0)
        stats.record_attempt(correct=True, response_time_ms=200.0)
        
        assert stats._count == 2
        assert stats.std_dev_response_time_ms == pytest.approx(70.71, rel=0.001)
        
        stats.record_attempt(correct=True, response_time_ms=100.0)
        assert stats._count == 3
        assert stats.avg_response_time_ms == pytest.approx(133.33, rel=0.01)
    
    def test_correct_incorrect_counting(self):
        stats = CardStats(card_id=1)
        
        stats.record_attempt(correct=True, response_time_ms=100.0)
        stats.record_attempt(correct=False, response_time_ms=50.0)
        stats.record_attempt(correct=True, response_time_ms=100.0)
        
        assert stats.correct_count == 2
        assert stats.incorrect_count == 1
        assert stats.total_attempts == 3
    
    def test_zero_response_time(self):
        stats = CardStats(card_id=1)
        stats.record_attempt(correct=True, response_time_ms=0.0)
        assert stats.avg_response_time_ms == 0.0


class TestGameStats:
    def test_start_card_timer(self):
        stats = GameStats()
        stats.start_card_timer(1)
        assert 1 in stats._start_times
    
    def test_record_result_no_timer(self):
        stats = GameStats()
        stats.record_result(card_id=1, correct=True)
        assert 1 in stats._stats
        assert stats._stats[1].correct_count == 1
        assert stats._stats[1].total_attempts == 1
    
    def test_get_all_stats(self):
        stats = GameStats()
        stats.record_result(card_id=1, correct=True)
        stats.record_result(card_id=2, correct=False)
        
        all_stats = stats.get_all_stats()
        assert len(all_stats) == 2
        assert 1 in all_stats
        assert 2 in all_stats
