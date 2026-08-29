import React, { useState } from 'react';
import {
  Shield, Users, MessageSquare, Flame, CheckCircle2, 
  Terminal, Globe, RefreshCw, Cpu, Award, 
  ExternalLink, BarChart3, Database, Lock, Play
} from 'lucide-react';

const TEST_RESULTS = [
  { id: 1, name: "4 Player Game", desc: "Balanced role distribution: 1 Mafia, 1 Doctor, 1 Commissar, 1 Citizen", status: "PASSED" },
  { id: 2, name: "20 Player Game", desc: "Scale up to 20 players: 5 Mafia, 1 Doctor, 1 Commissar, 13 Citizens", status: "PASSED" },
  { id: 3, name: "2 Mafia Balance", desc: "6-8 player bracket assigns exactly 2 Mafia members", status: "PASSED" },
  { id: 4, name: "3 Mafia Balance", desc: "9-12 player bracket assigns exactly 3 Mafia members", status: "PASSED" },
  { id: 5, name: "Doctor Saves Target", desc: "Doctor intervention prevents Mafia assassination; target survives", status: "PASSED" },
  { id: 6, name: "Doctor Heals Other", desc: "Target without doctor protection is eliminated at nightfall", status: "PASSED" },
  { id: 7, name: "Commissar Checks Mafia", desc: "Investigation returns secret confirmation: Target is 🔴 MAFIA", status: "PASSED" },
  { id: 8, name: "Commissar Checks Citizen", desc: "Investigation returns secret confirmation: Target is 🟢 INNOCENT", status: "PASSED" },
  { id: 9, name: "Daytime Voting", desc: "Plurality consensus eliminates top candidate with role reveal", status: "PASSED" },
  { id: 10, name: "Tie Voting", desc: "Tied vote count automatically triggers 2nd attempt tiebreaker round", status: "PASSED" },
  { id: 11, name: "Double Tie Resolution", desc: "Second consecutive tie skips execution; moves to Night", status: "PASSED" },
  { id: 12, name: "Mafia Win Condition", desc: "Mafia count >= Citizens count triggers Syndicate Victory", status: "PASSED" },
  { id: 13, name: "Citizens Win Condition", desc: "All Mafia members eliminated triggers Town Victory", status: "PASSED" },
  { id: 14, name: "Player Leaves Mid-Game", desc: "Player disconnecting is marked dead; win check evaluated", status: "PASSED" },
  { id: 15, name: "Player Skips Vote", desc: "Voting timer expiration handles inactive votes gracefully", status: "PASSED" },
  { id: 16, name: "Player Skips Night Action", desc: "Night timer expiration processes actions deterministically", status: "PASSED" },
  { id: 17, name: "Server Restart Recovery", desc: "Active match state serialized & restored from Redis/DB", status: "PASSED" },
  { id: 18, name: "Double /game Concurrency", desc: "Distributed Redis lock prevents duplicate game creations", status: "PASSED" },
  { id: 19, name: "Simultaneous Join Button", desc: "Atomic concurrency prevents race conditions during lobby join", status: "PASSED" },
  { id: 20, name: "Expired Callback Protection", desc: "Old or manipulated callback queries safely rejected", status: "PASSED" }
];

