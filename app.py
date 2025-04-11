import random
import logging
import logging.config

from flask import Flask, request, redirect, url_for, render_template, flash

# Logging configuration as described in logging_config.md
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'DEBUG',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'app.log',
            'formatter': 'standard',
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)
logger.debug("Logging configuration loaded.")

app = Flask(__name__)
app.secret_key = 'candyland-secret-key'  # for flash messages

# ---------- Game Models and Logic ----------

COLORS = ['red', 'purple', 'yellow', 'blue', 'orange', 'green']
PICTURE_CARDS = [
    "Peppermint Forest",
    "Gumdrop Mountain",
    "Lollipop Woods",
    "Ice Cream Sea",
    "Gingerbread Tree",
    "Gloppy the Molasses Monster"
]

class Square:
    def __init__(self, index, color=None, is_start=False, is_finish=False,
                 is_picture=False, picture_name=None, is_shortcut_start=False,
                 shortcut_target=None, is_lose_turn=False):
        self.index = index
        self.color = color
        self.is_start = is_start
        self.is_finish = is_finish
        self.is_picture = is_picture
        self.picture_name = picture_name
        self.is_shortcut_start = is_shortcut_start
        self.shortcut_target = shortcut_target
        self.is_lose_turn = is_lose_turn

class Board:
    def __init__(self):
        self.spaces = self.generate_board()

    def generate_board(self):
        board = []
        total_spaces = 134

        # Create basic board with repeating colors
        for i in range(total_spaces):
            if i == 0:
                board.append(Square(i, color=None, is_start=True))
            elif i == total_spaces - 1:
                board.append(Square(i, color="red", is_finish=True))
            else:
                color = COLORS[(i-1) % len(COLORS)]
                board.append(Square(i, color=color))

        # Mark picture spaces at fixed indices:
        picture_positions = {
            10: "Peppermint Forest",
            30: "Gumdrop Mountain",
            60: "Lollipop Woods",
            90: "Ice Cream Sea",
            110: "Gingerbread Tree",
            120: "Gloppy the Molasses Monster"  # Also the lose-turn square
        }
        for pos, name in picture_positions.items():
            if pos < total_spaces:
                board[pos].is_picture = True
                board[pos].picture_name = name
                if name == "Gloppy the Molasses Monster":
                    board[pos].is_lose_turn = True

        # Example shortcut: if a player lands exactly on space 50, move to space 70.
        shortcut_start = 50
        shortcut_end = 70
        if shortcut_start < total_spaces and shortcut_end < total_spaces:
            board[shortcut_start].is_shortcut_start = True
            board[shortcut_start].shortcut_target = shortcut_end

        return board

class Card:
    def __init__(self, card_type, value):
        self.card_type = card_type  # 'single', 'double', or 'picture'
        self.value = value

    def __repr__(self):
        if self.card_type in ['single', 'double']:
            # Use title case for better readability
            return f"{self.card_type.title()} {self.value.title()}"
        else:
            # Keep picture names as they are
            return f"Picture: {self.value}"

class Deck:
    def __init__(self):
        self.draw_pile = []
        self.discard_pile = []
        self.build_deck()
        self.shuffle()

    def build_deck(self):
        for color in COLORS:
            for _ in range(6):
                self.draw_pile.append(Card('single', color))
        for color in COLORS:
            for _ in range(2):
                self.draw_pile.append(Card('double', color))
        for pic in PICTURE_CARDS:
            self.draw_pile.append(Card('picture', pic))
        # Total cards: 6*6 + 2*6 + 6 = 54

    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self):
        if not self.draw_pile:
            self.draw_pile = self.discard_pile.copy()
            self.discard_pile = []
            self.shuffle()
        card = self.draw_pile.pop(0)
        self.discard_pile.append(card)
        return card

class Player:
    def __init__(self, pid, pawn_color, name):
        self.pid = pid
        self.pawn_color = pawn_color
        self.name = name
        self.position = 0
        self.skip_turn = False

