"""
Regression tests for Baganetic Chatbot Fixes.
Verifies:
1. "What's the history of Bagan?" -> Bagan overview / history as destination.
2. "Tell me about Ananda Temple history" -> Ananda Temple history from database.
3. "Tell me about Shwezigon Pagoda history" -> Shwezigon Pagoda history from database.
4. "Show me all pagodas" -> All 19 pagodas retrieved and displayed from database.
5. Suggestions do not echo user's query or loop repetitively.
6. Existing features: pagoda info, recommendations, nearby search, and A* route planning.
"""

import sys
import os
import unittest

# Ensure current directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from chatbot_backend import BaganeticChatbot


class TestChatbotRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bot = BaganeticChatbot()

    def test_01_history_of_bagan(self):
        """1. 'What's the history of Bagan?' -> bagan_overview or history_culture for whole destination"""
        query = "What's the history of Bagan?"
        res = self.bot.process_message(query, user_id="test_user_1")
        
        self.assertIn(res.get('intent'), ['bagan_overview', 'history_culture'])
        response_text = res.get('response', '')
        
        # Verify it provides Bagan destination overview and not an error
        self.assertNotIn("couldn't find 'bagan'", response_text.lower())
        self.assertNotIn("which pagoda's history", response_text.lower())
        self.assertTrue(
            "unesco world heritage" in response_text.lower() or "pagan kingdom" in response_text.lower() or "bagan" in response_text.lower(),
            "Response should describe Bagan historical overview"
        )
        
        # Suggestions should not echo the query
        suggestions = res.get('suggestions', [])
        for s in suggestions:
            self.assertNotEqual(s.strip().lower(), query.strip().lower())

    def test_02_ananda_temple_history(self):
        """2. 'Tell me about Ananda Temple history' -> Retrieve Ananda Temple history from DB"""
        query = "Tell me about Ananda Temple history"
        res = self.bot.process_message(query, user_id="test_user_2")
        
        self.assertIn(res.get('intent'), ['history_culture', 'pagoda_info'])
        response_text = res.get('response', '')
        
        # Verify it matches Ananda Temple and not a random pagoda or missing error
        self.assertIn("Ananda Temple", response_text)
        self.assertNotIn("couldn't find", response_text.lower())
        
        # Verify historical details from DB: 1105 AD, Kyanzittha, Pagan Dynasty
        self.assertIn("1105 AD", response_text)
        self.assertTrue("kyanzittha" in response_text.lower() or "kyansittha" in response_text.lower())
        self.assertIn("Pagan Dynasty", response_text)

    def test_03_shwezigon_pagoda_history(self):
        """3. 'Tell me about Shwezigon Pagoda history' -> Retrieve Shwezigon history from DB"""
        query = "Tell me about Shwezigon Pagoda history"
        res = self.bot.process_message(query, user_id="test_user_3")
        
        self.assertIn(res.get('intent'), ['history_culture', 'pagoda_info'])
        response_text = res.get('response', '')
        
        # Verify it matches Shwezigon Pagoda
        self.assertIn("Shwezigon Pagoda", response_text)
        self.assertNotIn("couldn't find", response_text.lower())
        
        # Verify historical details from DB: 1059-1102 AD, Anawrahta, Pagan Dynasty
        self.assertIn("1059-1102 AD", response_text)
        self.assertIn("Anawrahta", response_text)
        self.assertIn("Pagan Dynasty", response_text)

    def test_04_show_me_all_pagodas(self):
        """4. 'Show me all pagodas' -> Retrieve and display all available pagodas from DB"""
        query = "Show me all pagodas"
        res = self.bot.process_message(query, user_id="test_user_4")
        
        self.assertEqual(res.get('intent'), 'all_pagodas')
        response_text = res.get('response', '')
        
        # Not an error
        self.assertNotIn("couldn't find a pagoda named 'show me'", response_text.lower())
        
        # Verify all 19 pagodas from database are listed in response
        expected_pagodas = [p['name'] for p in self.bot.pagoda_data]
        self.assertEqual(len(expected_pagodas), 19, "Database should contain 19 pagodas")
        
        missing = []
        for name in expected_pagodas:
            if name not in response_text:
                missing.append(name)
        self.assertEqual(len(missing), 0, f"Missing pagodas in response: {missing}")

    def test_05_suggestions_not_echoing_query(self):
        """5. Verify suggestions do not display the exact query asked"""
        queries = [
            "What's the history of Bagan?",
            "Tell me about Ananda Temple history",
            "Show me all pagodas"
        ]
        for q in queries:
            res = self.bot.process_message(q, user_id=f"test_user_echo_{hash(q)}")
            suggestions = res.get('suggestions', [])
            cleaned_q = q.lower().strip(" ?.!").replace("'", "")
            for s in suggestions:
                cleaned_s = s.lower().strip(" ?.!").replace("'", "")
                self.assertNotEqual(cleaned_s, cleaned_q, f"Suggestion '{s}' echoed query '{q}'")

    def test_06_existing_pagoda_info(self):
        """6. Re-test individual pagoda information ('Tell me about Ananda Temple', 'What is Sulamani Temple?')"""
        res1 = self.bot.process_message("Tell me about Ananda Temple", user_id="test_info_1")
        self.assertEqual(res1.get('intent'), 'pagoda_info')
        self.assertIn("Ananda Temple", res1.get('response', ''))
        # Ensure 'a temple' bug is fixed and it doesn't return Lawkananda or other random pagoda
        self.assertNotIn("Lawkananda", res1.get('response', ''))

        res2 = self.bot.process_message("What is Sulamani Temple?", user_id="test_info_2")
        self.assertEqual(res2.get('intent'), 'pagoda_info')
        self.assertIn("Sulamani Temple", res2.get('response', ''))

    def test_07_existing_recommendations(self):
        """7. Re-test recommendations ('What are the must-see pagodas?', 'Recommend some pagodas')"""
        res1 = self.bot.process_message("What are the must-see pagodas?", user_id="test_rec_1")
        self.assertEqual(res1.get('intent'), 'recommendations')
        self.assertTrue(len(res1.get('response', '')) > 50)

        res2 = self.bot.process_message("Recommend some pagodas", user_id="test_rec_2")
        self.assertEqual(res2.get('intent'), 'recommendations')
        self.assertTrue(len(res2.get('response', '')) > 50)

    def test_08_existing_nearby_search(self):
        """8. Re-test nearby search ('Find pagodas near Ananda', 'Pagodas near Sulamani')"""
        res1 = self.bot.process_message("Find pagodas near Ananda", user_id="test_near_1")
        self.assertEqual(res1.get('intent'), 'nearby')
        self.assertIn("Pagodas near Ananda Temple", res1.get('response', ''))
        self.assertIn("km", res1.get('response', ''))

        res2 = self.bot.process_message("Pagodas near Sulamani", user_id="test_near_2")
        self.assertEqual(res2.get('intent'), 'nearby')
        self.assertIn("Pagodas near Sulamani Temple", res2.get('response', ''))

    def test_09_existing_astar_route_planning(self):
        """9. Re-test A* route planning ('Route from Ananda to Shwezigon')"""
        res = self.bot.process_message("Route from Ananda to Shwezigon", user_id="test_route_1")
        self.assertEqual(res.get('intent'), 'pathfinding')
        response_text = res.get('response', '')
        self.assertIn("Route from Ananda Temple to Shwezigon Pagoda", response_text)
        self.assertIn("Distance:", response_text)
        self.assertIn("Route:", response_text)
        self.assertIn("Ananda Temple", response_text)
        self.assertIn("Shwezigon Pagoda", response_text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
