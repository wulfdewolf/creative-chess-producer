# -----------------------------------------------------------------
#
#       Producing creative chess through chess engine selfplay
#
#                       author: Wolf De Wulf
#
# -----------------------------------------------------------------
import chess
import requests
import os

# Creative Chess Producer class


class CreativeChessProducer:
    def __init__(
        self,
        white_engine,
        black_engine,
        thresholds_w,
        thresholds_b,
        added_weight,
        logger,
    ):
        self.white_engine = white_engine
        self.black_engine = black_engine
        self.thresholds_w = thresholds_w
        self.thresholds_b = thresholds_b
        self.added_weight = added_weight
        self.logger = logger

    # Lets the two engines play a complete game
    def play_game(self):

        # Reset position
        self.current_position = chess.Board(chess.STARTING_FEN)
        self.game = chess.pgn.Game()
        self.move_count = 0
        self.game_node = False

        # Prepare both engines to start a new game
        self.white_engine.new_game(chess.WHITE)
        self.black_engine.new_game(chess.BLACK)

        while not (self.current_position.is_game_over(claim_draw=True)):

            # Increase move count
            self.move_count += 1

            # Let white engine play
            move, indices = self.white_engine.play_move(self.current_position)
            self.register_move(move, indices)

            # If the game isn't over
            if not (self.current_position.is_game_over(claim_draw=True)):

                # Let black engine play
                move, indices = self.black_engine.play_move(
                    self.current_position)
                self.register_move(move, indices)

    # Registers a played move
    def register_move(self, move, indices):

        # Push it to the position
        self.current_position.push(move)

        # Push it to the PGN game
        self.game_node = (
            self.game.add_variation(move)
            if isinstance(self.game_node, bool)
            else self.game_node.add_variation(move)
        )

        # Add the indices as comment
        self.game_node.comment = str(indices)

    # Run the CCP for a given number of games
    def run(self, N):

        i = 0
        while i < N:
            try:
                self.play_game()

                # When the game is done, let the engines evaluate whether it is to be accepted or not
                evaluation_white, evaluation_black = self.evaluate_game()
                self.logger.info("-----------------------------------------")
                self.logger.info("GAME DONE, evaluating...")
                self.logger.info("white:")
                self.logger.info(
                    str(
                        [
                            percentage
                            for achieved, percentage, threshold in evaluation_white
                        ]
                    )
                )
                self.logger.info(str(self.white_engine.weights))
                self.logger.info("black:")
                self.logger.info(
                    str(
                        [
                            percentage
                            for achieved, percentage, threshold in evaluation_black
                        ]
                    )
                )
                self.logger.info(str(self.black_engine.weights))

                # Accept
                if all(achieved for achieved, _, _ in evaluation_white) and all(
                    achieved for achieved, _, _ in evaluation_black
                ):

                    self.logger.info("ACCEPT")

                    # Store the accepted game
                    self.store_game()

                # Or reject and update
                else:
                    self.logger.info("REJECT")
                    self.white_engine.update_weights(
                        evaluation_white, self.added_weight
                    )
                    self.black_engine.update_weights(
                        evaluation_black, self.added_weight
                    )

                # Next iteration
                self.logger.info("-----------------------------------------")
                i += 1

            # If a connection error occured, act as if the game never happened
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                self.logger.info("Connection error occurred, skipped game.")

    # Returns for both engines a list that contains for each of the engine's weights: (a boolean that indicates if they achieved their threshold, the actual percentage, the threshold itself)
    def evaluate_game(self):

        # Calculate evaluations
        white_evaluation = [
            ((count / self.move_count) >= threshold,
             count / self.move_count, threshold)
            for count, threshold in zip(self.white_engine.counts, self.thresholds_w)
        ]
        black_evaluation = [
            ((count / self.move_count) >= threshold,
             count / self.move_count, threshold)
            for count, threshold in zip(self.black_engine.counts, self.thresholds_b)
        ]

        return white_evaluation, black_evaluation

    # Stores an accepted game with its evaluation values to the games folder
    def store_game(self):

        # Create a folder for the game
        foldername = "./games/game" + str(len(os.listdir("./games")))
        os.makedirs(foldername)

        # Store the weights in the event header
        self.game.headers["Event"] = str(self.white_engine.weights) + str(
            self.black_engine.weights
        )

        # Store the counts in the site header
        self.game.headers["Site"] = str(self.white_engine.counts) + str(
            self.black_engine.counts
        )

        # Store the thresholds in the player headers
        self.game.headers["White"] = str(self.thresholds_w)
        self.game.headers["Black"] = str(self.thresholds_b)

        # Print the game to a pgn file in the folder
        print(self.game, file=open(foldername + "/game.pgn", "w"), end="\n\n")
