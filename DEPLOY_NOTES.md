# Mafia Ku — Fixed Deployment Notes

## What was fixed

- `/game` now starts the match automatically after the minimum number of players joins, with a 5-second grace period (`AUTO_START_DELAY`) for extra players.
- Redis recovery no longer uses the nonexistent private `_client`; it uses the public Redis service API.
- Recovered games continue from their saved phase instead of blindly starting a new Night.
- Per-game lobby/night/discussion/voting durations and player limits are persisted in Redis.
- Group settings are loaded when a new game is created.
- Real Telegram group membership is checked before accepting a deep-link join.
- Ban flags are enforced by middleware and admin API actions are available.
- Night actions and votes are persisted to PostgreSQL.
- Commissar can investigate only once per Night.
- Death reasons are stored as `NIGHT_KILL`, `VOTED_OUT`, or `DISCONNECTED`.
- Final game player records are idempotent, preventing duplicate rows after recovery.
- Achievement XP rewards are granted and rank is recalculated.
- Telegram polling is supervised and retries after unexpected failures.
- The admin dashboard reads real API data instead of displaying hard-coded fake test results.
- Admin API supports user/group ban controls, group settings, active-game reset, and broadcast.

## Railway variables

Keep your existing production values and add:

```env
AUTO_START_DELAY=5
```

Do not put real secrets in `.env.example` or in source code.

## After deployment

1. Confirm `/health` returns HTTP 200.
2. Confirm Railway logs show Redis and PostgreSQL connections and Telegram polling.
3. In the Telegram group, make sure the bot is an Administrator.
4. Send `/game`.
5. Players press `Mafiyaga qo'shilish`; Telegram opens the bot's private chat.
6. Each player must be a member of the group.
7. Once the minimum is reached, the game starts after the short grace delay.
8. Roles are sent privately, then Night → Morning → Discussion → Voting runs automatically.
9. If the Railway service restarts during a game, Redis recovery resumes the saved phase.

## Verification performed in the development container

- Python compilation: passed.
- Automated tests: **29 passed**.

The Telegram API, Railway infrastructure, and your production credentials are external systems, so a local code audit cannot honestly certify those external services as 100% available. The project is prepared so the deployed service can be verified with the checklist above.
