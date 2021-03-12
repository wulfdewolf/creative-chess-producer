#------------------------------------------------
#
#           A CREATIVE CHESS ENGINE
#
#             author: Wolf De Wulf
#
#------------------------------------------------
import chess
import chess.engine
from optimality.optimality import get_optimality_scores
from creativity.creativity import get_creativity_scores

# Initial board
initial_board = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

# Engine location
heuristics_engine = chess.engine.SimpleEngine.popen_uci('./optimality/Stockfish/src/stockfish')

#------------------------------------------------
#             CREATIVE CHESS ENGINE
#------------------------------------------------
class CreativeChessEngine:

    def __init__(self, color):
        self.color = color
        self.creativity_weight = 0.5
        self.optimality_weight = 0.5
        self.current_position = chess.Board(chess.STARTING_FEN)

    def play_move(self):

        # Check if it is the engine's turn
        if(self.color == self.current_position.turn):

            # Get the scores
            optimality_scores = get_optimality_scores(self.current_position, heuristics_engine)
            creativity_scores = get_creativity_scores(self.current_position)

            # Merge the scores using the weights
            hybrid_scores = self.get_hybrid_scores(optimality_scores, creativity_scores)

            # Get the top move
            chosen_move = sorted(hybrid_scores.items(), key=lambda item: item[1], reverse=True)[0][0]
            chosen_move_score = sorted(hybrid_scores.items(), key=lambda item: item[1], reverse=True)[0][1]
            chosen_move_optimality_score = optimality_scores[chosen_move]
            chosen_move_creativity_score = creativity_scores[chosen_move]

            # Play it and return it
            self.current_position.push(chosen_move)
            return chosen_move.uci(), chosen_move_score, chosen_move_optimality_score, chosen_move_creativity_score

        else:
            return false

    def receive_move(self, move):
        self.current_position.push(move)

    def game_done(self):
        return self.current_position.is_game_over()

    def game_result(self):
        return self.current_position.result()

    def get_hybrid_scores(self, optimality_scores, creativity_scores):

        merged_scores = {}
        hybrid_scores = {}
        
        # 1. Merge the two dicts together to get: (key, (O_score, C_score))
        for move in list(optimality_scores) + list(creativity_scores):

            # The move is in both dicts
            if(move in creativity_scores and move in optimality_scores):
                merged_scores[move] = (optimality_scores[move], creativity_scores[move])

            # The move is in one of the dicts
            elif(move in creativity_scores):
                merged_scores[move] = (0.0, creativity_scores[move])

            else:
                merged_scores[move] = (optimality_scores[move], 0.0)
            
        # 2. Loop over the merged scores and calculate the hybrid scores
        for move, scores in merged_scores.items()   :
            
            # Split up the cell of scores
            optimality_score, creativity_score = scores

            # Calculate hybrid scores
            hybrid_scores[move] = self.optimality_weight*optimality_score + self.creativity_weight*creativity_score

        # Return the hybrid scores
        return hybrid_scores

#------------------------------------------------
#                     MAIN
#------------------------------------------------

# Create a creative engine
creative_engine = CreativeChessEngine(chess.WHITE)

# Play against it, each time asking the player for a move in terminal
while(not(creative_engine.game_done())):

    # Let the engine play
    print("Engine played: ")
    print(creative_engine.play_move())

    # Ask the player for a move
    from_square = str(input("Enter from square: "))
    to_square = str(input("Enter to square: "))
    player_move = chess.Move(chess.parse_square(from_square), chess.parse_square(to_square))
    print("Player played: ")
    print(player_move.uci())

    # Feed the player move to the engine
    creative_engine.receive_move(player_move) 

# When done print the result
print("Game is over: black - white:")
print(creative_engine.game_result())

# Stop the heuristics engine
heuristics_engine.quit()