class Game:
    def __init__(self, num_players, names):
        logger.info("Initializing game with %s players.", num_players)
        self.status = "Setup"
        self.board = Board()
        self.deck = Deck()
        self.players = []
        self.current_player_index = 0
        self.winner = None
        self.init_players(num_players, names)
        self.status = "InProgress"
        self.messages = []
        self.last_card = None  # Initialize the last drawn card attribute
        logger.debug("Game initialized: %s", self)

    def init_players(self, num_players, names):
        pawn_colors = ['#FF0000', '#0000FF', '#FFFF00', '#008000', '#FFA500', '#800080']
        for i in range(num_players):
            pawn_color = pawn_colors[i % len(pawn_colors)]
            name = names[i] if i < len(names) and names[i] else f"Player {i+1}"
            self.players.append(Player(i+1, pawn_color, name))
            logger.debug("Player added: %s with color %s", name, pawn_color)

    def get_current_player(self):
        return self.players[self.current_player_index]

    def advance_turn(self):
        next_player_index = (self.current_player_index + 1) % len(self.players)
        while self.players[next_player_index].skip_turn:
            self.messages.append(f"Player {self.players[next_player_index].name} loses a turn.")
            logger.info("Player %s loses a turn.", self.players[next_player_index].name)
            self.players[next_player_index].skip_turn = False  # Reset skip flag
            next_player_index = (next_player_index + 1) % len(self.players)
            if next_player_index == self.current_player_index and self.players[next_player_index].skip_turn:
                self.messages.append("All players skipping turn? Resetting skip for current player.")
                logger.warning("All players skipping turn; resetting skip for %s", 
                               self.players[next_player_index].name)
                self.players[next_player_index].skip_turn = False
        self.current_player_index = next_player_index
        logger.info("Advanced turn. New current player: %s", self.get_current_player().name)

    def move_player(self, player, card):
        orig_position = player.position
        new_position = orig_position
        board = self.board.spaces
        found_target = False

        if card.card_type in ['single', 'double']:
            needed = 1 if card.card_type == 'single' else 2
            found = 0
            for pos in range(orig_position + 1, len(board)):
                if not board[pos].is_finish and board[pos].color == card.value:
                    found += 1
                    if found == needed:
                        new_position = pos
                        found_target = True
                        break
            if not found_target:
                new_position = board[-1].index
                found_target = True

        elif card.card_type == 'picture':
            for pos in range(len(board)):
                if board[pos].is_picture and board[pos].picture_name == card.value:
                    new_position = pos
                    found_target = True
                    break

        if found_target:
            move_msg = f"{player.name} drew {card}. Moves from {orig_position} to {new_position}."
            self.messages.append(move_msg)
            logger.info(move_msg)
            player.position = new_position

            current_square = board[player.position]

            if current_square.is_shortcut_start and not current_square.is_finish:
                shortcut_msg = f"{player.name} took shortcut from {player.position} to {current_square.shortcut_target}!"
                self.messages.append(shortcut_msg)
                logger.info(shortcut_msg)
                player.position = current_square.shortcut_target
                current_square = board[player.position]

            if current_square.is_lose_turn and not current_square.is_finish:
                player.skip_turn = True
                lose_turn_msg = f"{player.name} landed on {current_square.picture_name}! Lose next turn."
                self.messages.append(lose_turn_msg)
                logger.info(lose_turn_msg)

            if player.position >= board[-1].index:
                self.status = "Finished"
                self.winner = player
                win_msg = f"{player.name} reached Candy Castle and wins!"
                self.messages.append(win_msg)
                logger.info(win_msg)
        else:
            error_msg = f"{player.name} drew {card}, but no valid move found."
            self.messages.append(error_msg)
            logger.error(error_msg)

    def play_turn(self):
        self.last_card = None
        player = self.get_current_player()
        logger.info("Player %s's turn.", player.name)

        if player.skip_turn:
            logger.debug("Player %s is skipping the turn.", player.name)
            self.advance_turn()
            return None

        card = self.deck.draw()
        self.last_card = card
        draw_msg = f"{player.name} drew: {self.last_card}."
        self.messages.append(draw_msg)
        logger.info(draw_msg)

        self.move_player(player, card)

        if self.status != "Finished":
            self.advance_turn()

        return card

# ---------- Global Game Instance ----------

game = None

# ---------- Flask Routes ----------
@app.route("/", methods=["GET"])
def setup():
    logger.debug("Setup route accessed, resetting game.")
    global game
    game = None
    return render_template("setup.html")

@app.route("/start", methods=["POST"])
def start():
    global game
    try:
        num_players = int(request.form.get("num_players", 0))
        if not 2 <= num_players <= 6:
            flash("Please enter a number of players between 2 and 6.", "error")
            logger.warning("Invalid number of players: %s", num_players)
            return redirect(url_for("setup"))
    except (ValueError, TypeError) as e:
        flash("Invalid number of players.", "error")
        logger.error("Error parsing number of players: %s", e)
        return redirect(url_for("setup"))

    names = []
    for i in range(1, num_players + 1):
        name = request.form.get(f"player{i}", f"Player {i}").strip()
        names.append(name if name else f"Player {i}")

    game = Game(num_players, names)
    game.messages.append("Game started!")
    logger.info("Game started with players: %s", names)
    return redirect(url_for("game_route"))

@app.route("/game", methods=["GET"])
def game_route():
    if game is None:
        flash("Please start a new game first.", "info")
        logger.info("Game route accessed without a game; redirecting to setup.")
        return redirect(url_for("setup"))
    logger.debug("Rendering game board for current state.")
    return render_template("game.html", game=game)

@app.route("/draw", methods=["POST"])
def draw():
    global game
    if game is None:
        logger.warning("Draw route accessed without an active game; redirecting to setup.")
        return redirect(url_for("setup"))
    if game.status == "Finished":
        flash("The game has already finished!", "info")
        logger.info("Draw attempted after game finished.")
        return redirect(url_for("game_route"))

    logger.debug("Processing draw for current player: %s", game.get_current_player().name)
    game.play_turn()
    return redirect(url_for("game_route"))

@app.route("/reset", methods=["POST"])
def reset():
    global game
    game = None
    flash("Game has been reset.", "info")
    logger.info("Game has been reset via /reset route.")
    return redirect(url_for("setup"))

if __name__ == '__main__':
    logger.info("Starting Candyland app.")
    app.run(host='0.0.0.0', port=5000, debug=True)
