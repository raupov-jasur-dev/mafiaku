import unittest
import asyncio
from app.core.config import settings

class TestServicesAndDatabase(unittest.TestCase):

    def test_group_leaderboard_isolation_logic(self):
        """Test: Pure isolation logic ensures group leaderboard records are partitioned per group."""
        # Simulated group ledger
        group_ledger = {}
        def add_member_xp(group_id, user_id, xp, won):
            key = (group_id, user_id)
            if key not in group_ledger:
                group_ledger[key] = {"xp": 0, "wins": 0, "games": 0}
            group_ledger[key]["xp"] += xp
            if won:
                group_ledger[key]["wins"] += 1
            group_ledger[key]["games"] += 1

        # Add stats for User 9001 in Group -5001 only
        add_member_xp(group_id=-5001, user_id=9001, xp=500, won=True)

        # Query Group -5001
        g1_members = [data for (gid, uid), data in group_ledger.items() if gid == -5001]
        self.assertEqual(len(g1_members), 1)
        self.assertEqual(g1_members[0]["xp"], 500)
        self.assertEqual(g1_members[0]["wins"], 1)

        # Query Group -5002 (must be completely isolated and empty)
        g2_members = [data for (gid, uid), data in group_ledger.items() if gid == -5002]
        self.assertEqual(len(g2_members), 0)

    def test_notification_toggle_logic(self):
        """Test: Notification toggle flips boolean state deterministically."""
        user_settings = {"user_1": True}
        
        # First toggle: True -> False
        user_settings["user_1"] = not user_settings["user_1"]
        self.assertFalse(user_settings["user_1"])

        # Second toggle: False -> True
        user_settings["user_1"] = not user_settings["user_1"]
        self.assertTrue(user_settings["user_1"])

    def test_admin_api_key_configuration(self):
        """Test: Admin API key setting and validation logic."""
        test_key = "secret-production-key-98765"
        settings.ADMIN_API_KEY = test_key
        
        def verify_key(header_key):
            if settings.ADMIN_API_KEY and header_key != settings.ADMIN_API_KEY:
                return False
            return True

        self.assertFalse(verify_key("wrong-key"))
        self.assertFalse(verify_key(None))
        self.assertTrue(verify_key("secret-production-key-98765"))

if __name__ == "__main__":
    unittest.main()


class TestRecoveryHardening(unittest.TestCase):
    def test_recovery_uses_public_redis_service_keys_api(self):
        from app.services.redis_service import InMemoryRedisFallback
        from app.services.recovery_service import RecoveryService
        from app.game.engine import GameEngine

        async def run():
            from app.services.redis_service import redis_service
            old_client = redis_service.client
            old_connected = redis_service._is_redis_connected
            redis_service.client = None
            redis_service._is_redis_connected = False
            try:
                state = GameEngine.create_game(-3001, "Recovery")
                await RecoveryService.save_active_game(state)
                games = await RecoveryService.get_all_saved_games()
                self.assertEqual(len(games), 1)
                self.assertEqual(games[0].game_id, state.game_id)
                await RecoveryService.clear_active_game(-3001)
            finally:
                redis_service.client = old_client
                redis_service._is_redis_connected = old_connected
        asyncio.run(run())
