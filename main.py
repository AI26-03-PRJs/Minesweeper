import pygame
import time
import random
from pyDatalog import pyDatalog
from src.minesweeper import MineSweeper

# =========================================================================
# Section 1: Define First-Order Logic Terms (FOL Terms)
# Students should define the required terms, facts, and rules for pyDatalog here.
# =========================================================================
pyDatalog.create_terms('R, C, Val, H, F, R2, C2, CellInfo, IsHiddenNeighbor, Safe, Mine')

# Suggested constants for the agent's internal memory (Shadow Board)
AGENT_UNKNOWN = -1
AGENT_FLAGGED = -2

# =========================================================================
# Section 2: Generation of Logical Facts and Rules
# =========================================================================

def init_static_facts(rows, cols):
    pyDatalog.clear()
    pyDatalog.create_terms('R, C, Val, H, F, R2, C2, CellInfo, IsHiddenNeighbor, Safe, Mine')

def init_rules():
    
    Safe(R2,C2)<=CellInfo(R,C,Val,H,F) & (Val==F) & IsHiddenNeighbor(R,C,R2,C2)

    Mine(R2,C2)<=CellInfo(R,C,Val,H,F) & (Val==H+F) & IsHiddenNeighbor(R,C,R2,C2)


def update_knowledge_base(agent_board, rows, cols):
    CellInfo.clear()
    IsHiddenNeighbor.clear()

    directions=[(-1,-1),(-1,0),(-1,1),
                (0,-1),        (0,1),
                (1,-1),(1,0),(1,1)]

    for (r,c),val in agent_board.items():
        if val>=0:
            hidden_neighbors=[]
            flags=0

            for dr,dc in directions:
                nr,nc=r+dr,c+dc

                if 0<=nr<rows and 0<=nc<cols:
                    state=agent_board[(nr,nc)]

                    if state==AGENT_UNKNOWN:
                        hidden_neighbors.append((nr,nc))

                    elif state==AGENT_FLAGGED:
                        flags+=1

            h_count=len(hidden_neighbors)

            if h_count>0:
                +CellInfo(r,c,val,h_count,flags)
                for (nr,nc) in hidden_neighbors:
                    +IsHiddenNeighbor(r,c,nr,nc)


def query_solver():
    safe_moves = []
    mine_moves = []

    ans_safe=Safe(R,C)

    if ans_safe:
        for r,c in ans_safe.data:
            safe_moves.append((r,c))

    ans_mine=Mine(R,C)

    if ans_mine:
        for r,c in ans_mine.data:
            mine_moves.append((r,c))

    return list(set(safe_moves)),list(set(mine_moves))

# =========================================================================
# Section 3: Uncertainty Handling Strategy (Smart Guess) - Optional/Bonus
# =========================================================================

def get_safest_guess(agent_board,rows,cols):
    """
    Task 5: Calculate the probability of cells being mines during a logical deadlock.
    """
    unknowns=[pos for pos,val in agent_board.items() if val==AGENT_UNKNOWN]

    if not unknowns:
        return None

    probs={pos:0.0 for pos in unknowns}

    directions=[(-1,-1),(-1,0),(-1,1),
                (0,-1),(0,1),
                (1,-1),(1,0),(1,1)]

    for (r,c),val in agent_board.items():

        if val>0:
            hidden=[]
            flags=0

            for dr,dc in directions:
                nr,nc=r+dr,c+dc

                if 0<=nr<rows and 0<=nc<cols:

                    if agent_board[(nr,nc)]==AGENT_UNKNOWN:
                        hidden.append((nr,nc))

                    elif agent_board[(nr,nc)]==AGENT_FLAGGED:
                        flags+=1

            if hidden:
                p=(val-flags)/len(hidden)

                for h in hidden:
                    probs[h]=max(probs[h],p)

    best_guess=min(probs.keys(),key=lambda k:probs[k])

    return best_guess

# =========================================================================
# Section 4: Main Agent Loop
# =========================================================================

def prolog_solver(game):
    # Initialize static facts and rules
    init_static_facts(game.rows, game.cols)
    init_rules()
    
    # Create agent's internal memory (Shadow Board) - initially all cells are unknown
    agent_board = {}
    for r in range(game.rows):
        for c in range(game.cols):
            agent_board[(r, c)] = AGENT_UNKNOWN

    # Get starting position (Guaranteed to be 0 and safe according to the project documentation)
    start_r, start_c = game.get_start_pos()
    print(f"Starting at guaranteed safe position: {start_r}, {start_c}")
    
    # First move: Reveal the starting cell and record it in the agent's memory
    start_val = game.reveal(start_r, start_c)
    agent_board[(start_r, start_c)] = start_val if start_val is not None else 0
    
    running = True
    while running and not game.game_over:
        # Handle Pygame events to prevent the window from freezing/crashing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1. Update the knowledge base based on the latest state of the agent's memory
        update_knowledge_base(agent_board, game.rows, game.cols)

        # 2. Query the logic engine
        safe_moves, mine_moves = query_solver()
        move_made = False

        # 3. Apply the extracted logical actions to the game environment and update memory
        # Hint: Reveal safe cells first, then flag the mine cells.
        for r,c in safe_moves:

            if agent_board[(r,c)]==AGENT_UNKNOWN:
                val=game.reveal(r,c)
                agent_board[(r,c)]=val if val is not None else -1
                move_made=True

        # Flag Mine Cells
        for r,c in mine_moves:

            if agent_board[(r,c)]==AGENT_UNKNOWN:
                game.flag(r,c)
                agent_board[(r,c)]=AGENT_FLAGGED
                move_made=True

        # Deadlock management
        if not move_made and not game.game_over:

            print("Logical deadlock! Attempting guess...")

            guess=get_safest_guess(agent_board,game.rows,game.cols)

            if guess:
                r,c=guess
                print(f"Guessing cell ({r}, {c})")

                val=game.reveal(r,c)
                agent_board[(r,c)]=val if val is not None else -1

            else:
                print("No more available moves!")
                break

        # 4. Deadlock management (if no deterministic logical move is found)
        if not move_made and not game.game_over:
            print("Logical deadlock! Attempting guess...")
            # First use the Heuristic, and if no data is available, make a completely random choice
            pass

        # Render the environment and add a short delay to observe the solving process
        game.render()
        time.sleep(0.2)

    # Keep the window open after the game ends
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        game.render()

if __name__ == "__main__":
    # Default settings based on the first scenario (Simple level) in the evaluation table
    # Note: auto_flood_fill must be False to preserve the encapsulation of the agent's memory.
    ms = MineSweeper(rows=9, cols=9, mines=9, seed=99 , auto_flood_fill=False)
    prolog_solver(ms)