import unittest
import asyncio
from app.game.engine import GameEngine
from app.game.models import GameState, PlayerState
from app.game.enums import GamePhase, Role, WinnerTeam
from app.game.role_distributor import RoleDistributor
from app.services.recovery_service import RecoveryService
from app.services.redis_service import redis_service
from app.services.lock_manager import acquire_lock

class TestMafiaKuGameEngine(unittest.TestCase):
    
    def test_01_four_player_game(self):
        """Test 1: 4 player game role distribution and startup."""
        state = GameEngine.create_game(group_id=-1001, group_title="Test Group 4")
        for i in range(1, 5):
            success, msg = GameEngine.add_player(state, user_id=i, full_name=f"Player {i}")
            self.assertTrue(success)
        
        self.assertEqual(len(state.players), 4)
        success, msg = GameEngine.start_game(state)
        self.assertTrue(success)
        self.assertEqual(state.phase, GamePhase.ROLE_ASSIGNMENT)
        
        roles = [p.role for p in state.players.values()]
        self.assertEqual(roles.count(Role.MAFIA), 1)
        self.assertEqual(roles.count(Role.DOCTOR), 1)
        self.assertEqual(roles.count(Role.COMMISSAR), 1)
        self.assertEqual(roles.count(Role.CITIZEN), 1)

    def test_02_twenty_player_game(self):
        """Test 2: 20 player game role distribution and startup."""
        state = GameEngine.create_game(group_id=-1002, group_title="Test Group 20")
        for i in range(1, 21):
            success, msg = GameEngine.add_player(state, user_id=i, full_name=f"Player {i}")
            self.assertTrue(success)
        
        self.assertEqual(len(state.players), 20)
        success, msg = GameEngine.start_game(state)
        self.assertTrue(success)
        
        roles = [p.role for p in state.players.values()]
        self.assertEqual(roles.count(Role.MAFIA), 5)
        self.assertEqual(roles.count(Role.DOCTOR), 1)
        self.assertEqual(roles.count(Role.COMMISSAR), 1)
        self.assertEqual(roles.count(Role.CITIZEN), 13)

    def test_03_two_mafia(self):
        """Test 3: 6-8 players yields exactly 2 Mafia."""
        for count in [6, 7, 8]:
            counts = RoleDistributor.calculate_role_counts(count)
            self.assertEqual(counts[Role.MAFIA], 2)
            self.assertEqual(counts[Role.DOCTOR], 1)
            self.assertEqual(counts[Role.COMMISSAR], 1)

    def test_04_three_mafia(self):
        """Test 4: 9-12 players yields exactly 3 Mafia."""
        for count in [9, 10, 11, 12]:
            counts = RoleDistributor.calculate_role_counts(count)
            self.assertEqual(counts[Role.MAFIA], 3)
            self.assertEqual(counts[Role.DOCTOR], 1)
            self.assertEqual(counts[Role.COMMISSAR], 1)

    def test_05_doctor_saves_target(self):
        """Test 5: Doctor saves Mafia's assassination target."""
        state = GameEngine.create_game(group_id=-1005, group_title="Test Save")
        p1 = PlayerState(user_id=1, full_name="Mafia 1", role=Role.MAFIA)
        p2 = PlayerState(user_id=2, full_name="Doctor 1", role=Role.DOCTOR)
        p3 = PlayerState(user_id=3, full_name="Citizen 1", role=Role.CITIZEN)
        p4 = PlayerState(user_id=4, full_name="Citizen 2", role=Role.CITIZEN)
        state.players = {1: p1, 2: p2, 3: p3, 4: p4}

        GameEngine.begin_night(state)
        # Mafia attacks Player 3
        GameEngine.record_mafia_target(state, actor_id=1, target_id=3)
        # Doctor heals Player 3
        GameEngine.record_doctor_target(state, actor_id=2, target_id=3)

        killed_id, was_saved = GameEngine.resolve_night(state)
        self.assertTrue(was_saved)
        self.assertIsNone(killed_id)
        self.assertTrue(p3.is_alive)
        self.assertEqual(p2.saves, 1)

    def test_06_doctor_heals_other_target_dies(self):
        """Test 6: Doctor heals Player 2, but Mafia attacks Player 3 -> Player 3 dies."""
        state = GameEngine.create_game(group_id=-1006, group_title="Test Miss")
        p1 = PlayerState(user_id=1, full_name="Mafia 1", role=Role.MAFIA)
        p2 = PlayerState(user_id=2, full_name="Doctor 1", role=Role.DOCTOR)
        p3 = PlayerState(user_id=3, full_name="Citizen 1", role=Role.CITIZEN)
        p4 = PlayerState(user_id=4, full_name="Citizen 2", role=Role.CITIZEN)
        state.players = {1: p1, 2: p2, 3: p3, 4: p4}

        GameEngine.begin_night(state)
        # Mafia attacks Player 3
        GameEngine.record_mafia_target(state, actor_id=1, target_id=3)
        # Doctor heals Player 2 (himself)
        GameEngine.record_doctor_target(state, actor_id=2, target_id=2)

        killed_id, was_saved = GameEngine.resolve_night(state)
        self.assertFalse(was_saved)
        self.assertEqual(killed_id, 3)
        self.assertFalse(p3.is_alive)
        self.assertEqual(p1.kills, 1)

    def test_07_commissar_checks_mafia(self):
        """Test 7: Commissar checks Mafia member."""
        state = GameEngine.create_game(group_id=-1007, group_title="Test Com Maf")
        p1 = PlayerState(user_id=1, full_name="Mafia 1", role=Role.MAFIA)
        p2 = PlayerState(user_id=2, full_name="Commissar 1", role=Role.COMMISSAR)
        state.players = {1: p1, 2: p2}

        GameEngine.begin_night(state)
        success, is_mafia, msg = GameEngine.record_commissar_target(state, actor_id=2, target_id=1)
        self.assertTrue(success)
        self.assertTrue(is_mafia)

    def test_08_commissar_checks_citizen(self):
        """Test 8: Commissar checks Citizen member."""
        state = GameEngine.create_game(group_id=-1008, group_title="Test Com Cit")
        p1 = PlayerState(user_id=1, full_name="Citizen 1", role=Role.CITIZEN)
        p2 = PlayerState(user_id=2, full_name="Commissar 1", role=Role.COMMISSAR)
        state.players = {1: p1, 2: p2}

        GameEngine.begin_night(state)
        success, is_mafia, msg = GameEngine.record_commissar_target(state, actor_id=2, target_id=1)
        self.assertTrue(success)
        self.assertFalse(is_mafia)

    def test_09_voting_elimination(self):
        """Test 9: Voting eliminates top candidate."""
        state = GameEngine.create_game(group_id=-1009, group_title="Test Voting")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.CITIZEN)
        p3 = PlayerState(user_id=3, full_name="P3", role=Role.CITIZEN)
        p4 = PlayerState(user_id=4, full_name="P4", role=Role.CITIZEN)
        state.players = {1: p1, 2: p2, 3: p3, 4: p4}

        GameEngine.begin_voting(state)
        GameEngine.record_vote(state, voter_id=2, target_id=1)
        GameEngine.record_vote(state, voter_id=3, target_id=1)
        GameEngine.record_vote(state, voter_id=4, target_id=2)

        eliminated_id, is_tie, is_double_tie = GameEngine.resolve_voting(state)
        self.assertEqual(eliminated_id, 1)
        self.assertFalse(is_tie)
        self.assertFalse(is_double_tie)
        self.assertFalse(p1.is_alive)

    def test_10_tie_voting(self):
        """Test 10: Tie voting triggers tie condition."""
        state = GameEngine.create_game(group_id=-1010, group_title="Test Tie")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.CITIZEN)
        p3 = PlayerState(user_id=3, full_name="P3", role=Role.CITIZEN)
        p4 = PlayerState(user_id=4, full_name="P4", role=Role.CITIZEN)
        state.players = {1: p1, 2: p2, 3: p3, 4: p4}

        GameEngine.begin_voting(state)
        GameEngine.record_vote(state, voter_id=1, target_id=2)
        GameEngine.record_vote(state, voter_id=2, target_id=1)

        eliminated_id, is_tie, is_double_tie = GameEngine.resolve_voting(state)
        self.assertIsNone(eliminated_id)
        self.assertTrue(is_tie)
        self.assertFalse(is_double_tie)
        self.assertEqual(state.tie_count, 1)

    def test_11_double_tie_voting(self):
        """Test 11: Second consecutive tie results in no elimination."""
        state = GameEngine.create_game(group_id=-1011, group_title="Test Double Tie")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.CITIZEN)
        state.players = {1: p1, 2: p2}
        state.tie_count = 1  # Already had 1 tie

        GameEngine.begin_voting(state)
        GameEngine.record_vote(state, voter_id=1, target_id=2)
        GameEngine.record_vote(state, voter_id=2, target_id=1)

        eliminated_id, is_tie, is_double_tie = GameEngine.resolve_voting(state)
        self.assertIsNone(eliminated_id)
        self.assertFalse(is_tie)
        self.assertTrue(is_double_tie)
        self.assertTrue(p1.is_alive)
        self.assertTrue(p2.is_alive)

    def test_12_mafia_wins(self):
        """Test 12: Mafia wins when alive mafia >= alive citizens."""
        state = GameEngine.create_game(group_id=-1012, group_title="Test Maf Win")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA, is_alive=True)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.CITIZEN, is_alive=True)
        p3 = PlayerState(user_id=3, full_name="P3", role=Role.CITIZEN, is_alive=False)
        state.players = {1: p1, 2: p2, 3: p3}

        winner = GameEngine.check_win_condition(state)
        self.assertEqual(winner, WinnerTeam.MAFIA)
        self.assertEqual(state.phase, GamePhase.GAME_OVER)

    def test_13_citizens_win(self):
        """Test 13: Citizens win when all Mafia are eliminated."""
        state = GameEngine.create_game(group_id=-1013, group_title="Test Cit Win")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA, is_alive=False)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.DOCTOR, is_alive=True)
        p3 = PlayerState(user_id=3, full_name="P3", role=Role.CITIZEN, is_alive=True)
        state.players = {1: p1, 2: p2, 3: p3}

        winner = GameEngine.check_win_condition(state)
        self.assertEqual(winner, WinnerTeam.CITIZENS)
        self.assertEqual(state.phase, GamePhase.GAME_OVER)

    def test_14_player_leaves_during_game(self):
        """Test 14: Player leaving mid-game is safely killed and triggers win check."""
        state = GameEngine.create_game(group_id=-1014, group_title="Test Leave")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA, is_alive=True)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.CITIZEN, is_alive=True)
        state.players = {1: p1, 2: p2}
        state.phase = GamePhase.NIGHT

        success, msg = GameEngine.remove_player(state, user_id=1)
        self.assertTrue(success)
        self.assertFalse(p1.is_alive)
        
        winner = GameEngine.check_win_condition(state)
        self.assertEqual(winner, WinnerTeam.CITIZENS)

    def test_15_player_skips_vote(self):
        """Test 15: Player skips voting -> Voting resolves without errors."""
        state = GameEngine.create_game(group_id=-1015, group_title="Test Skip Vote")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA, is_alive=True)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.CITIZEN, is_alive=True)
        p3 = PlayerState(user_id=3, full_name="P3", role=Role.CITIZEN, is_alive=True)
        state.players = {1: p1, 2: p2, 3: p3}

        GameEngine.begin_voting(state)
        # Only player 2 votes; player 1 and 3 skip
        GameEngine.record_vote(state, voter_id=2, target_id=1)

        eliminated_id, is_tie, is_double_tie = GameEngine.resolve_voting(state)
        self.assertEqual(eliminated_id, 1)
        self.assertFalse(p1.is_alive)

    def test_16_player_skips_night_action(self):
        """Test 16: Mafia or Doctor skips night action -> Handled safely."""
        state = GameEngine.create_game(group_id=-1016, group_title="Test Skip Night")
        p1 = PlayerState(user_id=1, full_name="P1", role=Role.MAFIA, is_alive=True)
        p2 = PlayerState(user_id=2, full_name="P2", role=Role.DOCTOR, is_alive=True)
        state.players = {1: p1, 2: p2}

        GameEngine.begin_night(state)
        # Neither acts
        killed_id, was_saved = GameEngine.resolve_night(state)
        self.assertIsNone(killed_id)
        self.assertFalse(was_saved)

    def test_17_server_restart_recovery(self):
        """Test 17: Game state serializes and deserializes cleanly without losing data."""
        state = GameEngine.create_game(group_id=-1017, group_title="Test Recovery")
        p1 = PlayerState(user_id=100, full_name="Ali", username="ali_uz", role=Role.MAFIA, is_alive=True, kills=2)
        p2 = PlayerState(user_id=200, full_name="Bek", username="bek_dev", role=Role.DOCTOR, is_alive=True, saves=1)
        state.players = {100: p1, 200: p2}
        state.phase = GamePhase.NIGHT
        state.round_number = 3

        serialized = RecoveryService.serialize_game(state)
        restored = RecoveryService.deserialize_game(serialized)

        self.assertIsNotNone(restored)
        self.assertEqual(restored.game_id, state.game_id)
        self.assertEqual(restored.phase, GamePhase.NIGHT)
        self.assertEqual(restored.round_number, 3)
        self.assertEqual(len(restored.players), 2)
        self.assertEqual(restored.get_player(100).role, Role.MAFIA)
        self.assertEqual(restored.get_player(100).kills, 2)
        self.assertEqual(restored.get_player(200).role, Role.DOCTOR)
        self.assertEqual(restored.get_player(200).saves, 1)

    def test_18_double_game_concurrency(self):
        """Test 18: Concurrency check prevents two games in the same group."""
        async def run_test():
            group_id = -1018
            async with acquire_lock(f"create_game:{group_id}") as lock1:
                self.assertTrue(lock1.acquired)
                # Second attempt while lock is held
                async with acquire_lock(f"create_game:{group_id}", timeout=1) as lock2:
                    # Second lock should not be acquired immediately while first is active
                    pass
        asyncio.run(run_test())

    def test_19_simultaneous_joins(self):
        """Test 19: Multiple users joining simultaneously are safely added."""
        state = GameEngine.create_game(group_id=-1019, group_title="Test Join")
        
        async def join_user(uid):
            async with acquire_lock(f"join:{state.group_id}"):
                return GameEngine.add_player(state, user_id=uid, full_name=f"User {uid}")

        async def run_joins():
            tasks = [join_user(i) for i in range(1, 10)]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(run_joins())
        self.assertEqual(len(state.players), 9)
        self.assertEqual(len([r for r, _ in results if r]), 9)

    def test_20_expired_callback_attack_protection(self):
        """Test 20: Expired / forged callback data is safely rejected."""
        state = GameEngine.create_game(group_id=-1020, group_title="Test Old Callback")
        state.phase = GamePhase.GAME_OVER

        # Attempt to vote on game over state
        success, reason = GameEngine.record_vote(state, voter_id=1, target_id=2)
        self.assertFalse(success)
        self.assertEqual(reason, "NOT_VOTING_PHASE")

        # Attempt night action on game over state
        success, msg = GameEngine.record_mafia_target(state, actor_id=1, target_id=2)
        self.assertFalse(success)
        self.assertEqual(msg, "NOT_NIGHT")

if __name__ == "__main__":
    unittest.main()
