from argparse import Namespace
import asyncio
import logging
import sys
import time
import typing

from CommonClient import CommonContext, ClientCommandProcessor

from CommonClient import server_loop, logger, gui_enabled
from NetUtils import ClientStatus, HintStatus, NetworkItem
from Utils import async_start, init_logging

from .Player import GoalSawPlayer, Find_who_has_that_item

class GoalSawCommandProcessor(ClientCommandProcessor):
    def _cmd_refresh_menu(self):
        """Refreshed the in game menu in case of maps being inaccessible when they should be"""
        self.ctx.refresh_menu()

class GoalSawContext(CommonContext):
    command_processor = GoalSawCommandProcessor
    game_command_sender_task: typing.Optional["asyncio.Task[None]"] = None
    game_message_listener_task: typing.Optional["asyncio.Task[None]"] = None
    game = "Jigsaw"
    tags = {"HintGame", "Tracker"}
    items_handling = 0b111  # receive all items for /received

    item_list: list[str] = []
    PlayerDict : dict[str, GoalSawPlayer] = {}
    slot_map : dict[int, str] = {}
    authentificated : bool = False
    initialized : bool = False
    item_buffer : list[NetworkItem] = []
    waiting_for_release_right : list[str] = []

    base_title = "GoalSaw Manager Client"

    def reset_server_state(self):
        self.item_list = []
        self.PlayerDict.clear()
        self.authentificated = False
        self.initialized = False
        self.item_buffer = []
        self.waiting_for_release_right = []

        super().reset_server_state()

    async def handle_slot_data(self, slot_data: dict):
        # this is where i build the extra menu
        # and load all the hints
        #
        #
        # self.game_map_menu.generate_menu()
        # if not self.client_map_menu:
        #     self.client_map_menu = self.get_menu()
        # self.refresh_menu()
        # self.client_map_menu.build()
        if ("GoalSaw_solution" not in slot_data):
            logger.error("Error, the GoalSaw_solution is missing")
        else:
            GoalSaw_solution = slot_data["GoalSaw_solution"]
            #logger.info(GoalSaw_solution)
            for player in GoalSaw_solution:
                self.PlayerDict[player] = GoalSawPlayer(player, GoalSaw_solution[player])
                # msg = {"cmd": "CreateHints", "locations": GoalSaw_solution[player], "player": int(player)}
                # async_start(self.send_msgs([msg]), name="Create_Hints")
            self.initialized = True
            logger.info(f"Initialization Done!" + (f" there is {len(self.item_buffer)} item to catch up" if len(self.item_buffer) > 0 else ""))
            while len(self.item_buffer) > 0:
                item = self.item_buffer.pop()
                self.handle_item(item)
        return    
    
    # def gather_all_location(self) -> bool:

    #     self.location_names.
    #     if not input_text:
    #         hints = {hint.re_check(self.ctx, self.client.team) for hint in
    #                  self.ctx.hints[self.client.team, self.client.slot]}
    #         self.ctx.hints[self.client.team, self.client.slot] = hints
    #         self.ctx.notify_hints(self.client.team, list(hints), recipients=(self.client.slot,))
    #         self.output(f"A hint costs {self.ctx.get_hint_cost(self.client.slot)} points. "
    #                     f"You have {points_available} points.")
    #         if hints and Utils.version_tuple < (0, 5, 0):
    #             self.output("It was recently changed, so that the above hints are only shown to you. "
    #                         "If you meant to alert another player of an above hint, "
    #                         "please let them know of the content or to run !hint themselves.")
    #         return True

    #     elif input_text.isnumeric():
    #         game = self.ctx.games[self.client.slot]
    #         hint_id = int(input_text)
    #         hint_name = self.ctx.item_names[game][hint_id] \
    #             if not for_location and hint_id in self.ctx.item_names[game] \
    #             else self.ctx.location_names[game][hint_id] \
    #             if for_location and hint_id in self.ctx.location_names[game] \
    #             else None
    #         if hint_name in self.ctx.non_hintable_names[game]:
    #             self.output(f"Sorry, \"{hint_name}\" is marked as non-hintable.")
    #             hints = []
    #         elif not for_location:
    #             hints = collect_hints(self.ctx, self.client.team, self.client.slot, hint_id)
    #         else:
    #             hints = collect_hint_location_id(self.ctx, self.client.team, self.client.slot, hint_id)

    #     else:
    #         game = self.ctx.games[self.client.slot]
    #         if game not in self.ctx.all_item_and_group_names:
    #             self.output("Can't look up item/location for unknown game. Hint for ID instead.")
    #             return False
    #         names = self.ctx.all_location_and_group_names[game] \
    #             if for_location else \
    #             self.ctx.all_item_and_group_names[game]
    #         hint_name, usable, response = get_intended_text(input_text, names)

    #         if usable:
    #             if hint_name in self.ctx.non_hintable_names[game]:
    #                 self.output(f"Sorry, \"{hint_name}\" is marked as non-hintable.")
    #                 hints = []
    #             elif not for_location and hint_name in self.ctx.item_name_groups[game]:  # item group name
    #                 hints = []
    #                 for item_name in self.ctx.item_name_groups[game][hint_name]:
    #                     if item_name in self.ctx.item_names_for_game(game):  # ensure item has an ID
    #                         hints.extend(collect_hints(self.ctx, self.client.team, self.client.slot, item_name))
    #             elif not for_location and hint_name in self.ctx.item_names_for_game(game):  # item name
    #                 hints = collect_hints(self.ctx, self.client.team, self.client.slot, hint_name)
    #             elif hint_name in self.ctx.location_name_groups[game]:  # location group name
    #                 hints = []
    #                 for loc_name in self.ctx.location_name_groups[game][hint_name]:
    #                     if loc_name in self.ctx.location_names_for_game(game):
    #                         hints.extend(
    #                             collect_hint_location_name(self.ctx, self.client.team, self.client.slot, loc_name)
    #                         )
    #             else:  # location name
    #                 hints = collect_hint_location_name(self.ctx, self.client.team, self.client.slot, hint_name)

    #         else:
    #             self.output(response)
    #             return False

    #     if hints:
    #         new_hints = set(hints) - self.ctx.hints[self.client.team, self.client.slot]
    #         old_hints = list(set(hints) - new_hints)
    #         if old_hints and not new_hints:
    #             self.ctx.notify_hints(self.client.team, old_hints)
    #             self.output("Hint was previously used, no points deducted.")
    #         if new_hints:
    #             found_hints = [hint for hint in new_hints if hint.found]
    #             not_found_hints = [hint for hint in new_hints if not hint.found]
    #             if not not_found_hints:  # everything's been found, no need to pay
    #                 can_pay = 1000
    #             elif cost:
    #                 can_pay = int((points_available // cost) > 0)  # limit to 1 new hint per call
    #             else:
    #                 can_pay = 1000

    #             self.ctx.random.shuffle(not_found_hints)
    #             # By popular vote, make hints prefer non-local placements
    #             not_found_hints.sort(key=lambda hint: int(hint.receiving_player != hint.finding_player))
    #             # By another popular vote, prefer early sphere
    #             not_found_hints.sort(key=lambda hint: self.ctx.get_sphere(hint.finding_player, hint.location),
    #                                  reverse=True)

    #             hints = found_hints + old_hints
    #             while can_pay > 0:
    #                 if not not_found_hints:
    #                     break
    #                 hint = not_found_hints.pop()
    #                 hints.append(hint)
    #                 can_pay -= 1
    #                 self.ctx.hints_used[self.client.team, self.client.slot] += 1

    #             self.ctx.notify_hints(self.client.team, hints)
    #             if not_found_hints:
    #                 points_available = get_client_points(self.ctx, self.client)
    #                 if hints and cost and int((points_available // cost) == 0):
    #                     self.output(
    #                         f"There may be more hintables, however, you cannot afford to pay for any more. "
    #                         f" You have {points_available} and need at least "
    #                         f"{self.ctx.get_hint_cost(self.client.slot)}.")
    #                 elif hints:
    #                     self.output(
    #                         "There may be more hintables, you can rerun the command to find more.")
    #                 else:
    #                     self.output(f"You can't afford the hint. "
    #                                 f"You have {points_available} points and need at least "
    #                                 f"{self.ctx.get_hint_cost(self.client.slot)}.")
    #             self.ctx.save()
    #             return True

    #     else:
    #         if points_available >= cost:
    #             if for_location:
    #                 self.output(f"Nothing found for recognized location name \"{hint_name}\". "
    #                             f"Location appears to not exist in this multiworld.")
    #             else:
    #                 self.output(f"Nothing found for recognized item name \"{hint_name}\". "
    #                             f"Item appears to not exist in this multiworld.")
    #         else:
    #             self.output(f"You can't afford the hint. "
    #                         f"You have {points_available} points and need at least "
    #                         f"{self.ctx.get_hint_cost(self.client.slot)}.")
    #         return False
    def processAdminResponce(self, msg) :
        if msg == "Login successful. You can now issue server side commands.": #yes connection
            self.authentificated = True
            logger.info("Loggin ok: gathering Goal status to make sure nothing is missed")
            msglist = [{"cmd": "Get", "keys" : [f"_read_client_status_{self.team}_{player}" for player in self.slot_map]}]
            if len(self.waiting_for_release_right) > 0:
                msglist += [{"cmd": "Say", "text": f"catching up with people waiting for release right"}]
                for name in self.waiting_for_release_right:
                    msglist += [{"cmd": "Say", "text": f"!admin /allow_release {name}"}]
            async_start(self.send_msgs(msglist), name="post_loggin_data")
        pass

    def handle_item(self, item : NetworkItem):
        player = self.slot_map.get(item.player, None)
        #logger.info(f"piece {item} is process. found player is {player}")
        if player is not None:
            done = self.PlayerDict[player].Collect([item.location])
            #logger.info(f"a piece has been collected. {self.PlayerDict}")
            command_list = []
            if done:
                command_list.append({"cmd" : "Say", "text": f"player {player} have collected all of its puzzle pieces ({self.PlayerDict[player].Get_total_pieces_num()}), it is now able to release"})
                if self.authentificated:
                    command_list.append({"cmd" : "Say", "text": f"!admin /allow_release {player}"})
                else:
                    command_list.append({"cmd" : "Say", "text": f"However, the Client does not yet have admin rights. please do !admin login"})
                    self.waiting_for_release_right.append(player)
            if self.PlayerDict[player].give_hint:
                nb, hint1, hint2 = self.PlayerDict[player].Get_Hint_pieces()
                if nb == 1:
                    command_list.append({"cmd": "CreateHints", "locations" : [hint1], "player" : item.player, "status" : HintStatus.HINT_PRIORITY})
                elif nb > 1:
                    command_list.append({"cmd": "CreateHints", "locations" : [hint1, hint2], "player" : item.player, "status" : HintStatus.HINT_PRIORITY})
            if len(command_list) > 0:
                async_start(self.send_msgs(command_list), name=f"allow_{player}_release")

    def on_package(self, cmd, args):
        super().on_package(cmd, args)

        # Add item names to list
        if cmd == "Retrieved":
            if f"_read_item_name_groups_{self.game}" in args["keys"]:
                self.item_list = args["keys"][f"_read_item_name_groups_{self.game}"]["Everything"]
            for player in self.slot_map:
                if player != self.slot:
                    if f"_read_client_status_{self.team}_{player}" in args["keys"]:
                        #logger.info(f"checking if {player} is done ({args})")
                        status : ClientStatus = args["keys"][f"_read_client_status_{self.team}_{player}"]
                        if status == ClientStatus.CLIENT_GOAL:
                            isdone = self.PlayerDict[self.slot_map[player]].Goaled()
                            if isdone and self.authentificated:
                                msg = {"cmd" : "Say", "text": f"During reconnection, player {self.slot_map[player]} was found to have collected all of its puzzle pieces ({self.PlayerDict[self.slot_map[player]].Get_total_pieces_num()}), it is now able to release"}
                                msg_cmd = {"cmd" : "Say", "text": f"!admin /allow_release {self.slot_map[player]}"}
                                async_start(self.send_msgs([msg, msg_cmd]), name=f"allow_{player}_release")

                            #logger.info(f"{self.slot_map[player]} has in fact Goald")

        if cmd == "ReceivedItems":
            items = args["items"]
            #logger.info(f"Items are recieved : {items}")
            if self.initialized:
                for item in items:
                    self.handle_item(item)
            else:
                #logger.info("the client is not fully initialized. buffering the items")
                self.item_buffer += items

        if cmd == "Connected":
            for playerInfo in args["players"]:
                if (playerInfo.team == self.team):
                    self.slot_map[playerInfo.slot] = playerInfo.name
            async_start(self.handle_slot_data(args["slot_data"]))

        if cmd == "PrintJSON":
            if "type" in args:
                if args["type"] == "ItemSend" and args["receiving"] == self.slot:
                    item: NetworkItem = args["item"]
                    text = self.parse_message(args["data"], sending = item.player)
                elif args["type"] == "Goal":
                    #logger.info(f"a Goal message is, the data are {args}")
                    Goalteam = args["team"]
                    Goalslot = args["slot"] 
                    msglist = []
                    if Goalteam == self.team and Goalslot != self.slot:
                        name = self.slot_map[Goalslot]
                        done = self.PlayerDict[name].Goaled()
                        if done:
                            msglist.append({"cmd": "Say", "text": f"Player {name} has already collected all of its peices"})
                            if self.authentificated:
                                msglist.append({"cmd": "Say", "text": f"!admin /allow_release {name}"})
                        else:
                            remaining = self.PlayerDict[name].Get_remaining_pieces_num()
                            msglist.append({"cmd": "Say", "text": f"However, player {name} still need to collect {remaining} pieces to finish their game.They now can use !collect, !goalhint and !goalstatus"})
                        async_start(self.send_msgs(msglist))

                    text = self.parse_message(args["data"])
                elif args["type"] == "CommandResult" :
                    #logger.info(f"got a command result : {args}")
                    self.processAdminResponce(args["data"][0]["text"])
                elif (args["type"] == "Chat" or args["type"] == "ServerChat") and args["slot"] != self.slot:
                    #logger.info(f"a chat or ServerChat message is, the data are {args}")
                    if args["message"] == "!help":
                        async_start(self.send_msgs([{"cmd": "Say", "text" : f"[Goal Command can only be used after Goal of your slot] : !goalhint, !goalstatus (responce to )"}]))
                    if args["message"] == "!goalstatus":
                        name = self.slot_map[args["slot"]]
                        remaining = self.PlayerDict[name].Get_remaining_pieces_num()
                        if remaining == -1 :
                            async_start(self.send_msgs([{"cmd": "Say", "text": f"sorry {name}, But you can't use that command before goal in your game"}]))
                        elif remaining == 0 :
                            total = self.PlayerDict[name].Get_total_pieces_num()
                            async_start(self.send_msgs([{"cmd": "Say", "text": f"all {total} pieces from {name}'s world have been collected. GG"}]))
                        else :
                            total = self.PlayerDict[name].Get_total_pieces_num()
                            async_start(self.send_msgs([{"cmd": "Say", "text": f"{name} : collected {total-remaining}/{total}"}]))
                    if args["message"] == "!goalhint":
                        name = self.slot_map[args["slot"]]
                        remaining = self.PlayerDict[name].Get_remaining_pieces_num()
                        if remaining == -1 :
                            async_start(self.send_msgs([{"cmd": "Say", "text": f"sorry {name}, But you can't use that command before goal in your game"}]))
                        else:
                            self.PlayerDict[name].Set_give_hint()
                            msglist = []
                            if self.PlayerDict[name].give_hint:
                                msglist.append({"cmd": "Say", "text": f"{name} has enabled goalhint for their slot"})
                                nb, hint1, hint2 = self.PlayerDict[name].Get_Hint_pieces()
                                if nb == -1:
                                    logger.info("whut? -1 hint when hint is allowed?")
                                elif nb == 1:
                                    msglist.append({"cmd": "CreateHints", "locations" : [hint1], "player" : args["slot"], "status" : HintStatus.HINT_PRIORITY})
                                else:
                                    msglist.append({"cmd": "CreateHints", "locations" : [hint1, hint2], "player" : args["slot"], "status" : HintStatus.HINT_PRIORITY})
                            else:
                                msglist.append({"cmd": "Say", "text": f"{name} has disabled goalhint for their slot"})
                            async_start(self.send_msgs(msglist), name=f"change goalhint for {name}")
    def parse_message(self, data: list[dict], sending: int | None = None) -> str: # data pats not cast to JSONMessagePart as expected, dict instead
        message = ""
        for part in data:
            text = part["text"]
            if "type" in part:
                if part["type"] == "item_id":
                    text = self.item_names.lookup_in_slot(int(text), self.slot)
                elif part["type"] == "location_id":
                    text = self.location_names.lookup_in_slot(int(text), sending)
                elif part["type"] == "player_id":
                    text = self.player_names[int(text)]
            message += text

        return message

    def on_ui_command(self, text):

        if text == "/debug_info":
            logger.info(f"PlayerDict : {self.PlayerDict}\n" +
                        f"slot_map : {self.slot_map}\n" +
                        f"buffer_item : {self.item_buffer}")
            return
        if text.startswith("/forcegoal"):
            player = text[11:]
            if player not in self.PlayerDict:
                logger.info(f"player {player} is not real")
            else:
                self.PlayerDict[player].Goaled()
            return

        if text=="/status":
            res = "total status :\n"
            for player in self.PlayerDict:
                collected = self.PlayerDict[player].Get_Collected_amount()
                total = self.PlayerDict[player].Get_total_pieces_num()
                remaining = self.PlayerDict[player].Get_remaining_pieces_num()
                if total == -1:
                    res += f"{player} : Not Goaled, {collected} pieces collected\n"
                else:
                    res += f"{player} : {collected}/{total} pieces collected, {remaining} pieces remaining\n"
            logger.info(res)
            return

        return super().on_ui_command(text)
        
    async def shutdown(self):
        self.server_address = ""
        self.username = None
        self.password = None
        self.cancel_autoreconnect()
        if self.server and not self.server.socket.closed:
            await self.server.socket.close()
        if self.server_task:
            await self.server_task
        if self.game_command_sender_task:
            self.game_command_sender_task.cancel()
        if self.game_message_listener_task:
            self.game_message_listener_task.cancel()

        while self.input_requests > 0:
            self.input_queue.put_nowait(None)
            self.input_requests -= 1
        self.keep_alive_task.cancel()
        if self.ui_task:
            await self.ui_task
        if self.input_task:
            self.input_task.cancel()

    async def server_auth(self, password_requested: bool = False) -> None:
        if password_requested and not self.password:
            await super().server_auth(password_requested)
        await self.get_username()
        await self.send_connect(game=self.game)

async def main(args: Namespace):
    ctx = GoalSawContext(args.connect, args.password)
    ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()
    
    await ctx.exit_event.wait()
    await ctx.shutdown()

def launch(*args: str) -> None:
    from .Launch import launch_GoalSaw_client

    launch_GoalSaw_client(*args)


if __name__ == "__main__":
    launch(*sys.argv[1:])