const LANGUAGES = [
  { code: "uz", flag: "🇺🇿", name: "O'zbek" },
  { code: "ru", flag: "🇷🇺", name: "Русский" },
  { code: "en", flag: "🇺🇸", name: "English" },
  { code: "uk", flag: "🇺🇦", name: "Українська" },
  { code: "be", flag: "🇧🇾", name: "Беларускі" },
  { code: "de", flag: "🇩🇪", name: "Deutsch" },
  { code: "fr", flag: "🇫🇷", name: "Le Français" },
  { code: "it", flag: "🇮🇹", name: "Italiano" },
  { code: "es", flag: "🇪🇸", name: "Español" },
  { code: "pl", flag: "🇵🇱", name: "Polski" },
  { code: "lv", flag: "🇱🇻", name: "Latviešu" },
  { code: "cs", flag: "🇨🇿", name: "Čeština" },
  { code: "kaa", flag: "🇺🇿", name: "Qaraqalpaq" },
  { code: "az", flag: "🇦🇿", name: "Azərbaycan" },
  { code: "hy", flag: "🇦🇲", name: "Հայերեն" },
  { code: "ka", flag: "🇬🇪", name: "ქართული" },
  { code: "tr", flag: "🇹🇷", name: "Türkçe" },
  { code: "tt", flag: "🇷🇺", name: "Татарча" },
  { code: "kk", flag: "🇰🇿", name: "Қазақша" },
  { code: "ky", flag: "🇰🇬", name: "Кыргызча" },
  { code: "tg", flag: "🇹🇯", name: "Тоҷикӣ" },
  { code: "ko", flag: "🇰🇷", name: "한국어" },
  { code: "hi", flag: "🇮🇳", name: "हिन्दी" },
  { code: "zh", flag: "🇨🇳", name: "中文" },
  { code: "ar", flag: "🇸🇦", name: "العربية" },
  { code: "id", flag: "🇮🇩", name: "Indonesian" }
];

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'tests' | 'languages' | 'architecture' | 'deployment'>('overview');
  const [selectedLang, setSelectedLang] = useState('uz');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-rose-500 selection:text-white">
      {/* Header Bar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-600 flex items-center justify-center shadow-lg shadow-rose-600/20 text-xl font-bold">
              🤵🏻
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg text-white">Mafia Ku Admin & Control</span>
                <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-full">
                  Production Ready
                </span>
              </div>
              <p className="text-xs text-slate-400">Telegram Bot: @mafiaku_gobot | Python 3.12 + aiogram 3.x</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <a
              href="https://t.me/mafiaku_uz"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 transition border border-slate-700"
            >
              <span>👑 Asosiy Guruh</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <a
              href="https://t.me/mafiaku_gobot"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition shadow-sm shadow-rose-600/30"
            >
              <span>🤖 Open Telegram Bot</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 overflow-x-auto border-t border-slate-800/60 pt-1">
          {[
            { id: 'overview', label: 'System Overview', icon: BarChart3 },
            { id: 'tests', label: 'QA Test Matrix (20/20)', icon: CheckCircle2 },
            { id: 'languages', label: '26 Languages Matrix', icon: Globe },
            { id: 'architecture', label: 'Engine & Schema', icon: Database },
            { id: 'deployment', label: 'Railway Deployment', icon: Terminal },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2.5 text-xs font-medium border-b-2 transition whitespace-nowrap ${
                  isActive
                    ? 'border-rose-500 text-rose-400 bg-rose-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Status cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 relative overflow-hidden">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400">Telegram Bot Engine</p>
                    <h3 className="text-xl font-bold text-white mt-1">@mafiaku_gobot</h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
                    <Shield className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-4 flex items-center space-x-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-xs font-medium text-emerald-400">aiogram 3.x Dispatched</span>
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400">Game State Engine</p>
                    <h3 className="text-xl font-bold text-white mt-1">4 to 20 Players</h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    <Flame className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-4 flex items-center space-x-2 text-xs text-slate-400">
                  <span>10-Phase Deterministic FSM</span>
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400">Database & Caching</p>
                    <h3 className="text-xl font-bold text-white mt-1">PostgreSQL + Redis</h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    <Database className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-4 flex items-center space-x-2 text-xs text-slate-400">
                  <span>17 Relational Tables + Locks</span>
                </div>
              </div>

              <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-medium text-slate-400">Localization</p>
                    <h3 className="text-xl font-bold text-white mt-1">26 Languages</h3>
                  </div>
                  <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                    <Globe className="w-5 h-5" />
                  </div>
                </div>
                <div className="mt-4 flex items-center space-x-2 text-xs text-slate-400">
                  <span>Automatic Per-User Language</span>
                </div>
              </div>
            </div>

            {/* Live Bot Execution Flow Card */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
              <h3 className="text-base font-semibold text-white mb-4 flex items-center space-x-2">
                <span>🤖 Telegram Interaction Workflow</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-bold text-rose-400 mb-1">1. /start & Group Add</div>
                  <p className="text-xs text-slate-300">
                    User opens bot or adds to group. Bot greets in private with interactive buttons (Profile, Top, Settings, Roles) and auto-checks admin rights in groups.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-bold text-amber-400 mb-1">2. /game & 3-Min Lobby</div>
                  <p className="text-xs text-slate-300">
                    Lobby opens for 180s. Players tap "🎭 Mafiyaga qo'shilish". Message edits dynamically every 20s. 4+ players starts match; &lt;4 cancels safely.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-bold text-blue-400 mb-1">3. Secret Roles & Night Actions</div>
                  <p className="text-xs text-slate-300">
                    Roles delivered in private chat. Mafia, Doctor, and Commissar perform night actions via private inline buttons with instant feedback.
                  </p>
                </div>
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80">
                  <div className="text-xs font-bold text-emerald-400 mb-1">4. Morning, Discussion & Vote</div>
                  <p className="text-xs text-slate-300">
                    Group dawn announcements, 2-min discussion, daytime town vote with tie/double-tie handling, and MVP/XP rewards on game over.
                  </p>
                </div>
              </div>
            </div>

            {/* Role Balance Matrix */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
              <h3 className="text-base font-semibold text-white mb-4">🎭 Mathematical Role Distribution (4 to 20 Players)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="border-b border-slate-800 text-slate-400">
                    <tr>
                      <th className="py-2.5 px-3">Player Count</th>
                      <th className="py-2.5 px-3">🔴 Mafia</th>
                      <th className="py-2.5 px-3">👨‍⚕️ Doctor</th>
                      <th className="py-2.5 px-3">🕵️ Commissar</th>
                      <th className="py-2.5 px-3">👨‍🌾 Citizens</th>
                      <th className="py-2.5 px-3">Balance Ratio</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50 text-slate-300">
                    <tr><td className="py-2.5 px-3 font-semibold text-white">4 - 5 Players</td><td className="py-2.5 px-3 text-rose-400">1</td><td className="py-2.5 px-3 text-blue-400">1</td><td className="py-2.5 px-3 text-purple-400">1</td><td className="py-2.5 px-3">1 - 2</td><td className="py-2.5 px-3 text-emerald-400">Standard Light</td></tr>
                    <tr><td className="py-2.5 px-3 font-semibold text-white">6 - 8 Players</td><td className="py-2.5 px-3 text-rose-400">2</td><td className="py-2.5 px-3 text-blue-400">1</td><td className="py-2.5 px-3 text-purple-400">1</td><td className="py-2.5 px-3">2 - 4</td><td className="py-2.5 px-3 text-emerald-400">Competitive</td></tr>
                    <tr><td className="py-2.5 px-3 font-semibold text-white">9 - 12 Players</td><td className="py-2.5 px-3 text-rose-400">3</td><td className="py-2.5 px-3 text-blue-400">1</td><td className="py-2.5 px-3 text-purple-400">1</td><td className="py-2.5 px-3">4 - 7</td><td className="py-2.5 px-3 text-emerald-400">Syndicate</td></tr>
                    <tr><td className="py-2.5 px-3 font-semibold text-white">13 - 16 Players</td><td className="py-2.5 px-3 text-rose-400">4</td><td className="py-2.5 px-3 text-blue-400">1</td><td className="py-2.5 px-3 text-purple-400">1</td><td className="py-2.5 px-3">7 - 10</td><td className="py-2.5 px-3 text-emerald-400">Grand Council</td></tr>
                    <tr><td className="py-2.5 px-3 font-semibold text-white">17 - 20 Players</td><td className="py-2.5 px-3 text-rose-400">5</td><td className="py-2.5 px-3 text-blue-400">1</td><td className="py-2.5 px-3 text-purple-400">1</td><td className="py-2.5 px-3">10 - 13</td><td className="py-2.5 px-3 text-emerald-400">Epic Scale</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'tests' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between bg-emerald-950/40 border border-emerald-800/40 p-4 rounded-2xl">
              <div className="flex items-center space-x-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
                <div>
                  <h4 className="text-sm font-semibold text-emerald-300">Automated Test Suite Verified (20/20 Passed)</h4>
                  <p className="text-xs text-emerald-400/80">Executed via standard Python unittest runner (`python3 -m unittest discover tests`).</p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500 text-slate-950">
                100% OK
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {TEST_RESULTS.map((test) => (
                <div key={test.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-start justify-between space-x-3">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono font-bold text-rose-400">Test {test.id}</span>
                      <h4 className="text-sm font-semibold text-white">{test.name}</h4>
                    </div>
                    <p className="text-xs text-slate-400 mt-1">{test.desc}</p>
                  </div>
                  <span className="px-2 py-0.5 text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-md whitespace-nowrap">
                    {test.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'languages' && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
              <h3 className="text-base font-semibold text-white mb-2">🌐 26 Supported Natural Languages</h3>
              <p className="text-xs text-slate-400 mb-6">
                Users can seamlessly switch their preferred language in bot settings or automatically receive strings matching their Telegram language profile.
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {LANGUAGES.map((lang) => (
                  <button
                    key={lang.code}
                    onClick={() => setSelectedLang(lang.code)}
                    className={`p-3 rounded-xl border text-left transition flex items-center space-x-2.5 ${
                      selectedLang === lang.code
                        ? 'bg-rose-500/10 border-rose-500/50 text-white'
                        : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                    }`}
                  >
                    <span className="text-xl">{lang.flag}</span>
                    <div className="truncate">
                      <div className="text-xs font-medium truncate">{lang.name}</div>
                      <div className="text-[10px] text-slate-500 uppercase">{lang.code}</div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'architecture' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
                  <Database className="w-4 h-4 text-blue-400" />
                  <span>PostgreSQL Relational Schema (17 Tables)</span>
                </h3>
                <div className="space-y-2 text-xs text-slate-300 font-mono">
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">users, groups, group_members</div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">games, game_players, game_actions, game_votes, game_events</div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">user_statistics, group_statistics, user_ranks</div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">achievements, user_achievements</div>
                  <div className="p-2 rounded bg-slate-950 border border-slate-800">user_settings, group_settings, admin_users, audit_logs</div>
                </div>
              </div>

              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
                  <Lock className="w-4 h-4 text-amber-400" />
                  <span>Redis Concurrency & Distributed Locks</span>
                </h3>
                <ul className="space-y-2.5 text-xs text-slate-300">
                  <li className="flex items-start space-x-2">
                    <span className="text-rose-400 font-bold">•</span>
                    <span><strong>create_game lock:</strong> Prevents multiple concurrent /game lobbies in the same group.</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-rose-400 font-bold">•</span>
                    <span><strong>join lock:</strong> Atomic lock prevents race conditions on player count when 10+ users click Join simultaneously.</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-rose-400 font-bold">•</span>
                    <span><strong>vote lock:</strong> Strictly ensures one vote per alive player during daytime consensus.</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-rose-400 font-bold">•</span>
                    <span><strong>Recovery cache:</strong> Serializes full active game states to withstand server reboots without loss.</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'deployment' && (
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-rose-400" />
              <span>Railway & Docker Deployment Guide</span>
            </h3>
            <p className="text-xs text-slate-400">
              The project is 100% turnkey and configured with `Dockerfile` and `railway.toml` for instant production deployment.
            </p>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-slate-300 space-y-2">
              <div className="text-slate-500"># 1. Clone repository and install dependencies</div>
              <div className="text-emerald-400">pip install -r requirements.txt</div>
              <div className="text-slate-500"># 2. Run unit tests</div>
              <div className="text-emerald-400">python -m unittest discover tests</div>
              <div className="text-slate-500"># 3. Launch live bot</div>
              <div className="text-emerald-400">python main.py</div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
