"""
盤面を表すboard_bit
- oが置かれているかどうか，xが置かれているかどうかの順に並べる．
- 桁の小さい方から3x3の盤面の左上にoが置かれているかどうか，10bit目からxが置かれているかどうかを示す全18bit．
例
0b001100100010010010
↓
001100100 010010010
    ↑黒     ↑白
001_100_100 010_010_010
3   2   1   3   2   1  行目
↓
.ox
.ox
xo.

board : 盤面
move : 手番
"""
import sys
sys.setrecursionlimit(50)
import queue
from functools import lru_cache
from typing import Tuple, Optional, List
from enum import IntEnum, auto
def error(*args, end="\n"): print(*args, file=sys.stderr, end=end)


class Move(IntEnum):
    o = 0
    x = 1


class Result(IntEnum):
    o_WIN = auto()
    DROW = auto()
    o_LOSE = auto()


class Status(IntEnum):
    o_WIN = auto()
    o_LOSE = auto()
    DROW = auto()
    o_MOVE = auto()
    x_MOVE = auto()
    ILLEGAL_OVERLAPPING = auto()
    ILLEGAL_QUANTITY = auto()
    ILLEGAL_WINQUANTITY = auto()
    ILLEGAL_OVERWIN = auto()


def popcount(bit: int) -> int:
    """
    1が立っているビットを数える

    Parameters
    ----------
    bit : int
        数えるbit

    Returns
    -------
    int
        数
    """
    c = (bit & 0x5555555555555555) + ((bit>>1) & 0x5555555555555555)
    c = (c & 0x3333333333333333) + ((c>>2) & 0x3333333333333333)
    c = (c & 0x0f0f0f0f0f0f0f0f) + ((c>>4) & 0x0f0f0f0f0f0f0f0f)
    c = (c & 0x00ff00ff00ff00ff) + ((c>>8) & 0x00ff00ff00ff00ff)
    c = (c & 0x0000ffff0000ffff) + ((c>>16) & 0x0000ffff0000ffff)
    c = (c & 0x00000000ffffffff) + ((c>>32) & 0x00000000ffffffff)
    return c


