"""
Core language translations: Uzbek (uz), Russian (ru), English (en).
"""
from typing import Dict

LOCALES_CORE: Dict[str, Dict[str, str]] = {
    "uz": {
        "welcome_title": "🤵🏻 *Mafia Ku* — Haqiqiy Telegram multiplayer Mafia boti!\n\nShaharni xavf-xatarlardan himoya qiling yoki tunda yashirincha boshqaring.",
        "btn_add_group": "➕ Guruhingizga qo'shish",
        "btn_main_group": "👑 Asosiy guruh",
        "btn_my_profile": "👤 Mening profilim",
        "btn_top_players": "🏆 Top o'yinchilar",
        "btn_settings": "⚙️ Sozlamalar",
        "btn_about_roles": "🎭 Rollar haqida",
        "btn_back": "⬅️ Orqaga",
        "btn_join_game": "🎭 Mafiyaga qo'shilish",
        
        "group_welcome": "🎭 *Mafia Ku*\n\nO'yinni boshlash uchun:\n/game",
        "bot_added_success": "✅ Bot muvaffaqiyatli guruhga qo'shildi va admin huquqlari tasdiqlandi!\n\nO'yinni boshlash uchun /game buyrug'ini yuboring.",
        "bot_needs_admin": "⚠️ Bot guruhda xabarlarni boshqarish va o'yinni to'liq olib borishi uchun *Administrator* qilinishi kerak.",
        
        "lobby_title": "🎭 *MAFIA KU*\n\nShahar tun oldidan so'nggi marta tinch...\n\n👥 O'yinchilar: {current}/{max}\n⏳ Qolgan vaqt: {time_left}\n\nO'yinga qo'shiling.",
        "player_joined_toast": "✅ Siz o'yinga qo'shildingiz.",
        "already_joined_toast": "⚠️ Siz allaqachon o'yindasiz!",
        "game_already_running": "⚠️ Ushbu guruhda allaqachon o'yin davom etmoqda!",
        "lobby_not_enough_players": "❌ O'yinchilar soni yetarli emas (kamida {min} ta kerak). O'yin bekor qilindi.",
        "game_starting": "🚀 O'yinchilar yig'ildi ({count} kishi). Rollar taqsimlanmoqda...",
        
        "role_mafia_title": "🔴 SIZ — MAFIA",
        "role_mafia_desc": "🎯 Maqsadingiz:\nTinch aholini kamaytirish va\nMafia ustunligini ta'minlash.",
        "role_mafia_team": "\n\nSiz bilan birga:\n{team}",
        "role_citizen_title": "👨‍🌾 SIZ — ODDIY AHOLI",
        "role_citizen_desc": "🎯 Maqsadingiz:\nKunduzgi muhokama va ovoz berish orqali barcha Mafiyalarni topish va yo'q qilish.",
        "role_doctor_title": "👨‍⚕️ SIZ — DOCTOR",
        "role_doctor_desc": "🎯 Maqsadingiz:\nHar tun bir kishini (yoki o'zingizni) davolash va Mafiyaning qurbonini qutqarib qolish.",
        "role_commissar_title": "🕵️ SIZ — COMMISSAR",
        "role_commissar_desc": "🎯 Maqsadingiz:\nHar tun bir o'yinchini tekshirib, uning Mafia yoki tinch aholi ekanini aniqlash.",
        
        "about_roles_text": "🎭 *Rollar haqida:*\n\n🔴 *Mafia*\nTunda yashirincha hujum qiladi.\nMaqsadi — shahardagi tinchlarni yo'q qilish.\n\n👨‍⚕️ *Doctor*\nHar tun bitta o'yinchini qutqarishi mumkin.\n\n🕵️ *Commissar*\nHar tun bitta o'yinchini tekshiradi.\n\n👨‍🌾 *Citizen (Oddiy aholi)*\nMaxsus kuchi yo'q.\nUning kuchi — kuzatish va to'g'ri ovoz berish.",
        
        "night_started_group": "🌙 Tun tushdi.\nShahar jim.\nAmmo hamma ham uxlayotgani yo'q...",
        "mafia_action_prompt": "🔴 Kimni nishonga olasiz?",
        "doctor_action_prompt": "👨‍⚕️ Bugun kimni qutqarasiz?",
        "commissar_action_prompt": "🕵️ Kimni tekshirasiz?",
        "action_recorded": "✅ Tanlovingiz qabul qilindi: {target}",
        "commissar_result_mafia": "🕵️ Natija: {target} — 🔴 *MAFIA*!",
        "commissar_result_citizen": "🕵️ Natija: {target} — 🟢 *Tinch aholi* (Mafia emas).",
        "cannot_target_teammate": "⚠️ Mafia a'zosiga hujum qila olmaysiz!",
        
        "morning_no_kill": "☀️ Tong otdi.\n\nBugun hech kim halok bo'lmadi.\nKimdir tunda o'z rejasini buzishga majbur bo'lgan...",
        "morning_killed": "☀️ Tong otdi.\n\nKecha shahar yana bir sinovdan o'tdi...\n☠️ *{player}* o'ldirildi!\n🎭 Uning roli: {role}",
        "discussion_start": "☀️ *KUN BOSHLANDI*\n\nSizlarda {minutes} daqiqa bor.\nShubhalaringizni ayting.",
        
        "voting_title": "🗳 *OVOZ BERISH*\n\nKimni shahardan chiqaramiz?\nQolgan vaqt: {seconds}s",
        "vote_private_prompt": "🗳 Shahardan chiqarmoqchi bo'lgan gumondorni tanlang:",
        "vote_recorded_toast": "✅ Ovoz berildi: {target}",
        "cannot_vote_self": "⚠️ O'zingizga ovoz bera olmaysiz!",
        "already_voted": "⚠️ Siz allaqachon ovoz bergansiz!",
        "vote_tie": "⚖️ Ovozlar teng chiqdi. Qayta ovoz berish o'tkaziladi...",
        "vote_double_tie": "🌆 Shahar qaror qabul qila olmadi.\nBugun hech kim chiqarilmadi.",
        "vote_eliminated": "☠️ *{player}* shahar qarori bilan o'yinni tark etdi.\n🎭 Uning roli: {role}",
        
        "game_over_title": "🏆 *O'YIN YAKUNLANDI*",
        "winner_citizens": "🟢 G'olib tomon: *Tinch aholi* (Barcha Mafiyalar yo'q qilindi!)",
        "winner_mafia": "🔴 G'olib tomon: *Mafia* (Shahar ustidan to'liq nazorat o'rnatildi!)",
        "game_summary_roles": "\n\n🎭 *Rollar:*\n{roles_list}",
        "game_summary_mvp": "\n⭐ *MVP:* {mvp}",
        
        "profile_title": "👤 *Profil: {name}*",
        "profile_stats": (
            "🎮 O'yinlar: {games}\n"
            "🏆 G'alabalar: {wins}\n"
            "💀 Mag'lubiyatlar: {losses}\n\n"
            "📈 Win Rate: {win_rate}%\n\n"
            "🔴 Mafia o'yinlari: {mafia_games}\n"
            "👨‍⚕️ Doctor: {doctor_games}\n"
            "🕵️ Commissar: {commissar_games}\n\n"
            "☠️ Kills: {kills}\n"
            "⭐ MVP: {mvp_count}\n\n"
            "🏅 Rank: {rank}\n"
            "✨ XP: {xp}"
        ),
        
        "settings_title": "⚙️ *Sozlamalar*",
        "btn_language": "🌐 Tilni o'zgartirish",
        "btn_notifications": "🔔 Bildirishnomalar",
        "btn_about_bot": "ℹ️ Bot haqida",
        "choose_language": "🌐 O'zingizga qulay tilni tanlang:",
        "language_changed": "✅ Til muvaffaqiyatli o'zgartirildi: {lang}",
        "notifications_toggled": "🔔 Bildirishnomalar holati: {status}",
        "about_bot_info": "🤵🏻 *Mafia Ku* (@mafiaku_gobot)\n\nVersiya: 1.0.0 (Production)\nRasmiy guruh: https://t.me/mafiaku_uz\n\nTelegram Bot API asosida eng yaxshi multiplayer o'yin tajribasi!",
        
        "group_top_title": "🏆 *Guruh bo'yicha TOP o'yinchilar* ({group_name}):\n\n{top_list}",
        "admin_panel_title": "👑 *Admin boshqaruv paneli*",
        "game_reset_success": "🔄 Joriy o'yin admin tomonidan to'xtatildi va tozalandi.",
        "only_admin_can_action": "⚠️ Bu amalni faqat guruh administratori bajara oladi.",
    },
    "ru": {
        "welcome_title": "🤵🏻 *Mafia Ku* — Настоящий Telegram мультиплеер Мафия бот!\n\nЗащищайте город от преступности или скрытно управляйте им ночью.",
        "btn_add_group": "➕ Добавить в группу",
        "btn_main_group": "👑 Официальная группа",
        "btn_my_profile": "👤 Мой профиль",
        "btn_top_players": "🏆 Топ игроков",
        "btn_settings": "⚙️ Настройки",
        "btn_about_roles": "🎭 О ролях",
        "btn_back": "⬅️ Назад",
        "btn_join_game": "🎭 Присоединиться к Мафии",
        "group_welcome": "🎭 *Mafia Ku*\n\nЧтобы начать игру:\n/game",
        "bot_added_success": "✅ Бот успешно добавлен в группу с правами администратора!\n\nОтправьте /game чтобы начать лобби.",
        "bot_needs_admin": "⚠️ Боту необходимы права Администратора в группе для полноценного проведения игры.",
        "lobby_title": "🎭 *MAFIA KU*\n\nГород спокоен перед наступлением ночи...\n\n👥 Игроки: {current}/{max}\n⏳ Осталось времени: {time_left}\n\nПрисоединяйтесь к игре.",
        "player_joined_toast": "✅ Вы присоединились к игре.",
        "already_joined_toast": "⚠️ Вы уже в игре!",
        "game_already_running": "⚠️ В этой группе уже идет игра!",
        "lobby_not_enough_players": "❌ Недостаточно игроков (минимум {min}). Игра отменена.",
        "game_starting": "🚀 Игроки собраны ({count}). Раздаем роли...",
        "role_mafia_title": "🔴 ВЫ — МАФИЯ",
        "role_mafia_desc": "🎯 Ваша цель:\nУстранить мирных жителей и захватить контроль над городом.",
        "role_mafia_team": "\n\nС вами в команде:\n{team}",
        "role_citizen_title": "👨‍🌾 ВЫ — МИРНЫЙ ЖИТЕЛЬ",
        "role_citizen_desc": "🎯 Ваша цель:\nНайти и исключить всех мафиози во время дневных обсуждений и голосований.",
        "role_doctor_title": "👨‍⚕️ ВЫ — ДОКТОР",
        "role_doctor_desc": "🎯 Ваша цель:\nКаждую ночь лечить одного игрока (или себя) и спасать от покушения.",
        "role_commissar_title": "🕵️ ВЫ — КОМИССАР",
        "role_commissar_desc": "🎯 Ваша цель:\nКаждую ночь проверять статус игрока (Мафия или Мирный).",
        "about_roles_text": "🎭 *Описание ролей:*\n\n🔴 *Мафия*\nАтакует ночью. Цель — уничтожить мирных жителей.\n\n👨‍⚕️ *Доктор*\nКаждую ночь может спасти одного игрока.\n\n🕵️ *Комиссар*\nКаждую ночь проверяет одного игрока.\n\n👨‍🌾 *Мирный житель*\nГлавная сила — логика и правильное голосование.",
        "night_started_group": "🌙 Наступила ночь.\nГород затих.\nНо не все собираются спать...",
        "mafia_action_prompt": "🔴 Кого выберете своей целью?",
        "doctor_action_prompt": "👨‍⚕️ Кого вылечите этой ночью?",
        "commissar_action_prompt": "🕵️ Кого проверите этой ночью?",
        "action_recorded": "✅ Ваш выбор принят: {target}",
        "commissar_result_mafia": "🕵️ Результат: {target} — 🔴 *МАФИЯ*!",
        "commissar_result_citizen": "🕵️ Результат: {target} — 🟢 *Мирный житель*.",
        "cannot_target_teammate": "⚠️ Вы не можете атаковать союзника по мафии!",
        "morning_no_kill": "☀️ Наступило утро.\n\nСегодня ночью никто не погиб. Доктор спас чью-то жизнь!",
        "morning_killed": "☀️ Наступило утро.\n\nГород потрясен трагедией...\n☠️ *{player}* был убит!\n🎭 Его роль: {role}",
        "discussion_start": "☀️ *ДЕНЬ НАЧАЛСЯ*\n\nУ вас {minutes} мин. Высказывайте подозрения.",
        "voting_title": "🗳 *ГОЛОСОВАНИЕ*\n\nКого исключим из города?\nОсталось: {seconds}с",
        "vote_private_prompt": "🗳 Выберите подозреваемого для голосования:",
        "vote_recorded_toast": "✅ Голос принят: {target}",
        "cannot_vote_self": "⚠️ Нельзя голосовать за себя!",
        "already_voted": "⚠️ Вы уже проголосовали!",
        "vote_tie": "⚖️ Ничья в голосовании. Проводится повторное голосование...",
        "vote_double_tie": "🌆 Город не пришел к согласию. Никто не исключен.",
        "vote_eliminated": "☠️ *{player}* исключен решением города.\n🎭 Его роль: {role}",
        "game_over_title": "🏆 *ИГРА ОКОНЧЕНА*",
        "winner_citizens": "🟢 Победа: *Мирные жители* (Все мафиози устранены!)",
        "winner_mafia": "🔴 Победа: *Мафия* (Город взят под контроль!)",
        "game_summary_roles": "\n\n🎭 *Роли игроков:*\n{roles_list}",
        "game_summary_mvp": "\n⭐ *MVP:* {mvp}",
        "profile_title": "👤 *Профиль: {name}*",
        "profile_stats": (
            "🎮 Всего игр: {games}\n"
            "🏆 Победы: {wins}\n"
            "💀 Поражения: {losses}\n\n"
            "📈 Win Rate: {win_rate}%\n\n"
            "🔴 Игр за Мафию: {mafia_games}\n"
            "👨‍⚕️ Доктор: {doctor_games}\n"
            "🕵️ Комиссар: {commissar_games}\n\n"
            "☠️ Убийства: {kills}\n"
            "⭐ MVP: {mvp_count}\n\n"
            "🏅 Ранг: {rank}\n"
            "✨ Опыт: {xp}"
        ),
        "settings_title": "⚙️ *Настройки*",
        "btn_language": "🌐 Сменить язык",
        "btn_notifications": "🔔 Уведомления",
        "btn_about_bot": "ℹ️ О боте",
        "choose_language": "🌐 Выберите предпочитаемый язык:",
        "language_changed": "✅ Язык успешно изменен: {lang}",
        "notifications_toggled": "🔔 Статус уведомлений: {status}",
        "about_bot_info": "🤵🏻 *Mafia Ku* (@mafiaku_gobot)\nВерсия: 1.0.0 (Production)\nГруппа: https://t.me/mafiaku_uz",
        "group_top_title": "🏆 *ТОП игроков группы* ({group_name}):\n\n{top_list}",
        "admin_panel_title": "👑 *Панель администратора*",
        "game_reset_success": "🔄 Игра успешно сброшена администратором.",
        "only_admin_can_action": "⚠️ Это действие доступно только администратору группы.",
    },
    "en": {
        "welcome_title": "🤵🏻 *Mafia Ku* — Real Telegram Multiplayer Mafia Game Bot!\n\nDefend your city against the crime syndicate or rule from the shadows.",
        "btn_add_group": "➕ Add to Your Group",
        "btn_main_group": "👑 Official Group",
        "btn_my_profile": "👤 My Profile",
        "btn_top_players": "🏆 Top Players",
        "btn_settings": "⚙️ Settings",
        "btn_about_roles": "🎭 About Roles",
        "btn_back": "⬅️ Back",
        "btn_join_game": "🎭 Join Mafia Game",
        "group_welcome": "🎭 *Mafia Ku*\n\nTo start a new game:\n/game",
        "bot_added_success": "✅ Bot added to group with admin permissions!\n\nSend /game to start a match.",
        "bot_needs_admin": "⚠️ The bot requires Administrator privileges in this group to manage messages and timer cycles.",
        "lobby_title": "🎭 *MAFIA KU*\n\nThe city rests quietly before nightfall...\n\n👥 Players: {current}/{max}\n⏳ Time remaining: {time_left}\n\nJoin the match below.",
        "player_joined_toast": "✅ You joined the game.",
        "already_joined_toast": "⚠️ You are already in this match!",
        "game_already_running": "⚠️ A game is already active in this group!",
        "lobby_not_enough_players": "❌ Not enough players joined (min {min} required). Lobby cancelled.",
        "game_starting": "🚀 Players gathered ({count}). Distributing secret roles...",
        "role_mafia_title": "🔴 YOU ARE — MAFIA",
        "role_mafia_desc": "🎯 Your Goal:\nEliminate the citizens and gain controlling majority.",
        "role_mafia_team": "\n\nYour mafia allies:\n{team}",
        "role_citizen_title": "👨‍🌾 YOU ARE — CITIZEN",
        "role_citizen_desc": "🎯 Your Goal:\nExpose and eliminate all Mafia members through deduction and daytime votes.",
        "role_doctor_title": "👨‍⚕️ YOU ARE — DOCTOR",
        "role_doctor_desc": "🎯 Your Goal:\nHeal one player (or yourself) each night to prevent Mafia assassinations.",
        "role_commissar_title": "🕵️ YOU ARE — COMMISSAR",
        "role_commissar_desc": "🎯 Your Goal:\nInvestigate one player each night to determine if they are Mafia or innocent.",
        "about_roles_text": "🎭 *Game Roles:*\n\n🔴 *Mafia*\nStrikes secretly at night. Goal is to overwhelm the innocents.\n\n👨‍⚕️ *Doctor*\nCan save one player from death each night.\n\n🕵️ *Commissar*\nInvestigates one suspect each night.\n\n👨‍🌾 *Citizen*\nHas no special abilities, but holds decisive voting power.",
        "night_started_group": "🌙 Night has fallen.\nThe city sleeps.\nYet shadowy figures stir in the dark...",
        "mafia_action_prompt": "🔴 Choose your assassination target:",
        "doctor_action_prompt": "👨‍⚕️ Who will you heal tonight?",
        "commissar_action_prompt": "🕵️ Who will you investigate tonight?",
        "action_recorded": "✅ Choice confirmed: {target}",
        "commissar_result_mafia": "🕵️ Investigation Result: {target} is 🔴 *MAFIA*!",
        "commissar_result_citizen": "🕵️ Investigation Result: {target} is 🟢 *Innocent Citizen*.",
        "cannot_target_teammate": "⚠️ You cannot target your fellow Mafia teammate!",
        "morning_no_kill": "☀️ Morning arrives.\n\nNobody died tonight! The Doctor's intervention was successful.",
        "morning_killed": "☀️ Morning arrives.\n\nTragedy struck in the shadows...\n☠️ *{player}* was eliminated!\n🎭 Secret Role: {role}",
        "discussion_start": "☀️ *DAY DISCUSSION*\n\nYou have {minutes} minutes to debate and analyze suspects.",
        "voting_title": "🗳 *TOWN VOTE*\n\nWho shall be cast out from the city?\nTime left: {seconds}s",
        "vote_private_prompt": "🗳 Choose a suspect to cast out from the town:",
        "vote_recorded_toast": "✅ Vote cast for {target}",
        "cannot_vote_self": "⚠️ You cannot vote for yourself!",
        "already_voted": "⚠️ You have already cast your vote!",
        "vote_tie": "⚖️ Voting resulted in a tie! Running tiebreaker round...",
        "vote_double_tie": "🌆 The town could not reach a verdict. No one is eliminated today.",
        "vote_eliminated": "☠️ *{player}* was executed by town consensus.\n🎭 Secret Role: {role}",
        "game_over_title": "🏆 *GAME OVER*",
        "winner_citizens": "🟢 Victory: *Innocent Citizens* (All Mafia members eradicated!)",
        "winner_mafia": "🔴 Victory: *Mafia* (Total syndicate dominance established!)",
        "game_summary_roles": "\n\n🎭 *Player Roles:*\n{roles_list}",
        "game_summary_mvp": "\n⭐ *MVP:* {mvp}",
        "profile_title": "👤 *Profile: {name}*",
        "profile_stats": (
            "🎮 Games Played: {games}\n"
            "🏆 Victories: {wins}\n"
            "💀 Losses: {losses}\n\n"
            "📈 Win Rate: {win_rate}%\n\n"
            "🔴 Mafia Matches: {mafia_games}\n"
            "👨‍⚕️ Doctor: {doctor_games}\n"
            "🕵️ Commissar: {commissar_games}\n\n"
            "☠️ Kills: {kills}\n"
            "⭐ MVP Awards: {mvp_count}\n\n"
            "🏅 Rank: {rank}\n"
            "✨ Experience: {xp} XP"
        ),
        "settings_title": "⚙️ *Settings*",
        "btn_language": "🌐 Change Language",
        "btn_notifications": "🔔 Notifications",
        "btn_about_bot": "ℹ️ About Bot",
        "choose_language": "🌐 Select your preferred language:",
        "language_changed": "✅ Language changed successfully: {lang}",
        "notifications_toggled": "🔔 Notifications status: {status}",
        "about_bot_info": "🤵🏻 *Mafia Ku* (@mafiaku_gobot)\nVersion: 1.0.0 (Production)\nGroup: https://t.me/mafiaku_uz",
        "group_top_title": "🏆 *Leaderboard for* {group_name}:\n\n{top_list}",
        "admin_panel_title": "👑 *Admin Control Panel*",
        "game_reset_success": "🔄 Game has been forcefully reset by group administrator.",
        "only_admin_can_action": "⚠️ Only group administrators can perform this action.",
    }
}
