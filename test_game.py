import unittest
from app import Game, COLORS, PICTURE_CARDS

class TestCandylandGame(unittest.TestCase):
    def setUp(self):
        # Create a game with 2 players for testing.
        self.game = Game(2)

    def test_initial_positions(self):
        # All players start at position 0.
        for player in self.game.players:
            self.assertEqual(player.position, 0)

    def test_draw_card_moves(self):
        # Force a specific card for deterministic behavior.
        player = self.game.get_current_player()
        # Create a single red card and move player manually.
        card = type("TestCard", (), {})()  # dummy card object
        card.card_type = 'single'
        card.value = 'red'
        orig_pos = player.position
        self.game.move_player(player, card)
        # Ensure player position is increased.
        self.assertGreater(player.position, orig_pos)

    def test_picture_card_move(self):
        player = self.game.get_current_player()
        # Find a picture card value from the list:
        picture = PICTURE_CARDS[0]  # "Peppermint Forest"
        card = type("TestCard", (), {})()
        card.card_type = 'picture'
        card.value = picture
        self.game.move_player(player, card)
        # Check that player's position matches the designated picture square.
        board = self.game.board.spaces
        found = False
        for square in board:
            if square.is_picture and square.picture_name == picture:
                self.assertEqual(player.position, square.index)
                found = True
                break
        self.assertTrue(found)

    def test_skip_turn(self):
        # Force player to land on a lose-turn square.
        player = self.game.get_current_player()
        # Assume board square 120 is a lose-turn square.
        player.position = 119
        dummy_card = type("TestCard", (), {})()
        dummy_card.card_type = 'single'
        dummy_card.value = self.game.board.spaces[120].color
        self.game.move_player(player, dummy_card)
        self.assertTrue(player.skip_turn)

if __name__ == "__main__":
    unittest.main()