def bit2board(board_bit: int) -> str:
    """
    bit盤面から見た目が良い盤面stringを返す

    Parameters
    ----------
    board_bit : int
        bit盤面

    Returns
    -------
    str
        盤面string
        Status
        ...
        ...
        ...
    """
    board_list = [""] * 3
    status = get_board_status(board_bit)
    if status == Status.ILLEGAL_OVERLAPPING:
        for i in range(9):
            if board_bit >> i & 1:
                board_list[i // 3] += "o"
            else:
                board_list[i // 3] += "."
        for i in range(3):
            board_list[i] += " "
        for i in range(9):
            if board_bit >> (i + 9) & 1:
                board_list[i // 3] += "x"
            else:
                board_list[i // 3] += "."
    else:
        for i in range(9):
            if board_bit >> i & 1:
                board_list[i // 3] += "o"
            elif board_bit >> (i + 9) & 1:
                board_list[i // 3] += "x"
            else:
                board_list[i // 3] += "."
    return status.name + "\n" + '\n'.join(board_list)


def decrease_ox(board_bit: int, move: Move) -> List[int]:
    """
    board_bitからmoveのコマを1つ減らした盤面のlistを返す関数

    Parameters
    ----------
    board_bit : int
        盤面bit
    move : Move
        oかxどちらを減らすか

    Returns
    -------
    List[int]
        盤面のlist
    """
    decrease_board_list = []
    for i in range(9):
        if not board_bit >> (i + move.value * 9) & 1: continue
        tmp_board = board_bit ^ 1 << (i + move.value * 9)
        decrease_board_list.append(tmp_board)
    return decrease_board_list


def get_board_status(board_bit: int) -> Status:
    """
    盤面の状態を返す

    Parameters
    ----------
    board_bit : int
        盤面bit

    Returns
    -------
    Status
        盤面がどの状態化返す．Statusクラスのいずれか
        Status.o_WIN
        Status.o_LOSE
        Status.DROW
        Status.o_MOVE
        Status.x_MOVE
        Status.ILLEGAL_OVERLAPPING
        Status.ILLEGAL_QUANTITY
        Status.ILLEGAL_WINQUANTITY
        Status.ILLEGAL_OVERWIN
    """
    # 合法かどうか
    if popcount(board_bit >> 9 & board_bit) > 0:
        return Status.ILLEGAL_OVERLAPPING
    o_cnt = popcount(board_bit & ((1 << 9) - 1))
    x_cnt = popcount(board_bit >> 9 & ((1 << 9) - 1))
    o_move = False
    x_move = False
    finish = False
    # error(o_cnt, x_cnt)
    if o_cnt == x_cnt + 1 and o_cnt == 5:   # 最終盤面
        finish = True
    if o_cnt == x_cnt:    # oの手番
        o_move = True
    elif o_cnt == x_cnt + 1:    # xの手番
        x_move = True
    else:
        return Status.ILLEGAL_QUANTITY

    # 勝敗判定
    o_win_num = 0
    o_lose_num = 0
    for i in range(3):
        if popcount(board_bit >> (i * 3) & 0b111) == 3:
            o_win_num += 1
        if popcount(board_bit >> i & 0b001001001) == 3:
            o_win_num += 1
    if popcount(board_bit & 0b100010001) == 3 or popcount(board_bit & 0b001010100) == 3:
        o_win_num += 1
    for i in range(3):
        if popcount(board_bit >> (i * 3 + 9) & 7) == 3:
            o_lose_num += 1
        if popcount(board_bit >> (i + 9) & 0b001001001) == 3:
            o_lose_num += 1
    if popcount(board_bit >> 9 & 0b100010001) == 3 or popcount(board_bit >> 9 & 0b001010100) == 3:
        o_lose_num += 1

    if o_win_num >= 1 and o_lose_num >= 1:
        return Status.ILLEGAL_OVERWIN
    
    if o_win_num == 1:
        if o_move: 
            return Status.ILLEGAL_WINQUANTITY
        else:
            return Status.o_WIN
    if o_lose_num == 1:
        if x_move:
            return Status.ILLEGAL_WINQUANTITY
        else:
            return Status.o_LOSE

    # 3列揃ってるやつが2つ以上の場合，1手戻してみて揃ってる列が0になったらok．そうじゃなければ違法
    if o_win_num >= 1:
        flag_o_win = False
        for board in decrease_ox(board_bit, Move.o):
            new_board_o_win_num = 0
            for i in range(3):
                if popcount(board >> (i * 3) & 7) == 3:
                    new_board_o_win_num += 1
                if popcount(board >> i & 0b001001001) == 3:
                    new_board_o_win_num += 1
            if popcount(board & 0b100010001) == 3 or popcount(board & 0b001010100) == 3:
                new_board_o_win_num += 1
            if new_board_o_win_num == 0:
                flag_o_win = True
        if flag_o_win:
            return Status.o_WIN
        else:
            return Status.ILLEGAL_OVERWIN
    elif o_lose_num > 1:
        flag_o_lose = False
        for board in decrease_ox(board_bit, Move.x):
            new_board_o_lose_num = 0
            for i in range(3):
                if popcount(board_bit >> (i * 3 + 9) & 7) == 3:
                    new_board_o_lose_num += 1
                if popcount(board_bit >> (i + 9) & 0b001001001) == 3:
                    new_board_o_lose_num += 1
            if popcount(board_bit >> 9 & 0b100010001) == 3 or popcount(board_bit >> 9 & 0b001010100) == 3:
                new_board_o_lose_num += 1
            if new_board_o_lose_num == 0:
                flag_o_lose = True
        if flag_o_lose:
            return Status.o_LOSE
        else:
            return Status.ILLEGAL_OVERWIN

    if finish:
        return Status.DROW
    if o_move:
        return Status.o_MOVE
    if x_move:
        return Status.x_MOVE


def get_next_board(board_bit: int) -> List[int]:
    """
    受け取った盤面の1つ後の盤面を返す．

    Parameters
    ----------
    board_bit : int
        盤面bit

    Returns
    -------
    List[int]
        1つ後の盤面のlist
        違法な盤面は取り除かれている
    """
    status = get_board_status(board_bit)
    assert not status in [Status.ILLEGAL_OVERLAPPING, Status.ILLEGAL_OVERWIN,
                            Status.ILLEGAL_QUANTITY, Status.ILLEGAL_WINQUANTITY]
    if status in [Status.o_WIN, Status.o_LOSE, Status.DROW]:
        return []
    if status == Status.o_MOVE:
        move = Move.o
    elif status == Status.x_MOVE:
        move = Move.x
    else:
        return []
    next_board_list = []
    for i in range(9):
        if board_bit >> (i + 9 * move.value) & 1: continue
        tmp_board = board_bit ^ (1 << (i + 9 * move.value))
        if get_board_status(tmp_board) in [Status.ILLEGAL_OVERLAPPING, Status.ILLEGAL_OVERWIN,
                                            Status.ILLEGAL_QUANTITY, Status.ILLEGAL_WINQUANTITY]: continue
        next_board_list.append(tmp_board)
    return next_board_list


def get_pre_board(board_bit: int) -> List[Tuple[int, Move]]:
    """
    受け取った盤面の1つ前の盤面を返す．返した盤面がどちらの手番かも返す．

    Parameters
    ----------
    board_bit : int
        盤面bit

    Returns
    -------
    List[Tuple[int, Move]]
        1つ前の盤面のlist
        Tuple[int, Move]
            int
                1つ前の盤面
            Move    
                盤面の手番
    """
    status = get_board_status(board_bit)
    if status in [Status.o_WIN, Status.DROW, Status.x_MOVE]:
        o_num = popcount(board_bit & ((1 << 9) - 1))
        if not o_num: return []
        move = Move.o
    elif status in [Status.o_MOVE, Status.o_LOSE]:
        x_num = popcount(board_bit >> 9 & ((1 << 9) - 1))
        if not x_num: return []
        move = Move.x
    else:
        assert False
    pre_board_list = []
    for board in decrease_ox(board_bit, move):
        if get_board_status(board) in [Status.ILLEGAL_OVERLAPPING, Status.ILLEGAL_OVERWIN,
                                        Status.ILLEGAL_QUANTITY, Status.ILLEGAL_WINQUANTITY]: continue
        pre_board_list.append((board, move))
    return pre_board_list


@lru_cache(maxsize=None)
def get_result_dfs(board_bit: int) -> Result:
    """
    dfsで完全解析

    Parameters
    ----------
    board_bit : int
        盤面bit

    Returns
    -------
    Result
        その盤面の結果
    """
    status = get_board_status(board_bit)
    if status == Status.o_WIN:
        return Result.o_WIN
    elif status == Status.o_LOSE:
        return Result.o_LOSE
    elif status == Status.DROW:
        return Result.DROW
    win_num = 0
    lose_num = 0
    drow_num = 0
    for next_board in get_next_board(board_bit):
        next_board_result = get_result_dfs(next_board)
        if next_board_result == Result.o_WIN: win_num += 1
        elif next_board_result == Result.o_LOSE: lose_num += 1
        else: drow_num += 1
    if status == Status.o_MOVE:
        if win_num >= 1:
            return Result.o_WIN
        elif drow_num >= 1:
            return Result.DROW
        else:
            return Result.o_LOSE
    else:
        if lose_num >= 1:
            return Result.o_LOSE
        elif drow_num >= 1:
            return Result.DROW
        else:
            return Result.o_WIN


# # -----------------------------------------------
# # 前から?解析を行う．
# board_move_num = [[] for i in range(10)]
# for i in range(1 << 18):
#     status = get_board_status(i)
#     if status in [Status.ILLEGAL_OVERLAPPING, Status.ILLEGAL_OVERWIN,
#                     Status.ILLEGAL_QUANTITY, Status.ILLEGAL_WINQUANTITY]: continue
#     p_cnt = popcount(i)
#     board_move_num[p_cnt].append(i)
    
# for i, boards in enumerate(board_move_num):
#     print(i)
#     win_num = 0
#     lose_num = 0
#     drow_num = 0
#     for board in boards:
#         # if get_board_status(board) in [Status.o_WIN, Status.o_LOSE]: continue
#         if get_result_dfs(board) == Result.o_WIN:
#             win_num += 1
#         elif get_result_dfs(board) == Result.o_LOSE:
#             lose_num += 1
#         elif get_result_dfs(board) == Result.DROW:
#             drow_num += 1
#         else:
#             assert False
#     print(f"win  : {win_num:>4d}")
#     print(f"lose : {lose_num:>4d}")
#     print(f"drow : {drow_num:>4d}")
#     print(f"sum  : {len(boards):>4d}")

# for i, boards in enumerate(board_move_num):
#     # if i == 0: continue
#     print(f"""
# ----------------------------------
# ----- {i} ------------------------  
# ----------------------------------    
#     """)
#     for board in boards:
#         if get_board_status(board) in [Status.o_WIN, Status.o_LOSE]: continue
#         print(board)
#         print(get_result_dfs(board).name)
#         print(bit2board(board))
#         print()
#         output = [""] * 5
#         for next_board in get_next_board(board):
#             output[0] += f"{get_result_dfs(next_board).name:<8s}"
#             for i, line in enumerate(bit2board(next_board).split("\n")):
#                 output[i + 1] += f"{line:<8s}"
#         print("\n".join(output))
#         print()
# # 前から解析終わり


# # -------------------------------------------------
# # 後退解析を行う．
# # 勝ち終了盤面，負け終了盤面，引き分け終了盤面，途中o手番盤面，途中x手番盤面を辞書に保持する．keyは盤面，valueは勝ち負け
# # board_treeに次の盤面の数を格納
# # seen_boardに探索済みかどうかを格納
# # 終了盤面の場合valueは勝ち負け（引き分け）だが，途中盤面のvalueは引き分けに初期化
# board_win_lose_dict = dict()
# board_tree = dict()
# seen_board = dict()

# que = queue.Queue()
# start_board_flag = True
# for i in range(1 << 18):
#     status = get_board_status(i)
#     if status in [Status.ILLEGAL_OVERLAPPING, Status.ILLEGAL_OVERWIN,
#                     Status.ILLEGAL_QUANTITY, Status.ILLEGAL_WINQUANTITY]: continue
#     board_tree[i] = len(get_next_board(i))
#     seen_board[i] = False
#     if status == Status.o_WIN:
#         board_win_lose_dict[i] = Result.o_WIN
#         que.put(i)
#         if start_board_flag:
#             seen_board[i] = True
#     elif status == Status.o_LOSE:
#         board_win_lose_dict[i] = Result.o_LOSE
#         que.put(i)
#         if start_board_flag:
#             seen_board[i] = True
#     else:
#         board_win_lose_dict[i] = Result.DROW

# while not que.empty():
#     board = que.get()
#     for pre_board, move in get_pre_board(board):
#         if seen_board[pre_board]: continue
#         board_tree[pre_board] -= 1
#         if move == Move.o:
#             if board_win_lose_dict[board] == Result.o_WIN:
#                 board_win_lose_dict[pre_board] = Result.o_WIN
#                 seen_board[pre_board] = True
#                 que.put(pre_board)
#             else:
#                 if board_tree[pre_board] == 0:
#                     board_win_lose_dict[pre_board] = Result.o_LOSE
#                     seen_board[pre_board] = True
#                     que.put(pre_board)
#         else:
#             if board_win_lose_dict[board] == Result.o_WIN: 
#                 if board_tree[pre_board] == 0:
#                     board_win_lose_dict[pre_board] = Result.o_WIN
#                     seen_board[pre_board] = True
#                     que.put(pre_board)
#             else:
#                 board_win_lose_dict[pre_board] = Result.o_LOSE
#                 seen_board[pre_board] = True
#                 que.put(pre_board)

# # 全結果出力
# csv_list = []
# board_move_num = [[] for i in range(10)]
# for board in board_win_lose_dict.keys():
#     p_cnt = popcount(board)
#     board_move_num[p_cnt].append(board)
# for boards in board_move_num:
#     for board in boards:
#         record_list = list("bbbbbbbbb,")
#         for i in range(9):
#             if board >> i & 1:
#                 record_list[i] = "o"
#             elif board >> (i + 9) & 1:
#                 record_list[i] = "x"
#         record_str = ''.join(record_list) 
#         if board_win_lose_dict[board] == Result.o_WIN:
#             record_str += "o"
#         elif board_win_lose_dict[board] == Result.o_LOSE:
#             record_str += "x"
#         else:
#             record_str += "d"       
#         csv_list.append(record_str)
# with open("result.csv", mode='w') as f:
#     f.write('\n'.join(csv_list))


# # 結果の可視化
# board_move_num = [[] for i in range(10)]
# for board in board_win_lose_dict.keys():
#     p_cnt = popcount(board)
#     board_move_num[p_cnt].append(board)

# for i, boards in enumerate(board_move_num):
#     print(i)
#     win_num = 0
#     lose_num = 0
#     drow_num = 0
#     for board in boards:
#         # if get_board_status(board) in [Status.o_WIN, Status.o_LOSE]: continue
#         if board_win_lose_dict[board] == Result.o_WIN:
#             win_num += 1
#         elif board_win_lose_dict[board] == Result.o_LOSE:
#             lose_num += 1
#         elif board_win_lose_dict[board] == Result.DROW:
#             drow_num += 1
#         else:
#             assert False
#     print(f"win  : {win_num:>4d}")
#     print(f"lose : {lose_num:>4d}")
#     print(f"drow : {drow_num:>4d}")
#     print(f"sum  : {len(boards):>4d}")

# for i, boards in enumerate(board_move_num):
#     # if i == 0: continue
#     print(f"""
# ----------------------------------
# ----- {i} ------------------------  
# ----------------------------------    
#     """)
#     for board in boards:
#         if get_board_status(board) in [Status.o_WIN, Status.o_LOSE]: continue
#         print(board)
#         print(board_win_lose_dict[board].name)
#         print(bit2board(board))
#         print()
#         output = [""] * 5
#         for next_board in get_next_board(board):
#             output[0] += f"{board_win_lose_dict[next_board].name:<8s}"
#             for i, line in enumerate(bit2board(next_board).split("\n")):
#                 output[i + 1] += f"{line:<8s}"
#         print("\n".join(output))
#         print()



# # get_pre_boardのデバッグ
# for i, board in enumerate(o_move_board.keys()):
#     print("--------------------------------")
#     print(board)
#     print(bit2board(board))
#     print()
#     for pre_board, move in get_pre_board(board):
#         print(pre_board, move)
#         print(bit2board(pre_board))
#         print()


# # 全盤面出力
# for i in range(1 << 18):
#     res = bit2board(i)
#     # if not "o_WIN" in res: continue
#     print(i)
#     print(res)
#     print()


# 2 ** 18通りのうちそれぞれどの状態の盤面か
cnt_dict = {}
for status in Status:
    cnt_dict[status] = 0
for i in range(1 << 18):
    cnt_dict[get_board_status(i)] += 1
for key, value in cnt_dict.items():
    print(f"{key.name:<20s} : {value:>6d}")

