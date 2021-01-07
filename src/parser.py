

class UCIParser():
    """
    A class for parsing uci to more human readable
    english strings
    """

    def __init__(self, referee):
        """
        Can use the referee to get info like
        if a move is taking a piece, or illegal, etc
        """
        self.referee = referee

    def move_to_english(self, move):
        """
        Given a python-chess move and return an English translation
        """

        # If null move is given:
        if not move:
            return 'pass turn'

        # Get the current board state from referee
        board = self.referee.board.copy()

        # If string was given, get move assuming the current board state
        if type(move) is str:
            # Though, if it is a code, ignore it
            if self.referee.is_code(move):
                code_name, _ = self.referee.code_checker.get_code_info(move)
                return f'Code: "{code_name}"'
            move = self.referee.to_move(move)
        # If a move was given, assume the move was just made,
        # and look at the board before
        else:
            board.pop()

        from_piece = board.piece_at(move.from_square)
        to_piece = board.piece_at(move.to_square)

        uci = move.uci()
        from_square_name = uci[:2]
        to_square_name = uci[2:]

        if from_piece is None:
            return f'No starting piece at {from_square_name}'

        piece_names = {
            1: 'pawn',
            2: 'knight',
            3: 'bishop',
            4: 'rook',
            5: 'queen',
            6: 'king'
        }

        from_piece_name = piece_names.get(from_piece.piece_type)
        to_piece_name = (None if to_piece is None
                         else piece_names.get(to_piece.piece_type))

        # What we will actually call the names when we say them
        # (default is the piece name, but dependent on ambiguity)
        to_piece_alias = to_piece_name
        from_piece_alias = from_piece_name

        # Check if this attacker could be confused for another of the
        # same type
        def is_ambigious(attacking, from_square=None, to_square=None, limit=1):
            # By default, use this moves squares.
            # However, can set as a param, as func is also
            # useful for finding if there is a simmilar capture
            # (e.g. 'Can a pawn take a knight anwhere else on this board?')
            if from_square is None:
                from_square = move.from_square
            if to_square is None:
                to_square = move.to_square

            if attacking:

                # TODO is this always true?
                # Because pawns don't attack the same way they move, their
                # attacking squares are not in contest with their move,
                # unless they are moving diagonal
                is_pawn = board.piece_type_at(from_square) == 1
                no_victim = board.piece_at(to_square) is None
                if is_pawn and no_victim:
                    return False

                origin_square = from_square
                square_set = board.attackers(board.turn, to_square)
            else:

                # TODO use python-chess 'is_attacking'?
                # If we do not have a victim, we must specify to_square
                if board.piece_at(to_square) is None:
                    return True

                origin_square = to_square
                square_set = board.attacks(from_square)

            origin_p_type = board.piece_type_at(origin_square)

            for square in square_set:
                p_type = board.piece_type_at(square)
                p_color = board.color_at(square)
                # Ambigious if the piece type is the same and either:
                # We are attacking, and the attacker mataches my color
                # We are a victim, and the other victim matches my color
                matching_piece = (
                    p_type == origin_p_type and
                    p_color == (board.turn == attacking)
                )
                if square != origin_square and matching_piece:
                    return True
            return False

        # Determine if this is attack , or regular move
        # TODO gross logic
        verb = 'to'
        if board.is_capture(move):
            verb = 'takes'
        if move.promotion is not None:
            verb = 'promotion to'
            to_piece_alias = piece_names.get(move.promotion)

        # Determine if the 'from piece' is ambigious
        # (because multiple peices of the same type could make this move)
        dupe_attackers = is_ambigious(attacking=True)
        if dupe_attackers:
            from_piece_alias = from_square_name

        # Determine if the 'from piece' is ambigious  (or nothing is there)
        # (because this peice can choose from several victims of the same type)
        dupe_victims = is_ambigious(attacking=False)
        if dupe_victims:
            to_piece_alias = to_square_name

        # Can still be ambigious if there are unrelated captures
        # by the same name elsewhere
        # TODO how best to do this fast?
        def dupe_capture():
            # Cannot be a dupe capture if this move is not a capture!
            if to_piece is None:
                return False

            # If we have already solved ambiguity, return false
            still_named = (
                to_piece_alias == to_piece_name and
                from_piece_alias == from_piece_name
            )
            if not still_named:
                return False

            matching_victims = [
                sq for sq in board.pieces(to_piece.piece_type, not board.turn)
                if sq != move.to_square
            ]
            for sq in matching_victims:
                # If there is an unrelated matching capture,
                # do we change from or to?
                dupe_capture = is_ambigious(attacking=True, to_square=sq)
                if dupe_capture:
                    return True

        dupe_capture = dupe_capture()
        if dupe_capture:
            from_piece_alias = from_square_name

        # TODO check color for this
        # TODO 'move.drop' gives the drop type - is this useful?

        s = f'{from_piece_alias} {verb} {to_piece_alias}'

        # Try move, see if it puts is in a special state
        # TODO these do not seem to work
        if board.is_en_passant(move):
            s += ' - pawn taken in passing'

        if board.is_castling(move):
            s += ' - castling'

        if board.gives_check(move):
            s += ' - check'

        return s
