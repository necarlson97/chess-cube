from abc import ABC, abstractmethod

class Player(ABC):
    """
    Abstract class for a chess player,
    can be implemented as a terminal-input human,
    or as a stock-fish AI, or as an email-input human, etc
    """

    # The referee will set this back-reference when
    # it is initialized
    referee = None
    # Similarly, their 'white' or 'black' names will be given
    name = None

    def prep(self, referee, name):
        """
        Before the referee starts play, it will set these values
        """
        self.referee = referee
        self.name = name

    @abstractmethod
    def get_move(self):
        """
        The 'primary' method of this player,
        returns a UCI chess move string for the referee
        to enact as their next move.
        This method can also give a code. If the code
        has a suggested move, it will automatically be played,
        otherwise this will be called again for a follow up.
        Similarly, if the input is invalid, this method will just
        continue to be called.
        """
        pass

    @abstractmethod
    def hear_move(self, move):
        """
        The other player has made a move,
        and the referee passes the move to this
        player to communicate it to them
        """
        pass

    @abstractmethod
    def hear(sefl, s):
        """
        The referee (or other player)
        has to inform the player of something.
        Could be printing to terminal, emailing, etc
        """
        pass

    @abstractmethod
    def win(self):
        # This player has won a match
        pass

    @abstractmethod
    def lose(self):
        # This player has lost a match
        pass

    @abstractmethod
    def draw(self):
        # This player has drawn a match
        pass

    def __str__(self):
        return f'{self.__class__.__name__} - {self.name}'

class TerminalPlayer(Player):
    """
    A human typing in their moves in the terminal
    """

    def get_move(self):
        """
        Poll from std-in until we get an input that
        is a valid move
        """
        inp = input(f'{self.name} move: ')
        english_str = self.referee.parser.move_to_english(inp)
        print(f'{english_str} ({inp})')
        return inp

    def hear_move(self, move):
        english_str = self.referee.parser.move_to_english(move)
        print(f'{self.referee.opponent()} played:', english_str)
        print(self.referee.board)

    def hear(sefl, s):
        print(s)

    def win(self):
        print(f'You win! ({self.name})')

    def lose(self):
        print(f'You lose... ({self.name})')

    def draw(self):
        print('Game was a draw')

class EmailPlayer(Player):
    """
    A human emailing their moves to an address
    """
    pass

class QueuePlayer(Player):
    """
    A test player which is just given a list of moves to spit out
    """
    pass
