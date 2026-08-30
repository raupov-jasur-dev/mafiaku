import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { Activity, Bot, Gamepad2, RefreshCw, ShieldCheck, Users, XCircle } from 'lucide-react';

type Stats = { total_users: number; total_groups: number; total_games: number; active_games: number; citizens_wins: number; mafia_wins: number };
type UserRow = { id: number; first_name: string; last_name?: string; username?: string; language: string; is_banned: boolean; games_played: number; wins: number; xp: number; rank: string };
type GroupRow = { id: number; title: string; username?: string; is_active: boolean; is_banned: boolean; bot_is_admin: boolean };
type GameRow = { game_id: string; group_id: number; group_title: string; phase: string; players_count: number; alive_count: number; round_number: number; deadline: number };

const API_KEY_STORAGE = 'mafiaku_admin_key';

export default function App() {
  const [apiKey, setApiKey] = useState(() => sessionStorage.getItem(API_KEY_STORAGE) || '');
  const [keyInput, setKeyInput] = useState(apiKey);
  const [tab, setTab] = useState<'overview' | 'users' | 'groups' | 'games'>('overview');
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [groups, setGroups] = useState<GroupRow[]>([]);
  const [games, setGames] = useState<GameRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const headers = useMemo(() => ({ 'X-Admin-Key': apiKey }), [apiKey]);

  const request = useCallback(async (path: string, options: RequestInit = {}) => {
    const response = await fetch(path, { ...options, headers: { ...headers, ...(options.headers || {}) } });
    if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
    return response.json();
  }, [headers]);

  const load = useCallback(async () => {
    if (!apiKey) return;
    setLoading(true); setError('');
    try {
      const [s, u, g, a] = await Promise.all([
        request('/api/stats'), request('/api/users?limit=100'), request('/api/groups?limit=100'), request('/api/active-games'),
      ]);
      setStats(s); setUsers(u); setGroups(g); setGames(a);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'API error');
    } finally { setLoading(false); }
  }, [apiKey, request]);

  useEffect(() => { load(); }, [load]);

  const login = () => {
    sessionStorage.setItem(API_KEY_STORAGE, keyInput.trim());
    setApiKey(keyInput.trim());
  };
  const logout = () => { sessionStorage.removeItem(API_KEY_STORAGE); setApiKey(''); setStats(null); };

  const action = async (path: string, method = 'POST') => {
    try { await request(path, { method }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Action failed'); }
  };

  if (!apiKey) return (
    <main className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-7 shadow-2xl">
        <div className="flex items-center gap-3 mb-6"><Bot className="w-9 h-9"/><div><h1 className="text-2xl font-bold">Mafia Ku Admin</h1><p className="text-slate-400 text-sm">Real-time backend dashboard</p></div></div>
        <label className="text-sm text-slate-300">ADMIN_API_KEY</label>
        <input value={keyInput} onChange={e => setKeyInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && login()} type="password" className="mt-2 w-full rounded-xl bg-slate-800 border border-slate-700 px-4 py-3 outline-none" placeholder="Railway variable qiymatini kiriting" />
        <button onClick={login} className="mt-4 w-full rounded-xl bg-white text-slate-950 py-3 font-semibold hover:bg-slate-200">Kirish</button>
      </section>
    </main>
  );

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/90 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3"><Bot/><div><h1 className="font-bold text-lg">Mafia Ku</h1><p className="text-xs text-slate-400">Production Admin Center</p></div></div>
          <div className="flex gap-2"><button onClick={load} className="px-3 py-2 rounded-lg border border-slate-700 hover:bg-slate-900"><RefreshCw className={loading ? 'animate-spin' : ''} size={17}/></button><button onClick={logout} className="px-3 py-2 rounded-lg border border-slate-700 text-sm">Chiqish</button></div>
        </div>
      </header>
      <div className="max-w-7xl mx-auto p-5">
        {error && <div className="mb-5 rounded-xl border border-red-900 bg-red-950/40 p-4 text-red-200">{error}</div>}
        <nav className="flex flex-wrap gap-2 mb-6">
          {(['overview','users','groups','games'] as const).map(t => <button key={t} onClick={() => setTab(t)} className={`px-4 py-2 rounded-lg text-sm ${tab === t ? 'bg-white text-slate-950' : 'bg-slate-900 border border-slate-800 text-slate-300'}`}>{t === 'overview' ? 'Overview' : t[0].toUpperCase()+t.slice(1)}</button>)}
        </nav>

        {tab === 'overview' && <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {[['Users',stats?.total_users,'👤'],['Groups',stats?.total_groups,'👥'],['Games',stats?.total_games,'🎮'],['Active',stats?.active_games,'⚡'],['Citizens',stats?.citizens_wins,'🟢'],['Mafia',stats?.mafia_wins,'🔴']].map(([label,value,icon]) => <div key={String(label)} className="rounded-xl border border-slate-800 bg-slate-900 p-4"><div className="text-xs text-slate-400">{icon} {label}</div><div className="text-2xl font-bold mt-2">{value ?? '—'}</div></div>)}
          </div>
          <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900 p-5"><h2 className="font-semibold flex gap-2 items-center"><ShieldCheck size={18}/>System status</h2><div className="grid md:grid-cols-3 gap-3 mt-4 text-sm"><div className="p-4 rounded-xl bg-slate-950"><Activity size={17} className="inline mr-2"/>API: connected</div><div className="p-4 rounded-xl bg-slate-950"><Gamepad2 size={17} className="inline mr-2"/>Active games: {stats?.active_games ?? 0}</div><div className="p-4 rounded-xl bg-slate-950"><Users size={17} className="inline mr-2"/>Loaded users: {users.length}</div></div></div>
        </>}

        {tab === 'users' && <Table title="Users" headers={['ID','Name','Username','Games','Wins','XP','Rank','Status']} rows={users.map(u => [u.id,u.first_name+' '+(u.last_name||''),u.username ? '@'+u.username : '—',u.games_played,u.wins,u.xp,u.rank,<button key={u.id} onClick={() => action(`/api/users/${u.id}/${u.is_banned ? 'unban':'ban'}`)} className="text-xs px-2 py-1 rounded border border-slate-700">{u.is_banned ? 'Unban':'Ban'}</button>])} />}
        {tab === 'groups' && <Table title="Groups" headers={['ID','Title','Username','Bot admin','Banned']} rows={groups.map(g => [g.id,g.title,g.username ? '@'+g.username : '—',g.bot_is_admin ? 'YES':'NO',<button key={g.id} onClick={() => action(`/api/groups/${g.id}/${g.is_banned ? 'unban':'ban'}`)} className="text-xs px-2 py-1 rounded border border-slate-700">{g.is_banned ? 'Unban':'Ban'}</button>])} />}
        {tab === 'games' && <Table title="Active games" headers={['Game','Group','Phase','Players','Alive','Round','Action']} rows={games.map(g => [g.game_id.slice(0,8),g.group_title,g.phase,g.players_count,g.alive_count,g.round_number,<button key={g.game_id} onClick={() => action(`/api/active-games/${g.group_id}/reset`)} className="text-xs px-2 py-1 rounded border border-red-900 text-red-300 flex items-center gap-1"><XCircle size={13}/>Reset</button>])} />}
      </div>
    </main>
  );
}

function Table({ title, headers, rows }: { title: string; headers: string[]; rows: (string|number|ReactNode)[][] }) {
  return <section className="rounded-2xl border border-slate-800 bg-slate-900 overflow-x-auto"><div className="p-5 flex items-center gap-2 font-semibold"><Users size={18}/>{title}</div><table className="w-full text-sm"><thead className="bg-slate-950"><tr>{headers.map(h=><th key={h} className="text-left px-4 py-3 text-slate-400 font-medium">{h}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i} className="border-t border-slate-800">{r.map((c,j)=><td key={j} className="px-4 py-3 whitespace-nowrap">{c}</td>)}</tr>)}</tbody></table>{rows.length===0&&<div className="p-8 text-center text-slate-500">Ma’lumot yo‘q</div>}</section>;
}
