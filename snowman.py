"""Snowman word game shared by the terminal and browser interfaces."""

import random

LEVELS = {
    "easy": {"words": ["cat", "dog", "sun", "hat", "fish"], "guesses": 6},
    "medium": {"words": ["hello", "cheese", "person", "school", "winter"], "guesses": 5},
    "hard": {"words": ["snowman", "computer", "elephant", "mountain", "keyboard"], "guesses": 4},
}


class SnowmanGame:
    def __init__(self, level, rng=None):
        if level not in LEVELS:
            raise ValueError("Choose easy, medium, or hard.")
        self.level = level
        self.rng = rng or random
        self.words = LEVELS[level]["words"]
        self.max_guesses = LEVELS[level]["guesses"]
        self.word = self.rng.choice(self.words)
        self.revealed = set()
        self.guessed = set()
        self.guesses_left = self.max_guesses
        self.points = 0
        self.phase = "main"
        self.message = "Guess a letter, the whole word, or use a hint."
        self.hint_used = False

    def state(self):
        finished = self.phase in ("won", "lost", "bonus_won", "bonus_lost", "complete")
        return {
            "level": self.level,
            "phase": self.phase,
            "masked_word": [letter if letter in self.revealed else "" for letter in self.word],
            "guesses_left": self.guesses_left,
            "max_guesses": self.max_guesses,
            "points": self.points,
            "guessed_letters": sorted(self.guessed),
            "hint_used": self.hint_used,
            "message": self.message,
            "answer": self.word if finished else None,
        }

    def guess(self, value):
        if self.phase not in ("main", "bonus"):
            raise ValueError("Start a new game to keep playing.")
        if not isinstance(value, str):
            raise ValueError("Enter letters only.")
        value = value.strip().lower()
        if not value.isalpha():
            raise ValueError("Enter letters only.")
        if len(value) == 1:
            if value in self.guessed:
                self.guesses_left -= 1
                self.message = f"You already guessed {value}. That costs a turn."
            else:
                self.guessed.add(value)
                if value in self.word:
                    self.revealed.add(value)
                    self.points += 5 if self.phase == "bonus" else 10
                    self.message = f"Nice! {value.upper()} is in the word."
                    if all(letter in self.revealed for letter in self.word):
                        self._win()
                else:
                    self.guesses_left -= 1
                    if self.phase == "main":
                        self.points -= 5
                    self.message = f"No {value.upper()} in this word."
        elif value == self.word:
            self.points += 20 if self.phase == "bonus" else 30
            self._win()
        elif self.phase == "main":
            self.points -= 100
            self.phase = "lost"
            self.message = f"That wasn't the word. It was {self.word.upper()}."
        else:
            self.guesses_left -= 1
            self.message = "That wasn't the bonus word."
        if self.guesses_left <= 0 and self.phase in ("main", "bonus"):
            self.phase = "bonus_lost" if self.phase == "bonus" else "lost"
            self.message = f"Out of guesses! The word was {self.word.upper()}."
        return self.state()

    def hint(self):
        if self.phase != "main":
            raise ValueError("Hints are only available in the main round.")
        if self.hint_used:
            raise ValueError("You already used your hint.")
        self.revealed.update(self.word[:2])
        self.hint_used = True
        self.guesses_left -= 1
        self.message = f"Hint: the first two letters are {self.word[:2].upper()}."
        if self.guesses_left <= 0:
            self.phase = "lost"
            self.message += f" The word was {self.word.upper()}."
        return self.state()

    def start_bonus(self, play):
        if self.phase != "won":
            raise ValueError("Win the main round before choosing the bonus round.")
        if not play:
            self.phase = "complete"
            self.message = f"Great game! Final score: {self.points}."
            return self.state()
        self.phase = "bonus"
        self.word = self.rng.choice(self.words)
        self.revealed = set()
        self.guessed = set()
        self.guesses_left = self.max_guesses
        self.message = "Bonus round! No hints this time."
        return self.state()

    def _win(self):
        if self.phase == "bonus":
            self.phase = "bonus_won"
            self.message = f"Bonus complete! The word was {self.word.upper()}."
        else:
            self.phase = "won"
            self.message = f"You won! The word was {self.word.upper()}. Try the bonus round?"


def play_terminal():
    print("snowman: choose your level\n1 easy\n2 medium\n3 hard")
    levels = {"1": "easy", "2": "medium", "3": "hard"}
    while True:
        level = levels.get(input("you: ").strip())
        if level:
            break
        print("snowman: please enter 1, 2, or 3")
    game = SnowmanGame(level)
    print("snowman: welcome to the game")
    while True:
        state = game.state()
        if state["phase"] == "won":
            print("snowman:", state["message"])
            game.start_bonus(input("you: bonus round yes or no? ").strip().lower() == "yes")
            continue
        if state["phase"] not in ("main", "bonus"):
            print("snowman:", state["message"])
            print("points:", state["points"])
            break
        print("word:", " ".join(letter or "-" for letter in state["masked_word"]))
        print("guesses left:", state["guesses_left"])
        value = input("you: enter a letter or word" + (" (or hint)" if state["phase"] == "main" else "") + ": ")
        try:
            result = game.hint() if value.strip().lower() == "hint" else game.guess(value)
            print("snowman:", result["message"])
        except ValueError as error:
            print("snowman:", error)


if __name__ == "__main__":
    play_terminal()
