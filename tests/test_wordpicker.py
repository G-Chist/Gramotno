import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.insert(0, '/home/matvei/EvolvingCards')

from main_clean import WordPicker, get_cards_from_db

class MockCard:
    def __init__(self, id, word, translation):
        self.id = id
        self.word = word
        self.translation = translation

class TestWordPicker(unittest.TestCase):
    
    def setUp(self):
        self.mock_cards = [
            MockCard(1, "hello", "hola"),
            MockCard(2, "world", "mundo"),
            MockCard(3, "foo", "bar"),
            MockCard(4, "test", "prueba"),
            MockCard(5, "code", "codigo"),
            MockCard(6, "bug", "error"),
            MockCard(7, "feature", "caracteristica"),
        ]
    
    @patch('main_clean.get_cards_from_db')
    def test_get_cards(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards
        
        picker = WordPicker()
        picker.get_cards()
        
        self.assertEqual(picker.cards, self.mock_cards)
        mock_get_cards.assert_called_once()
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_card(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards
        
        picker = WordPicker()
        result = picker.get_random_card()
        
        self.assertIsNotNone(result)
        self.assertIn(result, self.mock_cards)
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_5_cards(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards
        
        picker = WordPicker()
        picker.get_cards()
        picker.get_random_5_cards()
        
        self.assertEqual(len(picker.five_cards), 5)
        self.assertTrue(all(card in self.mock_cards for card in picker.five_cards))
    
    @patch('main_clean.get_cards_from_db')
    def test_fill_native_words(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards[:5]
        
        picker = WordPicker()
        picker.cards = self.mock_cards[:5]
        picker.five_cards = self.mock_cards[:5]
        picker.fill_native_words()
        
        self.assertEqual(len(picker.native_words), 5)
        words = [w[0] for w in picker.native_words]
        ids = [w[1] for w in picker.native_words]
        self.assertCountEqual(words, ["hola", "mundo", "bar", "prueba", "codigo"])
        self.assertCountEqual(ids, [1, 2, 3, 4, 5])
    
    @patch('main_clean.get_cards_from_db')
    def test_fill_learning_words(self, mock_get_cards):
        mock_get_cards.return_value = self.mock_cards[:5]
        
        picker = WordPicker()
        picker.cards = self.mock_cards[:5]
        picker.five_cards = self.mock_cards[:5]
        picker.fill_learning_words()
        
        self.assertEqual(len(picker.learning_words), 5)
        words = [w[0] for w in picker.learning_words]
        ids = [w[1] for w in picker.learning_words]
        self.assertCountEqual(words, ["hello", "world", "foo", "test", "code"])
        self.assertCountEqual(ids, [1, 2, 3, 4, 5])
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_card_empty_db(self, mock_get_cards):
        mock_get_cards.return_value = []
        
        picker = WordPicker()
        result = picker.get_random_card()
        
        self.assertIsNone(result)
    
    @patch('main_clean.get_cards_from_db')
    def test_get_random_5_cards_empty_db(self, mock_get_cards):
        mock_get_cards.return_value = []
        
        picker = WordPicker()
        picker.cards = []
        picker.get_random_5_cards()
        
        self.assertEqual(picker.five_cards, [])

    @patch('main_clean.Session')
    def test_get_worst_cards_by_success_rate(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
            MockCard(4, "d", "d"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.correct_count = 2
        mock_progress_1.total_attempts = 10

        mock_progress_2 = MagicMock()
        mock_progress_2.card_id = 2
        mock_progress_2.correct_count = 8
        mock_progress_2.total_attempts = 10

        mock_progress_3 = MagicMock()
        mock_progress_3.card_id = 3
        mock_progress_3.correct_count = 0
        mock_progress_3.total_attempts = 5

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1, mock_progress_2, mock_progress_3]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_success_rate(4)
        
        self.assertEqual([i.id for i in result], [4, 3, 1, 2])
        self.assertEqual(len(result), 4)

    @patch('main_clean.Session')
    def test_get_worst_cards_by_response_time(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
            MockCard(4, "d", "d"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.avg_response_time_ms = 5000.0

        mock_progress_2 = MagicMock()
        mock_progress_2.card_id = 2
        mock_progress_2.avg_response_time_ms = 1000.0

        mock_progress_3 = MagicMock()
        mock_progress_3.card_id = 3
        mock_progress_3.avg_response_time_ms = 3000.0

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1, mock_progress_2, mock_progress_3]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_response_time(4)

        self.assertEqual(len(result), 4)
        self.assertEqual([i.id for i in result], [4, 1, 3, 2])

    @patch('main_clean.Session')
    def test_get_worst_cards_by_errors(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
            MockCard(4, "d", "d"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.incorrect_count = 10

        mock_progress_2 = MagicMock()
        mock_progress_2.card_id = 2
        mock_progress_2.incorrect_count = 2

        mock_progress_3 = MagicMock()
        mock_progress_3.card_id = 3
        mock_progress_3.incorrect_count = 5

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1, mock_progress_2, mock_progress_3]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_errors(4)

        self.assertEqual(len(result), 4)
        self.assertEqual([i.id for i in result], [4, 1, 3, 2])

    @patch('main_clean.Session')
    def test_get_worst_cards_combined(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
            MockCard(4, "d", "d"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.correct_count = 1
        mock_progress_1.total_attempts = 10
        mock_progress_1.incorrect_count = 9
        mock_progress_1.avg_response_time_ms = 5000.0

        mock_progress_2 = MagicMock()
        mock_progress_2.card_id = 2
        mock_progress_2.correct_count = 9
        mock_progress_2.total_attempts = 10
        mock_progress_2.incorrect_count = 1
        mock_progress_2.avg_response_time_ms = 1000.0

        mock_progress_3 = MagicMock()
        mock_progress_3.card_id = 3
        mock_progress_3.correct_count = 5
        mock_progress_3.total_attempts = 10
        mock_progress_3.incorrect_count = 5
        mock_progress_3.avg_response_time_ms = 2000.0

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1, mock_progress_2, mock_progress_3]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_combined(4)

        self.assertEqual([i.id for i in result], [4, 1, 3, 2])

    @patch('main_clean.Session')
    def test_get_worst_5_cards(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
            MockCard(4, "d", "d"),
            MockCard(5, "e", "e"),
            MockCard(6, "f", "f"),
            MockCard(7, "g", "g"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.correct_count = 1
        mock_progress_1.total_attempts = 10
        mock_progress_1.incorrect_count = 9
        mock_progress_1.avg_response_time_ms = 5000.0

        mock_progress_2 = MagicMock()
        mock_progress_2.card_id = 2
        mock_progress_2.correct_count = 9
        mock_progress_2.total_attempts = 10
        mock_progress_2.incorrect_count = 1
        mock_progress_2.avg_response_time_ms = 1000.0

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1, mock_progress_2]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_5_cards()

        self.assertEqual(len(picker.five_cards), 5)
        card_ids = [c.id for c in picker.five_cards]
        self.assertTrue(all(i in card_ids for i in [3, 4, 5, 6, 7]))

    @patch('main_clean.Session')
    def test_get_worst_cards_n_equals_zero(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.correct_count = 5
        mock_progress_1.total_attempts = 10

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_success_rate(0)

        self.assertEqual(len(result), 0)

    @patch('main_clean.Session')
    def test_get_worst_cards_n_larger_than_cards(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.correct_count = 5
        mock_progress_1.total_attempts = 10

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_success_rate(10)

        self.assertEqual(len(result), 2)

    @patch('main_clean.Session')
    def test_get_worst_cards_all_new_cards(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
        ]
        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = []
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_success_rate(3)

        self.assertEqual(len(result), 3)
        card_ids = [c.id for c in result]
        self.assertEqual(sorted(card_ids), [1, 2, 3])

    @patch('main_clean.Session')
    def test_get_worst_cards_with_zero_attempts(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
            MockCard(3, "c", "c"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1
        mock_progress_1.correct_count = 0
        mock_progress_1.total_attempts = 0

        mock_progress_2 = MagicMock()
        mock_progress_2.card_id = 2
        mock_progress_2.correct_count = 5
        mock_progress_2.total_attempts = 10

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1, mock_progress_2]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_cards_by_success_rate(3)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].id, 1)

    @patch('main_clean.get_cards_from_db')
    def test_fill_native_words_empty(self, mock_get_cards):
        mock_get_cards.return_value = []
        
        picker = WordPicker()
        picker.cards = []
        picker.five_cards = []
        picker.fill_native_words()
        
        self.assertEqual(picker.native_words, [])

    @patch('main_clean.get_cards_from_db')
    def test_fill_learning_words_empty(self, mock_get_cards):
        mock_get_cards.return_value = []
        
        picker = WordPicker()
        picker.cards = []
        picker.five_cards = []
        picker.fill_learning_words()
        
        self.assertEqual(picker.learning_words, [])

    @patch('main_clean.Session')
    def test_get_worst_5_cards_empty_db(self, mock_session_cls):
        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = []
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = []
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        result = picker.get_worst_5_cards()

        self.assertEqual(len(picker.five_cards), 0)

    @patch('main_clean.Session')
    def test_get_cards_with_progress_returns_correct_mapping(self, mock_session_cls):
        mock_cards = [
            MockCard(1, "a", "a"),
            MockCard(2, "b", "b"),
        ]
        mock_progress_1 = MagicMock()
        mock_progress_1.card_id = 1

        mock_session = MagicMock()
        cards_query_result = MagicMock()
        cards_query_result.all.return_value = mock_cards
        progress_query_result = MagicMock()
        progress_filter_result = MagicMock()
        progress_filter_result.all.return_value = [mock_progress_1]
        progress_query_result.filter.return_value = progress_filter_result
        mock_session.query.side_effect = [cards_query_result, progress_query_result]
        mock_session_cls.return_value = mock_session

        picker = WordPicker()
        cards, progress_map = picker._get_cards_with_progress()

        self.assertEqual(len(cards), 2)
        self.assertIn(1, progress_map)
        self.assertNotIn(2, progress_map)

if __name__ == '__main__':
    unittest.main()
