class GoalSawPlayer:

    def __init__(self, slotid : int, 
                 total_pieces_list : list[int], give_hint : bool = False, collected_pieces : list[int] | None = None, 
                 Goaled : bool = False):
        self._slotid = slotid
        self._total_pieces_list = total_pieces_list
        if collected_pieces is None:
            self._remaining_pieces = self._total_pieces_list.copy()
        else:
            self._remaining_pieces = [piece for piece in self._total_pieces_list if piece not in collected_pieces]

        self._goaled = Goaled
        self.give_hint = give_hint

    def Collect(self, pieces : list[int]) -> bool:
        for piece in pieces:
            self._remaining_pieces.remove(piece)
        return len(self._remaining_pieces) == 0

    def Goaled(self) -> bool:
        self._goaled = True
        return len(self._remaining_pieces) == 0

    def Get_Hint_pieces(self):
        if self._goaled or len(self._remaining_pieces):
            if len(self._remaining_pieces) == 0:
                return (0, None, None)
            if len(self._remaining_pieces) == 1:
                return (1, self._remaining_pieces[0], None)
            return (len(self._remaining_pieces), self._remaining_pieces[0], self._remaining_pieces[1])
        return (-1, None, None)

    def Get_total_pieces_num(self) -> int:
        if self._goaled or len(self._remaining_pieces) == 0:
            return len(self._total_pieces_list)
        else:
            return -1

    def Get_remaining_pieces_num(self) -> int:
        if self._goaled or len(self._remaining_pieces) == 0:
            return len(self._remaining_pieces)
        else:
            return -1

    def Get_Collected_amount(self) -> int:
        return len(self._total_pieces_list) - len(self._remaining_pieces)

    def Set_give_hint(self, value : bool | None = None) :
        if value is None:
            self.give_hint = not self.give_hint
        else:
            self.give_hint = value

    def __repr__(self):
        return f"GoalSawPlayer({self._slotid}, {self._total_pieces_list}, {self.give_hint}, {[piece for piece in self._total_pieces_list if piece not in self._remaining_pieces]}, {self._goaled})"

    def __str__(self):
        return f"{{player : {self._slotid}, reamainning pieces : {self._remaining_pieces} {", Goaled" if self._goaled else ""} {", give hint" if self.give_hint else ""}}}"


def Find_who_has_that_item(PlayerDict : dict[str, GoalSawPlayer], piece : int) -> str | None:
    for player in PlayerDict:
        if piece in PlayerDict[player]._total_pieces_list:
            return player
    return None