#!/usr/bin/env python3
"""
AbyssChess — Interactive Chess Engine for faza-kamal's GitHub Profile
Triggered by GitHub Actions when someone opens an Issue with move format.
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# ── Board Representation ────────────────────────────────────────────────────

# Piece symbols (Unicode)
PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',  # White
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',  # Black
    '.': '·'
}

INITIAL_BOARD = [
    ['r','n','b','q','k','b','n','r'],
    ['p','p','p','p','p','p','p','p'],
    ['.','.','.','.','.','.','.','.',],
    ['.','.','.','.','.','.','.','.',],
    ['.','.','.','.','.','.','.','.',],
    ['.','.','.','.','.','.','.','.',],
    ['P','P','P','P','P','P','P','P'],
    ['R','N','B','Q','K','B','N','R'],
]

DATA_FILE = Path("chess_data/game.json")
LEADERBOARD_FILE = Path("chess_data/leaderboard.json")
README_FILE = Path("README.md")

# ── Game State ──────────────────────────────────────────────────────────────

def load_game():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {
        "board": INITIAL_BOARD,
        "turn": "black",  # Black moves first (community plays black)
        "moves": [],
        "game_num": 1,
    }

def save_game(state):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def load_leaderboard():
    if LEADERBOARD_FILE.exists():
        with open(LEADERBOARD_FILE) as f:
            return json.load(f)
    return {}

def save_leaderboard(lb):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(lb, f, indent=2)

# ── Move Logic ──────────────────────────────────────────────────────────────

def parse_move(move_str):
    """Parse move like 'e2e4' → ((6,4), (4,4))"""
    move_str = move_str.strip().lower()
    if len(move_str) != 4:
        return None
    col_map = {'a':0,'b':1,'c':2,'d':3,'e':4,'f':5,'g':6,'h':7}
    try:
        fc = col_map[move_str[0]]
        fr = 8 - int(move_str[1])
        tc = col_map[move_str[2]]
        tr = 8 - int(move_str[3])
        return (fr, fc), (tr, tc)
    except (KeyError, ValueError):
        return None

def apply_move(board, from_pos, to_pos):
    """Apply move to board, return new board."""
    import copy
    new_board = copy.deepcopy(board)
    fr, fc = from_pos
    tr, tc = to_pos
    piece = new_board[fr][fc]
    new_board[tr][tc] = piece
    new_board[fr][fc] = '.'

    # Pawn promotion (auto queen)
    if piece == 'P' and tr == 0:
        new_board[tr][tc] = 'Q'
    if piece == 'p' and tr == 7:
        new_board[tr][tc] = 'q'

    return new_board

def is_valid_move(board, from_pos, to_pos, turn):
    """Basic validation — piece belongs to current player and destination not own piece."""
    fr, fc = from_pos
    tr, tc = to_pos
    piece = board[fr][fc]

    if piece == '.':
        return False, "Tidak ada bidak di posisi itu!"

    is_white = piece.isupper()
    is_black = piece.islower()

    if turn == "white" and is_black:
        return False, "Sekarang giliran putih!"
    if turn == "black" and is_white:
        return False, "Sekarang giliran hitam!"

    target = board[tr][tc]
    if target != '.' and (is_white == target.isupper()):
        return False, "Tidak bisa makan bidak sendiri!"

    return True, "OK"

def get_legal_moves(board, turn):
    """Get all legal moves for current player (simplified)."""
    moves = []
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece == '.':
                continue
            if turn == "white" and not piece.isupper():
                continue
            if turn == "black" and not piece.islower():
                continue
            # Generate basic destination squares
            for tr in range(8):
                for tc in range(8):
                    valid, _ = is_valid_move(board, (r,c), (tr,tc), turn)
                    if valid:
                        col = 'abcdefgh'[c]
                        tcol = 'abcdefgh'[tc]
                        moves.append(f"{col}{8-r}{tcol}{8-tr}")
    return moves

# ── Board Rendering ─────────────────────────────────────────────────────────

def render_board_md(board, legal_moves, turn, game_num, recent_moves, leaderboard):
    """Render board as markdown table with move links."""
    col_letters = 'ABCDEFGH'

    # Group legal moves by source
    moves_by_from = {}
    for mv in legal_moves:
        key = mv[:2].upper()
        if key not in moves_by_from:
            moves_by_from[key] = []
        moves_by_from[key].append(mv)

    # Board table
    header = "| | A | B | C | D | E | F | G | H |"
    sep    = "|---|---|---|---|---|---|---|---|---|"
    rows = [header, sep]

    for r in range(8):
        rank = str(8 - r)
        cells = [f"**{rank}**"]
        for c in range(8):
            piece = board[r][c]
            symbol = PIECES.get(piece, '·')
            cells.append(symbol)
        rows.append("| " + " | ".join(cells) + " |")

    board_md = "\n".join(rows)

    # Legal moves table
    move_rows = []
    for from_sq, moves in sorted(moves_by_from.items()):
        links = []
        for mv in sorted(moves):
            to_sq = mv[2:].upper()
            url = f"https://github.com/faza-kamal/faza-kamal/issues/new?title=chess%7Cmove%7C{mv}%7C{game_num}&body=Tekan+Submit+Issue+untuk+bermain!"
            links.append(f"[{to_sq}]({url})")
        move_rows.append(f"| **{from_sq}** | {', '.join(links)} |")

    moves_md = "| DARI | KE — *klik untuk bermain* |\n|------|---------------------------|\n"
    moves_md += "\n".join(move_rows) if move_rows else "| — | Tidak ada gerakan legal |"

    # Recent moves
    recent_md = ""
    if recent_moves:
        recent_md = "\n".join([f"| {m['move']} | [@{m['player']}](https://github.com/{m['player']}) |"
                               for m in recent_moves[-5:][::-1]])
        recent_md = "| Gerakan | Pemain |\n|---------|--------|\n" + recent_md
    else:
        recent_md = "*Belum ada gerakan.*"

    # Leaderboard
    lb_sorted = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
    lb_md = ""
    if lb_sorted:
        lb_md = "\n".join([f"| {i+1} | [@{u}](https://github.com/{u}) | {n} |"
                           for i, (u, n) in enumerate(lb_sorted)])
        lb_md = "| # | Pemain | Gerakan |\n|---|--------|---------|\n" + lb_md
    else:
        lb_md = "*Belum ada pemain.*"

    turn_label = "HITAM ♟" if turn == "black" else "PUTIH ♙"

    return board_md, moves_md, recent_md, lb_md, turn_label

# ── README Update ────────────────────────────────────────────────────────────

def update_readme(board_md, moves_md, recent_md, lb_md, turn_label, game_num):
    with open(README_FILE, 'r') as f:
        content = f.read()

    # Replace between markers
    def replace_section(text, marker, new_content):
        pattern = rf"(<!-- CHESS_{marker}_START -->).*?(<!-- CHESS_{marker}_END -->)"
        replacement = f"<!-- CHESS_{marker}_START -->\n{new_content}\n<!-- CHESS_{marker}_END -->"
        return re.sub(pattern, replacement, text, flags=re.DOTALL)

    content = replace_section(content, "BOARD", board_md)
    content = replace_section(content, "MOVES", moves_md)
    content = replace_section(content, "RECENT", recent_md)
    content = replace_section(content, "LEADERBOARD", lb_md)
    content = replace_section(content, "TURN", f"**Giliran: {turn_label}** — Game #{game_num}")

    with open(README_FILE, 'w') as f:
        f.write(content)

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    move_str = os.environ.get("CHESS_MOVE", "").strip()
    player   = os.environ.get("CHESS_PLAYER", "anonymous").strip()
    command  = os.environ.get("CHESS_CMD", "move").strip()

    state = load_game()
    lb    = load_leaderboard()

    if command == "new":
        state = {
            "board": INITIAL_BOARD,
            "turn": "black",
            "moves": [],
            "game_num": state.get("game_num", 1) + 1,
        }
        save_game(state)
        print("[+] Game baru dimulai!")
    elif command == "move":
        parsed = parse_move(move_str)
        if not parsed:
            print(f"[-] Format gerakan tidak valid: {move_str}")
            sys.exit(1)

        from_pos, to_pos = parsed
        valid, msg = is_valid_move(state["board"], from_pos, to_pos, state["turn"])
        if not valid:
            print(f"[-] Gerakan tidak valid: {msg}")
            sys.exit(1)

        state["board"] = apply_move(state["board"], from_pos, to_pos)
        state["moves"].append({
            "move": move_str.upper(),
            "player": player,
            "time": datetime.utcnow().isoformat()
        })
        state["turn"] = "white" if state["turn"] == "black" else "black"

        lb[player] = lb.get(player, 0) + 1
        save_leaderboard(lb)
        save_game(state)
        print(f"[+] Gerakan {move_str} oleh @{player} berhasil!")

    # Render & update README
    legal = get_legal_moves(state["board"], state["turn"])
    board_md, moves_md, recent_md, lb_md, turn_label = render_board_md(
        state["board"], legal, state["turn"],
        state["game_num"], state["moves"], lb
    )
    update_readme(board_md, moves_md, recent_md, lb_md, turn_label, state["game_num"])
    print("[+] README berhasil diupdate!")

if __name__ == "__main__":
    main()
