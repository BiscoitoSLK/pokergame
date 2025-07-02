import tkinter as tk
from PIL import Image, ImageTk
import os
from utils import deal_deck, hand_rank, pretty_card

# Paths
ASSETS_DIR   = os.path.join(os.path.dirname(__file__), "assets")
CARD_DIR     = os.path.join(ASSETS_DIR, "cards")
TABLE_IMG    = os.path.join(ASSETS_DIR, "table.png")
CANVAS_W, CANVAS_H = 800, 600

# Pillow resampling
try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

class PokerGame(tk.Tk):
    def __init__(self, action_queue):
        super().__init__()
        self.title("Texas Hold'em")
        self.geometry(f"{CANVAS_W}x{CANVAS_H}")
        self.action_queue = action_queue

        # Keep every PhotoImage alive here
        self._images = []

        # Round counter
        self.round_number = 1

        # Game state
        self.player_stack = 1000
        self.bot_stack    = 1000
        self.pot          = 0
        self.board        = []
        self.player_hand  = []
        self.bot_hand     = []
        self.deck         = []
        self.bet_to_call  = 0
        self.player_bet   = 0
        self.bot_bet      = 0
        self.round        = 'preflop'

        # Cache card images
        self._card_images = {}

        # Build UI
        self._setup_canvas()
        self._create_summary_window()

        # First deal
        self.new_hand()

    def _setup_canvas(self):
        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H)
        self.canvas.pack(fill="both", expand=True)

        # Table background
        bg = Image.open(TABLE_IMG).resize((CANVAS_W, CANVAS_H), RESAMPLE)
        self._table_bg = ImageTk.PhotoImage(bg)
        self._images.append(self._table_bg)
        self.canvas.create_image(0,0, image=self._table_bg, anchor="nw")

        # Text overlays
        self.status_text = self.canvas.create_text(
            CANVAS_W//2, CANVAS_H - 30,
            text="", font=("Segoe UI", 16, "bold"), fill="white"
        )
        self.pot_text = self.canvas.create_text(
            CANVAS_W//2, CANVAS_H//2 + 50,
            text="", font=("Segoe UI", 14), fill="white"
        )
        self.stack_text = self.canvas.create_text(
            CANVAS_W//2, CANVAS_H - 60,
            text="", font=("Segoe UI", 12), fill="white"
        )

    def _create_summary_window(self):
        self.summary_win = tk.Toplevel(self)
        self.summary_win.title("Game Summary")
        self.summary_list = tk.Listbox(self.summary_win, width=80, height=20)
        self.summary_list.pack(padx=10, pady=10)

    def _load_card(self, code):
        if code not in self._card_images:
            path = os.path.join(CARD_DIR, f"{code}.png")
            img  = Image.open(path).resize((80,120), RESAMPLE)
            photo = ImageTk.PhotoImage(img)
            self._card_images[code] = photo
            self._images.append(photo)
        return self._card_images[code]

    def _draw_table(self, show_bot=False):
        # Remove old card images
        self.canvas.delete("card")

        # Community cards
        for i, c in enumerate(self.board):
            img = self._load_card(c)
            x = CANVAS_W//2 - 200 + i*100
            y = CANVAS_H//2 - 50
            self.canvas.create_image(x, y, image=img, tag="card")

        # Player hand
        for i, c in enumerate(self.player_hand):
            img = self._load_card(c)
            x = CANVAS_W//2 - 100 + i*100
            y = CANVAS_H - 150
            self.canvas.create_image(x, y, image=img, tag="card")

        # Bot hand
        if show_bot or self.round == 'showdown':
            for i, c in enumerate(self.bot_hand):
                img = self._load_card(c)
                x = CANVAS_W//2 - 100 + i*100
                y = 100
                self.canvas.create_image(x, y, image=img, tag="card")
        else:
            back = self._load_card("back")
            for i in range(2):
                x = CANVAS_W//2 - 100 + i*100
                y = 100
                self.canvas.create_image(x, y, image=back, tag="card")

        # Update texts
        self.canvas.itemconfigure(self.status_text, text=self.status)
        self.canvas.itemconfigure(self.pot_text,   text=f"Pot: {self.pot}")
        self.canvas.itemconfigure(
            self.stack_text,
            text=f"You: {self.player_stack}    Bot: {self.bot_stack}"
        )

    def new_hand(self):
        self.pot         = 0
        self.player_bet  = 0
        self.bot_bet     = 0
        self.board       = []
        self.deck        = deal_deck()
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.bot_hand    = [self.deck.pop(), self.deck.pop()]
        self.bet_to_call = 0
        self.round       = 'preflop'
        self.status      = "New hand dealt. Your move."
        self._draw_table(show_bot=False)
        self.after(100, self.betting_loop)

    def betting_loop(self):
        if self.round == 'showdown':
            return self.showdown()
        self.status = "Your move: fold / call / raise / allin / show"
        return self.after(100, self.check_action)

    def check_action(self):
        try:
            action = self.action_queue.get_nowait()
        except:
            return self.after(100, self.check_action)
        return self.handle_player_action(action)

    def handle_player_action(self, action):
        a = action.lower()
        if a == 'fold':
            self.status = "You folded. Bot wins."
            self.bot_stack += self.pot + self.player_bet + self.bot_bet
            self.round = 'showdown'
            self._draw_table(show_bot=True)
            return self.after(2000, self._end_round)
        if a == 'show':
            self.round = 'showdown'
            return self.showdown()
        if a == 'call':
            to_call = self.bet_to_call - self.player_bet
            amt     = min(self.player_stack, to_call)
            self.player_stack -= amt
            self.player_bet   += amt
            self.pot           += amt
            self.status = "You call."
            return self.after(500, self.bot_action)
        if a == 'raise':
            amt = min(100, self.player_stack)
            self.player_stack -= amt
            self.player_bet   += amt
            self.pot           += amt
            self.bet_to_call   = self.player_bet
            self.status        = f"You raise {amt}."
            return self.after(500, self.bot_action)
        if a == 'allin':
            amt = self.player_stack
            self.player_bet  += amt
            self.pot          += amt
            self.player_stack = 0
            self.bet_to_call  = self.player_bet
            self.status       = "You go ALL-IN!"
            return self.after(500, self.bot_action)
        self.status = "Invalid, try again."
        return self.after(500, self.betting_loop)

    def bot_action(self):
        to_call = self.bet_to_call - self.bot_bet
        if to_call <= self.bot_stack:
            self.bot_stack -= to_call
            self.bot_bet   += to_call
            self.pot        += to_call
            self.status     = "Bot calls."
        else:
            amt = self.bot_stack
            self.bot_bet  += amt
            self.pot       += amt
            self.bot_stack = 0
            self.bet_to_call = self.bot_bet
            self.status    = "Bot ALL-IN!"
        return self.after(500, self.next_round)

    def next_round(self):
        if self.round == 'preflop':
            self.board = [self.deck.pop() for _ in range(3)]
            self.round = 'flop'
        elif self.round == 'flop':
            self.board.append(self.deck.pop())
            self.round = 'turn'
        elif self.round == 'turn':
            self.board.append(self.deck.pop())
            self.round = 'river'
        else:
            self.round = 'showdown'
        self._draw_table(show_bot=False)
        if self.round == 'showdown':
            return self.after(500, self.showdown)
        return self.after(500, self.betting_loop)

    def showdown(self):
        pr, pname = hand_rank(self.player_hand, self.board)
        br, bname = hand_rank(self.bot_hand,    self.board)
        if pr > br:
            winner, amt = 'You', self.pot + self.player_bet + self.bot_bet
            self.player_stack += amt
            self.status = f"You win with {pname}!"
        elif br > pr:
            winner, amt = 'Bot', self.pot + self.player_bet + self.bot_bet
            self.bot_stack += amt
            self.status = f"Bot wins with {bname}!"
        else:
            winner, amt = 'Tie', (self.pot + self.player_bet + self.bot_bet)//2
            self.player_stack += amt
            self.bot_stack    += amt
            self.status = f"Tie: both {pname}."
        # Log summary
        board_str  = ' '.join(pretty_card(c) for c in self.board)
        p_str      = ' '.join(pretty_card(c) for c in self.player_hand)
        b_str      = ' '.join(pretty_card(c) for c in self.bot_hand)
        summary = (f"Round {self.round_number}: Board {board_str} | You: {p_str} | "
                   f"Bot: {b_str} | Winner: {winner} | Won: {amt}")
        self.summary_list.insert(tk.END, summary)
        self.round_number += 1
        self.pot = 0
        self._draw_table(show_bot=True)
        return self.after(3000, self.new_hand)

    def _end_round(self):
        return self.showdown()

    def start(self):
        self.mainloop()

def run_poker_game(action_queue):
    PokerGame(action_queue).start()
