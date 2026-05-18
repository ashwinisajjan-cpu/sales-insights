import { useState, useEffect, useCallback, useRef } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer,
} from "recharts";

const API    = "http://localhost:8000";
const COLORS = ["#F5A623","#F47B5E","#00c49f","#a78bfa","#38bdf8","#fb7185"];

const scoreBg = (score) => {
  if (score >= 80) return { bg: "#fef2f2", color: "#b91c1c", border: "#fca5a5" };
  if (score >= 55) return { bg: "#fffbeb", color: "#b45309", border: "#fcd34d" };
  return              { bg: "#f0fdf4", color: "#15803d", border: "#86efac" };
};

const priorityChip = (p) => {
  if (p === "HIGH")   return { bg: "#fef2f2", color: "#b91c1c", dot: "#ef4444" };
  if (p === "MEDIUM") return { bg: "#fffbeb", color: "#b45309", dot: "#f59e0b" };
  return                     { bg: "#f0fdf4", color: "#15803d", dot: "#22c55e" };
};

// ── Chatbot suggestion questions ─────────────────────────────
const CHAT_SUGGESTIONS = [
  "Which companies should I target for cloud?",
  "Show me top 10 prospects",
  "Show HIGH priority accounts",
  "Tell me about Wells Fargo",
  "Show Technology companies",
  "Accounts in Texas",
  "Who haven't I contacted in 6 months?",
  "Show existing customers",
  "Revenue over $100M",
  "Give me a summary",
  "Show upsell opportunities",
  "Which companies to target for IoT?",
];

// ── Format chatbot markdown replies ─────────────────────────
function formatChatReply(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/_(.*?)_/g, "<em>$1</em>")
    .replace(/\n/g, "<br/>");
}

// ── Single chatbot account card ───────────────────────────────
function ChatAccountCard({ account }) {
  const sb = scoreBg(account.score || 0);
  const pc = priorityChip(account.priority || "LOW");
  return (
    <div style={{
      border: `1px solid ${pc.dot}`,
      borderLeft: `4px solid ${pc.dot}`,
      borderRadius: 10,
      padding: "12px 14px",
      marginBottom: 8,
      backgroundColor: pc.bg,
      fontSize: "13px",
    }}>
      <div style={{ fontWeight: "bold", fontSize: "14px", color: "#111827", marginBottom: 4 }}>
        🏢 {account.name}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, color: "#555", marginBottom: 4 }}>
        <span>💰 {account.revenue_fmt || "N/A"}</span>
        <span>👥 {account.employees_fmt || "N/A"}</span>
        <span>🏭 {account.industry || "N/A"}</span>
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
        <span>📍 {[account.billing_city, account.billing_state].filter(Boolean).join(", ") || "N/A"}</span>
        <span style={{
          background: pc.dot, color: "white",
          borderRadius: 10, padding: "1px 8px",
          fontSize: "12px", fontWeight: "bold",
        }}>
          {account.priority || "N/A"}
        </span>
        <span style={{
          background: sb.bg, color: sb.color,
          border: `1px solid ${sb.border}`,
          borderRadius: 10, padding: "1px 8px",
          fontSize: "12px", fontWeight: "bold",
        }}>
          {account.score}/100
        </span>
      </div>
      {account.recommended_action && (
        <div style={{ marginTop: 6, color: "#1d4ed8", fontSize: "12px" }}>
          🚀 {account.recommended_action}
        </div>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════
// TRAVEL PLANNER COMPONENT
// ════════════════════════════════════════════════════════
function TravelPlanner() {
  const [city,       setCity]       = useState("");
  const [data,       setData]       = useState(null);
  const [coverage,   setCoverage]   = useState(null);
  const [loading,    setLoading]    = useState(false);
  const [covLoading, setCovLoading] = useState(true);

  const PRIORITY_COLOR = {
    "VERY HIGH": "#7c3aed",
    "HIGH":      "#dc2626",
    "MEDIUM":    "#d97706",
    "LOW":       "#16a34a",
  };

  useEffect(() => {
    fetch("http://localhost:8000/api/travel-coverage")
      .then(r => r.json())
      .then(d => { setCoverage(d); setCovLoading(false); })
      .catch(() => setCovLoading(false));
  }, []);

  function search(cityOverride) {
    const q = (cityOverride || city).trim();
    if (!q) return;
    setLoading(true);
    setData(null);
    fetch(`http://localhost:8000/api/travel-matches?city=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }

  return (
    <div style={{padding:"0 16px 40px"}}>
      {/* ── Header ── */}
      <div style={{background:"linear-gradient(135deg,#F5A623,#F47B5E)",borderRadius:12,padding:"24px 28px",marginBottom:24,color:"white"}}>
        <h2 style={{margin:"0 0 4px",fontSize:"22px",fontWeight:700}}>✈️ Travel Planner</h2>
        <p style={{margin:0,opacity:0.85}}>Enter a city you're visiting to see which accounts to prioritise for in-person meetings</p>
      </div>

      {/* ── Search bar ── */}
      <div style={{display:"flex",gap:8,marginBottom:24}}>
        <input
          value={city}
          onChange={e => setCity(e.target.value)}
          onKeyDown={e => e.key === "Enter" && search()}
          placeholder="Enter city name  (e.g. Dallas, New York, Chicago)…"
          style={{flex:1,padding:"10px 14px",border:"2px solid #e5e7eb",borderRadius:8,fontSize:"15px",outline:"none"}}
        />
        <button
          onClick={() => search()}
          style={{padding:"10px 22px",background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",border:"none",borderRadius:8,cursor:"pointer",fontWeight:600,fontSize:"14px"}}
        >Search</button>
      </div>

      {/* ── Two-column layout ── */}
      <div style={{display:"grid",gridTemplateColumns:"270px 1fr",gap:20,alignItems:"start"}}>

        {/* Left: top cities sidebar */}
        <div style={{background:"white",borderRadius:12,padding:16,border:"1px solid #e5e7eb"}}>
          <h3 style={{margin:"0 0 12px",fontSize:"14px",fontWeight:700,color:"#374151"}}>📍 Top Cities by Accounts</h3>
          {covLoading && <div style={{color:"#9ca3af",fontSize:"13px"}}>Loading…</div>}
          {coverage && coverage.locations.slice(0, 15).map((loc, i) => (
            <div key={i}
              onClick={() => { setCity(loc.city); search(loc.city); }}
              style={{
                display:"flex", justifyContent:"space-between", alignItems:"center",
                padding:"8px 10px", marginBottom:4, borderRadius:6, cursor:"pointer",
                background: data && data.city.toLowerCase() === loc.city.toLowerCase() ? "#eff6ff" : "#f9fafb",
                border:"1px solid #e5e7eb", transition:"background 0.15s",
              }}
            >
              <div>
                <div style={{fontWeight:600,fontSize:"13px",color:"#111827"}}>{loc.city}</div>
                {loc.state && <div style={{fontSize:"11px",color:"#6b7280"}}>{loc.state}</div>}
              </div>
              <div style={{display:"flex",gap:4,alignItems:"center"}}>
                {loc.high_priority > 0 && (
                  <span style={{background:"#fef2f2",color:"#dc2626",fontSize:"11px",fontWeight:700,padding:"2px 6px",borderRadius:99}}>{loc.high_priority} HP</span>
                )}
                <span style={{background:"#f3f4f6",color:"#374151",fontSize:"12px",padding:"2px 6px",borderRadius:99}}>{loc.count}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Right: search results */}
        <div>
          {loading && (
            <div style={{textAlign:"center",padding:48,color:"#6b7280"}}>⏳ Searching accounts in {city}…</div>
          )}

          {data && data.total_matches === 0 && (
            <div style={{background:"#fff7ed",border:"1px solid #fed7aa",borderRadius:12,padding:32,textAlign:"center",color:"#92400e"}}>
              <div style={{fontSize:"36px",marginBottom:8}}>🔍</div>
              <div style={{fontWeight:600,fontSize:"16px"}}>No accounts found in "{data.city}"</div>
              <div style={{fontSize:"13px",marginTop:6}}>Try a different spelling or click a city from the list</div>
            </div>
          )}

          {data && data.total_matches > 0 && (
            <>
              {/* Summary banner */}
              <div style={{
                background: data.high_priority > 0 ? "#fef2f2" : "#f0fdf4",
                border: `1px solid ${data.high_priority > 0 ? "#fecaca" : "#bbf7d0"}`,
                borderRadius:12, padding:"16px 20px", marginBottom:16,
              }}>
                <div style={{fontWeight:700,fontSize:"16px",color: data.high_priority > 0 ? "#991b1b":"#166534"}}>
                  📌 {data.total_matches} account{data.total_matches !== 1 ? "s" : ""} in {data.city}{data.state ? `, ${data.state}` : ""}
                  {data.high_priority > 0 && (
                    <span style={{marginLeft:10,background:"#fef2f2",color:"#dc2626",fontSize:"12px",padding:"2px 8px",borderRadius:99,border:"1px solid #fecaca"}}>
                      {data.high_priority} High Priority
                    </span>
                  )}
                </div>
                <div style={{fontSize:"14px",marginTop:6,color:"#374151"}}>💡 {data.tip}</div>
              </div>

              {/* Account cards */}
              {data.accounts.map((acc, i) => (
                <div key={i} style={{
                  background:"white", border:"1px solid #e5e7eb", borderRadius:10,
                  padding:"14px 18px", marginBottom:10,
                  display:"flex", alignItems:"flex-start", gap:14,
                }}>
                  {/* Rank badge */}
                  <div style={{
                    width:34, height:34, borderRadius:8, flexShrink:0,
                    background: PRIORITY_COLOR[acc.priority] || "#6b7280",
                    display:"flex", alignItems:"center", justifyContent:"center",
                    color:"white", fontWeight:700, fontSize:"13px",
                  }}>{i + 1}</div>

                  {/* Main info */}
                  <div style={{flex:1}}>
                    <div style={{display:"flex",alignItems:"center",gap:8,flexWrap:"wrap",marginBottom:4}}>
                      <span style={{fontWeight:700,fontSize:"15px",color:"#111827"}}>{acc.name}</span>
                      <span style={{
                        background: PRIORITY_COLOR[acc.priority] || "#6b7280",
                        color:"white", fontSize:"11px", fontWeight:700,
                        padding:"2px 8px", borderRadius:99,
                      }}>{acc.priority}</span>
                      <span style={{background:"#f3f4f6",color:"#374151",fontSize:"12px",padding:"2px 8px",borderRadius:99}}>
                        Score: {acc.score}
                      </span>
                    </div>
                    <div style={{fontSize:"13px",color:"#6b7280"}}>
                      📍 {[acc.billing_city, acc.billing_state].filter(Boolean).join(", ") || "N/A"}
                      &nbsp;•&nbsp;🏭 {acc.industry || "N/A"}
                      &nbsp;•&nbsp;👤 {acc.owner_name || "Unassigned"}
                    </div>
                    {acc.recommended_action && (
                      <div style={{
                        marginTop:6, fontSize:"13px", color:"#1d4ed8",
                        background:"#eff6ff", borderRadius:6,
                        padding:"4px 8px", display:"inline-block",
                      }}>🚀 {acc.recommended_action}</div>
                    )}
                  </div>

                  {/* Right: revenue / employees */}
                  <div style={{textAlign:"right",flexShrink:0}}>
                    {acc.revenue_fmt && acc.revenue_fmt !== "N/A" && (
                      <div style={{fontSize:"13px",fontWeight:600,color:"#059669"}}>{acc.revenue_fmt}</div>
                    )}
                    {acc.employees_fmt && acc.employees_fmt !== "N/A" && (
                      <div style={{fontSize:"12px",color:"#9ca3af",marginTop:2}}>{acc.employees_fmt} emp</div>
                    )}
                    {acc.phone && (
                      <div style={{fontSize:"11px",color:"#6b7280",marginTop:4}}>📞 {acc.phone}</div>
                    )}
                  </div>
                </div>
              ))}
            </>
          )}

          {/* Empty state before first search */}
          {!loading && !data && (
            <div style={{
              background:"white", border:"2px dashed #e5e7eb", borderRadius:12,
              padding:56, textAlign:"center", color:"#9ca3af",
            }}>
              <div style={{fontSize:"48px",marginBottom:12}}>✈️</div>
              <div style={{fontWeight:600,fontSize:"16px",color:"#374151"}}>Ready to plan your trip</div>
              <div style={{marginTop:8,fontSize:"14px"}}>Search a city above or click one from the list on the left</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════
// WEEKLY TARGETS COMPONENT
// ════════════════════════════════════════════════════════
function WeeklyTargets() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const load = () => {
    setLoading(true); setError(null);
    fetch("http://localhost:8000/api/weekly-targets")
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const priorityColor = p => ({
    "HIGH":      "#dc2626",
    "VERY HIGH": "#7c3aed",
    "MEDIUM":    "#d97706",
    "LOW":       "#16a34a",
  }[p] || "#6b7280");

  const medals = ["🥇","🥈","🥉"];

  // Calculate stats client-side so they always show even if backend omits them
  const totalSellers      = data?.sellers?.length || 0;
  const totalTargets      = data?.sellers?.reduce((t, s) => t + (s.top_targets?.length || 0), 0) || 0;
  const totalAccounts     = data?.sellers?.reduce((t, s) => t + (s.total_accounts || 0), 0) || 0;
  const highPriorityCount = data?.sellers?.reduce(
    (t, s) => t + (s.top_targets?.filter(a => a.priority === "HIGH" || a.priority === "VERY HIGH").length || 0), 0
  ) || 0;

  return (
    <div style={{padding:"0 4px"}}>
      {/* Header */}
      <div style={{background:"linear-gradient(135deg,#F5A623,#F47B5E)",borderRadius:14,padding:"24px 28px",marginBottom:24,color:"white"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div>
            <h2 style={{margin:0,fontSize:"22px",fontWeight:700}}>📅 Weekly Top Targets</h2>
            <p style={{margin:"6px 0 0",opacity:0.85}}>{data?.week || "Loading..."}</p>
          </div>
          <button onClick={load} style={{background:"rgba(255,255,255,0.2)",border:"1px solid rgba(255,255,255,0.4)",color:"white",padding:"8px 18px",borderRadius:20,cursor:"pointer",fontWeight:600}}>
            🔄 Refresh
          </button>
        </div>
        {data && (
          <div style={{display:"flex",gap:24,marginTop:18,flexWrap:"wrap"}}>
            {[
              ["👔 Sellers",       totalSellers],
              ["🎯 Total Targets", totalTargets],
              ["📋 Total Accounts",totalAccounts],
              ["🔴 HIGH Priority", highPriorityCount],
            ].map(([label, val]) => (
              <div key={label} style={{background:"rgba(255,255,255,0.15)",borderRadius:10,padding:"10px 18px",textAlign:"center"}}>
                <div style={{fontSize:"22px",fontWeight:700}}>{val}</div>
                <div style={{fontSize:"12px",opacity:0.85}}>{label}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {loading && <div style={{textAlign:"center",padding:40,color:"#6b7280"}}>⏳ Loading weekly targets...</div>}
      {error   && <div style={{textAlign:"center",padding:40,color:"#dc2626"}}>❌ {error}</div>}

      {/* Seller cards */}
      {data?.sellers?.map(seller => (
        <div key={seller.owner} style={{background:"white",borderRadius:12,border:"1px solid #e5e7eb",marginBottom:20,overflow:"hidden",boxShadow:"0 1px 4px rgba(0,0,0,0.06)"}}>
          {/* Seller header */}
          <div style={{background:"#f8fafc",borderBottom:"1px solid #e5e7eb",padding:"14px 20px",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <div>
              <span style={{fontWeight:700,fontSize:"15px"}}>👔 {seller.owner}</span>
              <span style={{marginLeft:12,color:"#6b7280",fontSize:"13px"}}>{seller.total_accounts} accounts total</span>
            </div>
            <span style={{background:"#fee2e2",color:"#dc2626",padding:"3px 10px",borderRadius:12,fontSize:"13px",fontWeight:600}}>
              🔴 {seller.high_priority_count} HIGH priority
            </span>
          </div>
          {/* Top 3 targets */}
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:0}}>
            {seller.top_targets.map((t, i) => (
              <div key={t.name} style={{padding:"16px 20px",borderRight: i < seller.top_targets.length-1 ? "1px solid #f0f0f0" : "none"}}>
                <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:8}}>
                  <span style={{fontSize:"20px"}}>{medals[i]}</span>
                  <div>
                    <div style={{fontWeight:700,fontSize:"14px"}}>{t.name}</div>
                    <div style={{fontSize:"12px",color:"#6b7280"}}>{t.industry || "N/A"}</div>
                  </div>
                </div>
                <div style={{display:"flex",flexWrap:"wrap",gap:6,fontSize:"12px"}}>
                  <span style={{background:priorityColor(t.priority)+"22",color:priorityColor(t.priority),padding:"2px 8px",borderRadius:10,fontWeight:600}}>{t.priority}</span>
                  <span style={{background:"#eff6ff",color:"#1d4ed8",padding:"2px 8px",borderRadius:10,fontWeight:600}}>Score: {t.score}/100</span>
                  <span style={{background:"#f0fdf4",color:"#15803d",padding:"2px 8px",borderRadius:10}}>{t.revenue_fmt}</span>
                </div>
                <div style={{marginTop:8,fontSize:"13px",color:"#374151"}}>
                  📍 {[t.billing_city, t.billing_state].filter(Boolean).join(", ") || "N/A"}
                </div>
                {t.action && (
                  <div style={{marginTop:6,fontSize:"12px",color:"#6b7280",fontStyle:"italic"}}>💡 {t.action}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [accounts,  setAccounts]  = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [connected, setConnected] = useState(false);
  const [tab,       setTab]       = useState("accounts");
  const [search,    setSearch]    = useState("");
  const [priFilter, setPriFilter] = useState("ALL");

  const [companyInput,     setCompanyInput]     = useState("");
  const [aiLoading,        setAiLoading]        = useState(false);
  const [aiInsight,        setAiInsight]        = useState(null);
  const [wikiData,         setWikiData]         = useState(null);
  const [newsSignals,      setNewsSignals]      = useState(null);
  const [selectedAccount,  setSelectedAccount]  = useState(null);
  const [selectedCompany,  setSelectedCompany]  = useState("");

  const [topProspects,     setTopProspects]     = useState([]);
  const [topLoading,       setTopLoading]       = useState(false);

  const [copilotOpen,      setCopilotOpen]      = useState(false);
  const [copilotInput,     setCopilotInput]     = useState("");

  // ── CHATBOT STATE ────────────────────────────────────────────
  const [chatMessages,  setChatMessages]  = useState([
    {
      role: "bot",
      text: "👋 Hi! I'm your **Lumen Sales Assistant**.\n\nAsk me anything about your Salesforce accounts!\n\n• _'Which companies should I target for cloud?'_\n• _'Show top 10 prospects'_\n• _'Tell me about Wells Fargo'_",
      accounts: [],
      tip: "",
    },
  ]);
  const [chatInput,   setChatInput]   = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const chatBottomRef = useRef(null);
  const chatInputRef  = useRef(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, tab]);

  // ── Send chatbot message ─────────────────────────────────────
  const sendChat = async (text) => {
    const msg = (text || chatInput).trim();
    if (!msg || chatLoading) return;
    setChatInput("");
    setShowSuggestions(false);

    const userMsg    = { role: "user", text: msg, accounts: [], tip: "" };
    const loadingMsg = { role: "bot", text: "", loading: true, accounts: [], tip: "" };
    setChatMessages(prev => [...prev, userMsg, loadingMsg]);
    setChatLoading(true);

    try {
      const res  = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      const botMsg = {
        role:     "bot",
        text:     data.answer   || data.reply || "Sorry, no response.",
        accounts: data.accounts || [],
        tip:      data.tip      || "",
        intent:   data.intent   || "",
        loading:  false,
      };
      setChatMessages(prev => [...prev.slice(0, -1), botMsg]);
    } catch (e) {
      setChatMessages(prev => [...prev.slice(0, -1), {
        role: "bot",
        text: "❌ Cannot connect to backend. Make sure Python is running on port 8000.",
        accounts: [], tip: "", loading: false,
      }]);
    }
    setChatLoading(false);
    setTimeout(() => chatInputRef.current?.focus(), 100);
  };

  const handleChatKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  };

  // ── Fetch all accounts ───────────────────────────────────────
  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const res  = await fetch(`${API}/api/accounts`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (Array.isArray(data)) {
        setAccounts(data);
        setConnected(true);
      } else {
        throw new Error(data.detail || data.error || "Unknown error");
      }
    } catch (e) {
      alert("❌ Cannot connect! Make sure the Python backend is running on port 8000.\nError: " + e.message);
    }
    setLoading(false);
  };

  const fetchTopProspects = async () => {
    setTopLoading(true);
    try {
      const res  = await fetch(`${API}/api/top-prospects?limit=10`);
      const data = await res.json();
      setTopProspects(data.top_prospects || []);
    } catch (e) {
      console.warn("Top prospects fetch failed:", e.message);
    }
    setTopLoading(false);
  };

  useEffect(() => {
    if (connected) fetchTopProspects();
  }, [connected]);

  const getAiInsight = useCallback(async (company, account) => {
    if (!company.trim()) return;
    setAiLoading(true);
    setAiInsight(null);
    setWikiData(null);
    setNewsSignals(null);
    setSelectedCompany(company);

    const found = account || accounts.find(
      a => (a.name || "").toLowerCase() === company.toLowerCase()
        || (a.name || "").toLowerCase().includes(company.toLowerCase())
    );
    if (found) setSelectedAccount(found);

    let insight = null;
    let wiki    = null;

    try {
      const res  = await fetch(`${API}/company-insights?company=${encodeURIComponent(company)}`);
      const data = await res.json();
      if (data?.summary) {
        const s  = data.summary     || {};
        const ai = data.ai_insights || {};
        const w  = data.wikipedia   || {};

        insight = {
          financialStatus:   ai.financial_status || s.annual_revenue  || "Not Available",
          headcount:         ai.headcount        || s.employees       || "Not Available",
          mission:           ai.mission          || w.wiki_summary    || "Not Available",
          coreValues:        ai.core_values      || "Not Available",
          solutions:         ai.solutions        || "Not Available",
          score:             s.score,
          priority:          s.priority,
          recommendedAction: s.recommended_action,
        };
        wiki = {
          summary:   w.wiki_summary  || "",
          url:       w.wiki_url      || "",
          image:     w.wiki_image    || "",
          founded:   w.wiki_founded  || "",
          hq:        w.wiki_hq       || "",
          industry:  w.wiki_industry || "",
          products:  w.wiki_products || [],
          ceo:       w.wiki_ceo      || "",
          revenue:   w.wiki_revenue  || "",
          employees: w.wiki_employees|| "",
        };

        if (!found && data.sf_found && s) {
          setSelectedAccount({
            name:               s.name || company,
            revenue_fmt:        s.annual_revenue  || "N/A",
            employees_fmt:      s.employees       || "N/A",
            industry:           s.industry        || "N/A",
            score:              s.score,
            priority:           s.priority,
            recommended_action: s.recommended_action,
            billing_address:    s.location        || "N/A",
            billing_city:       (s.location||"").split(",")[0] || "",
            billing_state:      (s.location||"").split(",")[1] || "",
            billing_country:    (s.location||"").split(",")[2] || "",
            type:               s.account_type    || "N/A",
            owner_name:         s.sales_director  || "N/A",
            owner_email:        s.director_email  || "N/A",
            sales_potential:    s.sales_potential || "N/A",
            website:            s.website         || "",
            phone:              s.phone           || "",
            description:        s.description     || "",
            rating:             s.rating          || "",
            lead_source:        s.lead_source     || "",
            parent_name:        s.parent_account  || "",
            id:                 s.salesforce_id   || "",
            last_activity:      s.last_activity   || "",
          });
        }
      }
    } catch (e) {
      console.warn("Backend failed:", e.message);
    }

    if (!insight) {
      try {
        const r = await fetch(
          `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(company.replace(/ /g,"_"))}`
        );
        const d = await r.json();
        if (d.extract) {
          wiki    = { summary: d.extract, url: d.content_urls?.desktop?.page||"", image: d.thumbnail?.source||"", products: [] };
          insight = {
            financialStatus: d.extract.substring(0,200),
            headcount:       "See company website",
            mission:         d.extract.substring(0,300),
            coreValues:      "Innovation, Integrity, Customer Focus, Excellence, Teamwork",
            solutions:       d.description || "Products and professional services",
          };
        }
      } catch (e) { /* silent */ }
    }

    if (!insight) {
      insight = {
        financialStatus: "Financial data not publicly available",
        headcount:       "Headcount data not available",
        mission:         `${company} is committed to delivering value to customers and communities.`,
        coreValues:      "Integrity, Innovation, Customer Focus, Excellence, Teamwork",
        solutions:       "Professional services and industry-specific solutions",
      };
    }

    setAiInsight(insight);
    if (wiki) setWikiData(wiki);

    // Fetch news signals for the company
    try {
      const nr = await fetch(`http://localhost:8000/api/news-signals?company=${encodeURIComponent(company)}`);
      if (nr.ok) setNewsSignals(await nr.json());
    } catch(e) { /* news signals optional */ }
    setAiLoading(false);
  }, [accounts]);

  const displayed = accounts
    .filter(a => priFilter === "ALL" || a.priority === priFilter)
    .filter(a => (a.name||"").toLowerCase().includes(search.toLowerCase()))
    .slice()
    .sort((a, b) => b.score - a.score);

  const revenueByIndustry = Object.entries(
    accounts.reduce((acc, a) => {
      if (a.industry && a.revenue) acc[a.industry] = (acc[a.industry]||0) + Number(a.revenue||0);
      return acc;
    }, {})
  ).slice(0,8).map(([name, revenue]) => ({
    name: name.length > 14 ? name.slice(0,14)+"…" : name,
    revenue: +(revenue/1e6).toFixed(1),
  }));

  const industryCount = Object.entries(
    accounts.reduce((acc,a) => { if(a.industry) acc[a.industry]=(acc[a.industry]||0)+1; return acc; }, {})
  ).slice(0,6).map(([name,value])=>({name,value}));

  const empDist = [
    { name:"0–100",    count: accounts.filter(a=>+a.employees>0    && +a.employees<=100).length },
    { name:"100–500",  count: accounts.filter(a=>+a.employees>100  && +a.employees<=500).length },
    { name:"500–1000", count: accounts.filter(a=>+a.employees>500  && +a.employees<=1000).length },
    { name:"1000+",    count: accounts.filter(a=>+a.employees>1000).length },
  ];

  const priDist = ["HIGH","MEDIUM","LOW"].map(p=>({ name:p, value:accounts.filter(a=>a.priority===p).length }));
  const priDistColors = ["#ef4444","#f59e0b","#22c55e"];

  return (
    <div style={css.root}>

      {/* HEADER */}
      <header style={css.header}>
        <div>
          <h1 style={css.logo}>🏢 Sales Insights AI</h1>
          <p style={css.logoSub}>Lumen Sales Director Account Mapping — Powered by Salesforce + Wikipedia</p>
        </div>
        <nav style={css.nav}>
          {[
            ["accounts",  "🏢 Accounts"],
            ["ai",        "🤖 AI Insights"],
            ["prospects", "🎯 Top Prospects"],
            ["weekly",    "📅 Weekly Targets"],
            ["travel",    "✈️ Travel Planner"],
            ["dashboard", "📊 Dashboard"],
            ["charts",    "📈 Charts"],
            ["chatbot",   "💬 Chatbot"],
          ].map(([key, label]) => (
            <button key={key}
              style={tab===key ? css.navActive : css.navBtn}
              onClick={() => setTab(key)}
            >{label}</button>
          ))}
        </nav>
      </header>

      <main style={css.main}>

        {/* ════════════ ACCOUNTS TAB ════════════ */}
        {tab === "accounts" && <>
          <div style={css.card}>
            <h2 style={css.cardTitle}>🔗 Connect to Salesforce</h2>
            <button
              style={loading ? css.btnDisabled : css.btn}
              onClick={fetchAccounts}
              disabled={loading}
            >
              {loading ? "⏳ Connecting…" : connected ? "🔄 Refresh Accounts" : "🔗 Connect & Load Accounts"}
            </button>
            {connected && <p style={css.ok}>✅ {accounts.length} accounts loaded and scored!</p>}
          </div>

          {connected && <>
            <div style={{...css.card, padding:"16px 24px"}}>
              <div style={css.filterRow}>
                <input
                  style={css.input}
                  placeholder="🔍 Search company name…"
                  value={search}
                  onChange={e=>setSearch(e.target.value)}
                />
                <div style={css.chipRow}>
                  {["ALL","HIGH","MEDIUM","LOW"].map(p=>(
                    <button key={p}
                      style={priFilter===p ? css.chipActive : css.chip}
                      onClick={()=>setPriFilter(p)}
                    >{p}</button>
                  ))}
                </div>
                <span style={{color:"#6b7280",fontSize:"13px",whiteSpace:"nowrap"}}>
                  {displayed.length} of {accounts.length}
                </span>
              </div>
            </div>

            <div style={css.card}>
              <div style={{overflowX:"auto"}}>
                <table style={css.table}>
                  <thead>
                    <tr>
                      {["#","Company Name","Industry","Revenue","Employees","Score","Priority","Recommended Action","AI Insights"].map(h=>(
                        <th key={h} style={css.th}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {displayed.map((row,i)=>{
                      const sb = scoreBg(row.score||0);
                      const pc = priorityChip(row.priority||"LOW");
                      return (
                        <tr key={row.id||i}
                          style={{backgroundColor: i%2===0?"#ffffff":"#fafafa", transition:"background .15s"}}
                          onMouseEnter={e=>e.currentTarget.style.backgroundColor="#fff7ed"}
                          onMouseLeave={e=>e.currentTarget.style.backgroundColor=i%2===0?"#ffffff":"#fafafa"}
                        >
                          <td style={{...css.td,color:"#9ca3af",width:"40px"}}>{i+1}</td>
                          <td style={{...css.td,fontWeight:"600"}}>{row.name||"—"}</td>
                          <td style={css.td}>{row.industry||"—"}</td>
                          <td style={{...css.td,color:"#047857",fontWeight:"600"}}>{row.revenue_fmt||"—"}</td>
                          <td style={css.td}>{row.employees_fmt||"—"}</td>
                          <td style={css.td}>
                            <span style={{display:"inline-block",padding:"3px 10px",borderRadius:"20px",background:sb.bg,color:sb.color,border:`1px solid ${sb.border}`,fontWeight:"700",fontSize:"14px"}}>
                              {row.score||0}/100
                            </span>
                          </td>
                          <td style={css.td}>
                            <span style={{display:"inline-flex",alignItems:"center",gap:"5px",padding:"3px 10px",borderRadius:"20px",background:pc.bg,color:pc.color,fontWeight:"600",fontSize:"13px"}}>
                              <span style={{width:"6px",height:"6px",borderRadius:"50%",background:pc.dot,flexShrink:0}}/>
                              {row.priority||"LOW"}
                            </span>
                          </td>
                          <td style={{...css.td,maxWidth:"200px",fontSize:"13px",color:"#374151"}}>
                            {row.recommended_action||"—"}
                          </td>
                          <td style={css.td}>
                            <button style={css.aiBtn}
                              onClick={()=>{ setCompanyInput(row.name||""); setTab("ai"); getAiInsight(row.name||"", row); }}
                            >🤖 View</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>}

          {!connected && (
            <div style={{...css.card, textAlign:"center", padding:"60px 30px"}}>
              <p style={{fontSize:"16px",color:"#6b7280",marginBottom:"20px"}}>
                Click "Connect & Load Accounts" above to start
              </p>
              <div style={css.featGrid}>
                {["🏢 200 Salesforce Accounts","📊 AI Prospect Score (0–100)","🎯 HIGH / MEDIUM / LOW Priority",
                  "💡 Recommended Sales Action","📖 Wikipedia Enrichment","💬 AI Chatbot"].map((f,i)=>(
                  <div key={i} style={css.featCard}>{f}</div>
                ))}
              </div>
            </div>
          )}
          {connected && (
            <div style={{textAlign:"right",padding:"8px 0 16px"}}>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px"}} onClick={()=>setTab("ai")}>View AI Insights →</button>
            </div>
          )}
        </>}

        {/* ════════════ AI INSIGHTS TAB ════════════ */}
        {tab === "ai" && (
          <div style={css.card}>
            <h2 style={css.cardTitle}>🤖 AI Company Insights</h2>
            <p style={{color:"#6b7280",marginBottom:"20px"}}>
              Enter any company name — fetches data from Salesforce + Wikipedia automatically.
            </p>
            <div style={css.searchRow}>
              <input
                style={{...css.input, flex:1}}
                placeholder="e.g. Wells Fargo, Microsoft, Lumen Technologies…"
                value={companyInput}
                onChange={e=>setCompanyInput(e.target.value)}
                onKeyDown={e=>e.key==="Enter" && getAiInsight(companyInput)}
              />
              <button
                style={aiLoading||!companyInput ? css.btnDisabled : css.btn}
                onClick={()=>getAiInsight(companyInput)}
                disabled={aiLoading||!companyInput}
              >
                {aiLoading ? "⏳ Loading…" : "🤖 Get Insight"}
              </button>
            </div>

            {aiLoading && <div style={css.loadBox}>⏳ Fetching "{companyInput}" from Salesforce + Wikipedia…</div>}

            {aiInsight && !aiLoading && <>
              <div style={css.banner}>
                <div>
                  <h2 style={{margin:0,fontSize:"20px"}}>🏢 {selectedCompany}</h2>
                  {aiInsight.priority && (
                    <span style={{display:"inline-flex",alignItems:"center",gap:"5px",padding:"4px 12px",borderRadius:"20px",marginTop:"8px",fontWeight:"600",fontSize:"13px",background:"rgba(255,255,255,0.2)",color:"white"}}>
                      Priority: {aiInsight.priority}
                      {aiInsight.score != null && ` · Score: ${aiInsight.score}/100`}
                    </span>
                  )}
                </div>
                {aiInsight.score != null && (
                  <div style={{textAlign:"center"}}>
                    <div style={{fontSize:"36px",fontWeight:"800",lineHeight:1}}>{aiInsight.score}</div>
                    <div style={{fontSize:"13px",opacity:.8}}>/100 Prospect Score</div>
                  </div>
                )}
              </div>

              {aiInsight.recommendedAction && (
                <div style={css.actionBox}>
                  <strong>📌 Recommended Action:</strong> {aiInsight.recommendedAction}
                </div>
              )}

              <div style={css.insightGrid}>
                {[
                  {icon:"💰",label:"Financial Status",val:aiInsight.financialStatus},
                  {icon:"👥",label:"Headcount",       val:aiInsight.headcount},
                  {icon:"🎯",label:"Mission",          val:aiInsight.mission},
                  {icon:"⭐",label:"Core Values",      val:aiInsight.coreValues},
                  {icon:"🔧",label:"Solutions",        val:aiInsight.solutions},
                ].map((item,i)=>(
                  <div key={i} style={css.insightCard}>
                    <div style={css.insightLabel}>{item.icon} {item.label}</div>
                    <div style={css.insightVal}>{item.val||"N/A"}</div>
                  </div>
                ))}
              </div>

              {wikiData?.summary && (
                <div style={css.wikiCard}>
                  <h3 style={{color:"#5c35cc",marginTop:0}}>📖 Wikipedia Enrichment</h3>
                  <div style={css.wikiGrid}>
                    {[
                      {label:"🏭 Industry",val:wikiData.industry||"N/A"},
                      {label:"📅 Founded", val:wikiData.founded||"N/A"},
                      {label:"📍 HQ",      val:wikiData.hq||"N/A"},
                      {label:"👔 CEO",     val:wikiData.ceo||"N/A"},
                    ].map((f,i)=>(
                      <div key={i} style={css.wikiFactCard}>
                        <div style={{fontSize:"11px",color:"#9ca3af",fontWeight:"600",marginBottom:"4px"}}>{f.label}</div>
                        <div style={{fontSize:"14px",fontWeight:"700",color:"#1f2937"}}>{f.val}</div>
                      </div>
                    ))}
                  </div>
                  <p style={{color:"#4b5563",lineHeight:"1.7",fontSize:"14px",margin:"0 0 12px"}}>{wikiData.summary}</p>
                  {wikiData.products?.length>0 && (
                    <div style={css.tagRow}>
                      {wikiData.products.map((p,i)=><span key={i} style={css.tag}>{p}</span>)}
                    </div>
                  )}
                  {wikiData.url && <a href={wikiData.url} target="_blank" rel="noreferrer" style={css.wikiLink}>🔗 Read more on Wikipedia →</a>}
                </div>
              )}

              {/* ── NEWS SIGNALS ── */}
              {newsSignals && (newsSignals.signals?.length > 0 || newsSignals.headlines?.length > 0) && (
                <div style={{background: newsSignals.hot_lead ? "#fef3c7" : "#f0fdf4", border: `1px solid ${newsSignals.hot_lead ? "#f59e0b" : "#86efac"}`, borderRadius:12, padding:"18px 20px", marginBottom:18}}>
                  <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:12}}>
                    <h4 style={{margin:0, fontSize:"15px", fontWeight:700}}>
                      {newsSignals.hot_lead ? "🔥 HOT LEAD" : "📰"} News Signals for {selectedCompany}
                    </h4>
                    {newsSignals.score_boost > 0 && (
                      <span style={{background:"#dc2626", color:"white", padding:"3px 10px", borderRadius:12, fontSize:"13px", fontWeight:700}}>
                        +{newsSignals.score_boost} Score Boost
                      </span>
                    )}
                  </div>
                  {newsSignals.signals?.map((sig, i) => (
                    <div key={i} style={{background:"white", borderRadius:8, padding:"10px 14px", marginBottom:8, border:"1px solid #e5e7eb"}}>
                      <div style={{fontWeight:700, marginBottom:4}}>{sig.emoji} {sig.label} <span style={{background:"#fee2e2",color:"#dc2626",padding:"1px 7px",borderRadius:10,fontSize:"12px",marginLeft:6}}>+{sig.boost} pts</span></div>
                      <div style={{fontSize:"13px", color:"#374151", marginBottom:4}}>📰 {sig.headline}</div>
                      <div style={{fontSize:"12px", color:"#6b7280", fontStyle:"italic"}}>💡 {sig.tip}</div>
                    </div>
                  ))}
                  {newsSignals.signals?.length === 0 && newsSignals.headlines?.length > 0 && (
                    <div style={{fontSize:"13px", color:"#6b7280"}}>
                      <strong>Recent headlines:</strong>
                      <ul style={{marginTop:6, paddingLeft:18}}>
                        {newsSignals.headlines.map((h,i) => <li key={i} style={{marginBottom:3}}>{h}</li>)}
                      </ul>
                    </div>
                  )}
                  {newsSignals.signals?.length === 0 && newsSignals.headlines?.length === 0 && (
                    <p style={{margin:0, color:"#6b7280", fontSize:"13px"}}>No recent news signals detected.</p>
                  )}
                </div>
              )}

              <div style={css.ctaBox}>
                <span style={{color:"#047857",fontWeight:"600"}}>✅ Data loaded for {selectedCompany}</span>
              </div>
            </>}

            {!aiInsight && !aiLoading && (
              <div style={css.placeholder}>
                <p style={{fontSize:"16px",fontWeight:"600",marginBottom:"12px"}}>Enter a company name above to get started</p>
                <div style={css.tagRow}>
                  {["💰 Financial Status","👥 Headcount","🎯 Mission","⭐ Core Values","🔧 Solutions","📊 Prospect Score","🎯 Priority Tag","📌 Recommended Action","📖 Wikipedia Summary","📅 Founded","👔 CEO"].map((t,i)=>(
                    <span key={i} style={css.tag}>{t}</span>
                  ))}
                </div>
              </div>
            )}
            <div style={{display:"flex",justifyContent:"space-between",padding:"16px 0 4px"}}>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px",background:"linear-gradient(135deg,#6b7280,#4b5563)"}} onClick={()=>setTab("accounts")}>← Back to Accounts</button>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px"}} onClick={()=>setTab("prospects")}>View Top Prospects →</button>
            </div>
          </div>
        )}

        {/* ════════════ TOP PROSPECTS TAB ════════════ */}
        {tab === "prospects" && <>
          {!connected ? (
            <div style={css.warnBox}>
              ⚠️ Load accounts first!
              <button style={css.smallBtn} onClick={()=>setTab("accounts")}>Go to Accounts →</button>
            </div>
          ) : topLoading ? (
            <div style={{...css.card,textAlign:"center",padding:"50px"}}>⏳ Loading top prospects…</div>
          ) : (
            <>
              <div style={css.card}>
                <h2 style={css.cardTitle}>🎯 Top 10 Prospect Targets This Week</h2>
                <p style={{color:"#6b7280",marginBottom:"20px"}}>Companies ranked by AI Prospect Score (0–100).</p>
                {topProspects.map((row,i)=>{
                  const sb = scoreBg(row.score||0);
                  const pc = priorityChip(row.priority||"LOW");
                  return (
                    <div key={row.id||i} style={{display:"flex",alignItems:"center",gap:"16px",padding:"16px",marginBottom:"12px",borderRadius:"12px",border:"1px solid #e5e7eb",backgroundColor:i===0?"#fffbeb":i===1?"#fef7ff":i===2?"#f0fdf4":"white",cursor:"pointer",transition:"all .15s"}}
                      onMouseEnter={e=>e.currentTarget.style.boxShadow="0 4px 12px rgba(0,0,0,0.08)"}
                      onMouseLeave={e=>e.currentTarget.style.boxShadow="none"}
                      onClick={()=>{ setTab("ai"); setCompanyInput(row.name); getAiInsight(row.name,row); }}
                    >
                      <div style={{width:"36px",height:"36px",borderRadius:"50%",background:i<3?"linear-gradient(135deg,#F5A623,#F47B5E)":"#e5e7eb",color:i<3?"white":"#6b7280",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:"800",fontSize:"14px",flexShrink:0}}>
                        {i+1}
                      </div>
                      <div style={{flex:1,minWidth:0}}>
                        <div style={{fontWeight:"700",fontSize:"14px",color:"#111827"}}>{row.name}</div>
                        <div style={{fontSize:"13px",color:"#6b7280"}}>{row.industry||"—"} · {row.revenue_fmt||"N/A"}</div>
                      </div>
                      <span style={{padding:"4px 12px",borderRadius:"20px",background:sb.bg,color:sb.color,border:`1px solid ${sb.border}`,fontWeight:"800",fontSize:"14px"}}>{row.score}/100</span>
                      <span style={{display:"inline-flex",alignItems:"center",gap:"5px",padding:"4px 12px",borderRadius:"20px",background:pc.bg,color:pc.color,fontWeight:"600",fontSize:"13px"}}>
                        <span style={{width:"6px",height:"6px",borderRadius:"50%",background:pc.dot}}/>{row.priority}
                      </span>
                      <div style={{fontSize:"12px",color:"#374151",maxWidth:"180px",textAlign:"right",lineHeight:"1.4"}}>{row.recommended_action}</div>
                      <button style={css.aiBtn}>View →</button>
                    </div>
                  );
                })}
              </div>

              <div style={css.card}>
                <h3 style={css.cardTitle}>📐 How the Score is Calculated</h3>
                <div style={{display:"grid",gridTemplateColumns:"repeat(5,1fr)",gap:"12px"}}>
                  {[
                    {label:"💰 Revenue",    pts:"40 pts",desc:"Based on annual revenue bands"},
                    {label:"👥 Employees",  pts:"20 pts",desc:"Company size signals capacity"},
                    {label:"🏭 Industry",   pts:"20 pts",desc:"Fit with Lumen's target sectors"},
                    {label:"📅 Engagement", pts:"10 pts",desc:"Recency of last Salesforce activity"},
                    {label:"🏢 Account Type",pts:"10 pts",desc:"Customer > Prospect > Other"},
                  ].map((item,i)=>(
                    <div key={i} style={{textAlign:"center",padding:"16px",borderRadius:"10px",border:"1px solid #e5e7eb",backgroundColor:"#fafafa"}}>
                      <div style={{fontSize:"15px",marginBottom:"6px"}}>{item.label}</div>
                      <div style={{fontSize:"18px",fontWeight:"800",color:"#F5A623"}}>{item.pts}</div>
                      <div style={{fontSize:"12px",color:"#6b7280",marginTop:"6px"}}>{item.desc}</div>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{display:"flex",justifyContent:"space-between",padding:"8px 0 4px"}}>
                <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px",background:"linear-gradient(135deg,#6b7280,#4b5563)"}} onClick={()=>setTab("ai")}>← Back to AI Insights</button>
                <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px"}} onClick={()=>setTab("weekly")}>View Weekly Targets →</button>
              </div>
            </>
          )}
        </>}

        {/* ════════════ DASHBOARD TAB ════════════ */}
        {tab === "dashboard" && <>
          {!selectedAccount ? (
            <div style={css.warnBox}>
              ⚠️ No company selected.
              <button style={css.smallBtn} onClick={()=>setTab("ai")}>Go to AI Insights →</button>
            </div>
          ) : null}

          {selectedAccount && <>
            <div style={{...css.banner,marginBottom:"20px"}}>
              <div>
                <h2 style={{margin:0,fontSize:"20px"}}>📌 {selectedAccount.name}</h2>
                <p style={{margin:"6px 0 0",opacity:.8,fontSize:"13px"}}>Click any company in AI Insights to update this dashboard</p>
              </div>
              {selectedAccount.score != null && (
                <div style={{textAlign:"center"}}>
                  <div style={{fontSize:"40px",fontWeight:"800",lineHeight:1}}>{selectedAccount.score}</div>
                  <div style={{fontSize:"13px",opacity:.8}}>/100 Prospect Score</div>
                </div>
              )}
            </div>

            {selectedAccount.recommended_action && (
              <div style={css.actionBox}>
                <strong>📌 Recommended Action:</strong> {selectedAccount.recommended_action}
              </div>
            )}

            <div style={css.kpiGrid}>
              {[
                {icon:"💰",label:"Annual Revenue",   val:selectedAccount.revenue_fmt||"—",    color:"#047857"},
                {icon:"👥",label:"Employees",         val:selectedAccount.employees_fmt||"—"},
                {icon:"🏭",label:"Industry",           val:selectedAccount.industry||"—"},
                {icon:"⭐",label:"Priority",           val:selectedAccount.priority||"—",      color:priorityChip(selectedAccount.priority||"LOW").color},
                {icon:"📍",label:"Location",           val:[selectedAccount.billing_city,selectedAccount.billing_state,selectedAccount.billing_country].filter(Boolean).join(", ")||selectedAccount.billing_address||"—"},
                {icon:"🏢",label:"Account Type",       val:selectedAccount.type||"—"},
                {icon:"👔",label:"Sales Director",     val:selectedAccount.owner_name||"—"},
                {icon:"📈",label:"Sales Potential",    val:selectedAccount.sales_potential||"—",color:"#1d4ed8"},
                {icon:"📅",label:"Last Activity",      val:selectedAccount.last_activity||"—"},
              ].map((item,i)=>(
                <div key={i} style={css.kpiCard}>
                  <div style={css.kpiLabel}>{item.icon} {item.label}</div>
                  <div style={{...css.kpiVal,color:item.color||"#F5A623"}}>{item.val}</div>
                </div>
              ))}
            </div>

            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"20px",marginBottom:"20px"}}>
              <div style={css.card}>
                <h3 style={css.secTitle}>🏢 Company Profile</h3>
                {[
                  {l:"Company Name",  v:selectedAccount.name},
                  {l:"Industry",      v:selectedAccount.industry},
                  {l:"Account Type",  v:selectedAccount.type},
                  {l:"Rating",        v:selectedAccount.rating},
                  {l:"Lead Source",   v:selectedAccount.lead_source},
                  {l:"Parent Account",v:selectedAccount.parent_name},
                  {l:"Salesforce ID", v:selectedAccount.id},
                ].map((f,i)=>(
                  <div key={i} style={css.fieldRow}>
                    <span style={css.fieldLabel}>{f.l}</span>
                    <span style={css.fieldVal}>{f.v||"—"}</span>
                  </div>
                ))}
              </div>

              <div style={css.card}>
                <h3 style={css.secTitle}>📞 Contact Information</h3>
                {[
                  {l:"Website",        v:selectedAccount.website, link:true},
                  {l:"Phone",          v:selectedAccount.phone},
                  {l:"Billing Address",v:selectedAccount.billing_address},
                  {l:"Sales Director", v:selectedAccount.owner_name},
                  {l:"Director Email", v:selectedAccount.owner_email},
                  {l:"Last Activity",  v:selectedAccount.last_activity},
                  {l:"Created Date",   v:(selectedAccount.created_date||"").slice(0,10)},
                ].map((f,i)=>(
                  <div key={i} style={css.fieldRow}>
                    <span style={css.fieldLabel}>{f.l}</span>
                    <span style={css.fieldVal}>
                      {f.link && f.v
                        ? <a href={`https://${f.v}`} target="_blank" rel="noreferrer" style={{color:"#F5A623"}}>{f.v}</a>
                        : (f.v||"—")}
                    </span>
                  </div>
                ))}
              </div>

              <div style={css.card}>
                <h3 style={css.secTitle}>💰 Financial & Scoring</h3>
                {[
                  {l:"Annual Revenue", v:selectedAccount.revenue_fmt,    color:"#047857"},
                  {l:"Employees",      v:selectedAccount.employees_fmt},
                  {l:"Prospect Score", v:selectedAccount.score!=null?`${selectedAccount.score}/100`:"N/A", color:"#b45309"},
                  {l:"Priority",       v:selectedAccount.priority,        color:priorityChip(selectedAccount.priority||"LOW").color},
                  {l:"Sales Potential",v:selectedAccount.sales_potential, color:"#1d4ed8"},
                ].map((f,i)=>(
                  <div key={i} style={css.fieldRow}>
                    <span style={css.fieldLabel}>{f.l}</span>
                    <span style={{...css.fieldVal,color:f.color||"#111827",fontWeight:"700"}}>{f.v||"—"}</span>
                  </div>
                ))}
              </div>

              <div style={css.card}>
                <h3 style={css.secTitle}>📝 Description</h3>
                <p style={{color:"#4b5563",lineHeight:"1.7",fontSize:"14px",margin:0}}>
                  {selectedAccount.description||wikiData?.summary||"No description available."}
                </p>
              </div>
            </div>

            {/* Lumen Services Card */}
            {selectedAccount && (
              <div style={{
                ...css.card,
                marginBottom: "20px"
              }}>
                <h3 style={css.secTitle}>
                  🔗 Lumen Services
                </h3>

                <div style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "20px"
                }}>
                  {/* Active Services */}
                  <div>
                    <h4 style={{
                      color: "#2e7d32",
                      margin: "0 0 12px 0",
                      fontSize: "14px"
                    }}>
                      ✅ Active Services (
                      {(selectedAccount.active_services
                        ||[]).length})
                    </h4>
                    {(selectedAccount.active_services
                      ||[]).length > 0 ? (
                      <div style={{
                        display:"flex",
                        flexWrap:"wrap",
                        gap:"8px"
                      }}>
                        {(selectedAccount.active_services
                          ||[]).map((svc, i) => (
                          <span key={i} style={{
                            backgroundColor: "#e8f5e9",
                            color: "#2e7d32",
                            border: "1px solid #2e7d32",
                            padding: "5px 12px",
                            borderRadius: "20px",
                            fontSize: "13px",
                            fontWeight: "bold"
                          }}>
                            ✅ {svc}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p style={{color:"#999",
                        fontSize:"14px"}}>
                        No active services found
                      </p>
                    )}
                  </div>

                  {/* Recommended Services */}
                  <div>
                    <h4 style={{
                      color: "#F47B5E",
                      margin: "0 0 12px 0",
                      fontSize: "14px"
                    }}>
                      🎯 Recommended Services (
                      {(selectedAccount.recommended_services
                        ||[]).length})
                    </h4>
                    {(selectedAccount.recommended_services
                      ||[]).length > 0 ? (
                      <div style={{
                        display:"flex",
                        flexWrap:"wrap",
                        gap:"8px"
                      }}>
                        {(selectedAccount.recommended_services
                          ||[]).map((svc, i) => (
                          <span key={i} style={{
                            backgroundColor: "#fff5f0",
                            color: "#F47B5E",
                            border: "1px solid #F47B5E",
                            padding: "5px 12px",
                            borderRadius: "20px",
                            fontSize: "13px",
                            fontWeight: "bold"
                          }}>
                            🎯 {svc}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <p style={{color:"#999",
                        fontSize:"14px"}}>
                        All recommended services active!
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div style={css.ctaBox}>
              <span style={{color:"#047857",fontWeight:"600"}}></span>
              <button style={css.smallBtn} onClick={()=>setTab("charts")}>View Charts →</button>
            </div>
          </>}
        </>}

        {/* ════════════ CHARTS TAB ════════════ */}
        {tab === "charts" && <>
          {!connected && (
            <div style={css.warnBox}>
              ⚠️ Load accounts first to see live charts.
              <button style={css.smallBtn} onClick={()=>setTab("accounts")}>Go to Accounts →</button>
            </div>
          )}
          <div style={css.card}>
            <h2 style={css.cardTitle}>📈 Revenue by Industry ($M)</h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={revenueByIndustry}>
                <CartesianGrid strokeDasharray="3 3"/>
                <XAxis dataKey="name" tick={{fontSize:11}}/>
                <YAxis/><Tooltip formatter={v=>`$${v}M`}/><Legend/>
                <Bar dataKey="revenue" fill="#F5A623" name="Revenue ($M)"/>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:"20px",marginBottom:"20px"}}>
            <div style={css.card}>
              <h2 style={css.cardTitle}>🏭 Industry Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={industryCount} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name,value})=>`${name}: ${value}`}>
                    {industryCount.map((_,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
                  </Pie>
                  <Tooltip/>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={css.card}>
              <h2 style={css.cardTitle}>⭐ Priority Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={priDist} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name,value})=>`${name}: ${value}`}>
                    {priDist.map((_,i)=><Cell key={i} fill={priDistColors[i]}/>)}
                  </Pie>
                  <Tooltip/>
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div style={css.card}>
            <h2 style={css.cardTitle}>👥 Employee Size Distribution</h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={empDist}>
                <CartesianGrid strokeDasharray="3 3"/>
                <XAxis dataKey="name"/><YAxis/><Tooltip/><Legend/>
                <Bar dataKey="count" fill="#F47B5E" name="Accounts"/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>}

        {/* ════════════ CHATBOT TAB ════════════ */}
        {tab === "chatbot" && (
          <div style={{
            display: "flex", flexDirection: "column",
            height: "calc(100vh - 160px)",
            backgroundColor: "#f9fafb",
            borderRadius: 14,
            overflow: "hidden",
            border: "1px solid #e5e7eb",
            boxShadow: "0 1px 6px rgba(0,0,0,0.07)",
          }}>

            {/* Chat header */}
            <div style={{
              background: "linear-gradient(135deg,#F5A623,#F47B5E)",
              padding: "16px 22px",
              display: "flex", alignItems: "center",
              justifyContent: "space-between",
              flexShrink: 0,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 42, height: 42, borderRadius: "50%",
                  background: "rgba(255,255,255,0.2)",
                  display: "flex", alignItems: "center",
                  justifyContent: "center", fontSize: 20,
                }}>🤖</div>
                <div>
                  <div style={{ color: "white", fontWeight: "700", fontSize: "15px" }}>
                    Lumen Sales AI Assistant
                  </div>
                  <div style={{ color: "rgba(255,255,255,0.82)", fontSize: "12px" }}>
                    Powered by Salesforce · Ask me anything about your accounts
                  </div>
                </div>
              </div>
              <div style={{
                background: "rgba(255,255,255,0.2)", color: "white",
                borderRadius: 20, padding: "4px 14px", fontSize: "12px",
                display: "flex", alignItems: "center", gap: 6,
              }}>
                <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e", display: "inline-block" }}/>
                Online
              </div>
            </div>

            {/* Messages area */}
            <div style={{
              flex: 1, overflowY: "auto",
              padding: "20px 20px 10px",
            }}>
              {chatMessages.map((msg, i) => (
                <div key={i} style={{
                  display: "flex",
                  flexDirection: msg.role === "user" ? "row-reverse" : "row",
                  gap: 10, marginBottom: 18,
                  alignItems: "flex-start",
                }}>
                  {/* Avatar */}
                  <div style={{
                    width: 34, height: 34, borderRadius: "50%", flexShrink: 0,
                    background: msg.role === "bot"
                      ? "linear-gradient(135deg,#F5A623,#F47B5E)"
                      : "#e5e7eb",
                    display: "flex", alignItems: "center",
                    justifyContent: "center", fontSize: 16,
                  }}>
                    {msg.role === "bot" ? "🤖" : "👤"}
                  </div>

                  <div style={{ maxWidth: "78%" }}>
                    {/* Bubble */}
                    <div style={{
                      backgroundColor: msg.role === "bot" ? "white" : "linear-gradient(135deg,#F5A623,#F47B5E)",
                      background: msg.role === "user"
                        ? "linear-gradient(135deg,#F5A623,#F47B5E)"
                        : "white",
                      color: msg.role === "user" ? "white" : "#1f2937",
                      borderRadius: msg.role === "bot"
                        ? "4px 18px 18px 18px"
                        : "18px 4px 18px 18px",
                      padding: "12px 16px",
                      boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                      border: msg.role === "bot" ? "1px solid #e5e7eb" : "none",
                      fontSize: "14px",
                      lineHeight: 1.6,
                    }}>
                      {msg.loading ? (
                        <span style={{ color: "#F5A623" }}>⏳ Thinking...</span>
                      ) : msg.role === "bot" ? (
                        <div dangerouslySetInnerHTML={{ __html: formatChatReply(msg.text) }}/>
                      ) : (
                        msg.text
                      )}
                    </div>

                    {/* Account cards under bot message */}
                    {msg.accounts && msg.accounts.length > 0 && (
                      <div style={{ marginTop: 10 }}>
                        {msg.accounts.map((acc, j) => (
                          <ChatAccountCard key={j} account={acc}/>
                        ))}
                      </div>
                    )}

                    {/* Tip */}
                    {msg.tip && (
                      <div style={{
                        marginTop: 8, padding: "6px 12px",
                        background: "#fff7ed", borderRadius: 8,
                        fontSize: "13px", color: "#c2410c",
                        border: "1px solid #fed7aa",
                      }}>
                        💡 {msg.tip}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Suggestion chips — show only at start */}
              {showSuggestions && (
                <div style={{ marginBottom: 12, marginLeft: 44 }}>
                  <p style={{ color: "#9ca3af", fontSize: "12px", margin: "0 0 8px" }}>
                    Try asking:
                  </p>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {CHAT_SUGGESTIONS.slice(0, 8).map((s, i) => (
                      <button key={i}
                        style={{
                          background: "#fff7ed", color: "#c2410c",
                          border: "1px solid #fed7aa",
                          padding: "5px 12px", borderRadius: 20,
                          cursor: "pointer", fontSize: "12px",
                          fontWeight: "600",
                        }}
                        onMouseEnter={e => { e.target.style.background = "#F5A623"; e.target.style.color = "white"; }}
                        onMouseLeave={e => { e.target.style.background = "#fff7ed"; e.target.style.color = "#c2410c"; }}
                        onClick={() => sendChat(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div ref={chatBottomRef}/>
            </div>

            {/* Input row */}
            <div style={{
              backgroundColor: "white",
              borderTop: "1px solid #e5e7eb",
              padding: "12px 16px",
              flexShrink: 0,
            }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                {/* Suggestions toggle */}
                <button
                  title="Show example questions"
                  style={{
                    width: 38, height: 38, borderRadius: "50%", flexShrink: 0,
                    background: "linear-gradient(135deg,#F5A623,#F47B5E)",
                    border: "none", color: "white", fontSize: 16,
                    cursor: "pointer", display: "flex",
                    alignItems: "center", justifyContent: "center",
                  }}
                  onClick={() => setShowSuggestions(s => !s)}
                >
                  💡
                </button>

                <input
                  ref={chatInputRef}
                  style={{
                    flex: 1, padding: "10px 16px",
                    borderRadius: 25,
                    border: "1.5px solid #e5e7eb",
                    fontSize: "14px", outline: "none",
                    background: "#fafafa",
                  }}
                  placeholder="Ask about your accounts... (e.g. 'Which companies to target for cloud?')"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={handleChatKey}
                  disabled={chatLoading}
                />

                <button
                  style={{
                    width: 42, height: 42, borderRadius: "50%", flexShrink: 0,
                    background: chatLoading || !chatInput.trim()
                      ? "#d1d5db"
                      : "linear-gradient(135deg,#F5A623,#F47B5E)",
                    border: "none", color: "white", fontSize: "16px",
                    cursor: chatLoading || !chatInput.trim() ? "not-allowed" : "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center",
                  }}
                  onClick={() => sendChat()}
                  disabled={chatLoading || !chatInput.trim()}
                >
                  {chatLoading ? "⏳" : "➤"}
                </button>
              </div>
              <div style={{ textAlign: "center", fontSize: "11px", color: "#9ca3af", marginTop: 6 }}>
                Lumen Sales AI · Salesforce CRM Data · Press Enter to send
              </div>
            </div>
          </div>
        )}

        {/* ════════════ WEEKLY TARGETS TAB ════════════ */}
        {tab === "weekly" && (
          <>
            <WeeklyTargets />
            <div style={{display:"flex",justifyContent:"space-between",padding:"0 16px 24px"}}>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px",background:"linear-gradient(135deg,#6b7280,#4b5563)"}} onClick={()=>setTab("prospects")}>← Back to Top Prospects</button>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px"}} onClick={()=>setTab("travel")}>View Travel Planner →</button>
            </div>
          </>
        )}

        {/* ════════════ TRAVEL PLANNER TAB ════════════ */}
        {tab === "travel" && (
          <>
            <TravelPlanner />
            <div style={{display:"flex",justifyContent:"space-between",padding:"0 16px 24px"}}>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px",background:"linear-gradient(135deg,#6b7280,#4b5563)"}} onClick={()=>setTab("weekly")}>← Back to Weekly Targets</button>
              <button style={{...css.smallBtn,fontSize:"14px",padding:"10px 22px"}} onClick={()=>setTab("dashboard")}>View Dashboard →</button>
            </div>
          </>
        )}

      </main>

      {/* ── FLOATING COPILOT BUTTON ── */}
      <button style={css.fab} onClick={()=>setCopilotOpen(o=>!o)}>
        {copilotOpen ? "✕ Close" : "🤖 Ask AI"}
      </button>

      {copilotOpen && (
        <div style={css.copWin}>
          <div style={css.copHead}>
            <span>🤖 Lumen Sales Assistant</span>
            <button style={{background:"none",border:"none",color:"white",fontSize:"17px",cursor:"pointer"}}
              onClick={()=>setCopilotOpen(false)}>✕</button>
          </div>
          <div style={{padding:"20px"}}>
            <p style={{color:"#374151",marginBottom:"12px"}}>Type a company name and press Enter:</p>
            <input
              style={css.input}
              placeholder="e.g. Wells Fargo, Microsoft…"
              value={copilotInput}
              onChange={e=>setCopilotInput(e.target.value)}
              onKeyDown={e=>{
                if(e.key==="Enter" && copilotInput.trim()){
                  const name = copilotInput.trim();
                  setCompanyInput(name);
                  getAiInsight(name, accounts.find(a=>(a.name||"").toLowerCase()===name.toLowerCase()));
                  setTab("ai");
                  setCopilotOpen(false);
                  setCopilotInput("");
                }
              }}
            />
            <p style={{color:"#9ca3af",fontSize:"13px",marginTop:"8px",textAlign:"center"}}>
              Press Enter to get Salesforce + Wikipedia insights
            </p>
            <div style={{marginTop:"12px",borderTop:"1px solid #e5e7eb",paddingTop:"12px"}}>
              <p style={{color:"#374151",fontSize:"13px",marginBottom:"8px",fontWeight:"600"}}>
                Or ask the chatbot:
              </p>
              <button
                style={{...css.btn,width:"100%",textAlign:"center"}}
                onClick={()=>{ setCopilotOpen(false); setTab("chatbot"); }}
              >
                💬 Open Full Chatbot
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

const css = {
  root:        {fontFamily:"'Segoe UI',-apple-system,BlinkMacSystemFont,sans-serif",minHeight:"100vh",backgroundColor:"#f9fafb",fontSize:"14px",lineHeight:"1.6"},
  header:      {background:"linear-gradient(135deg,#F5A623 0%,#F47B5E 100%)",color:"white",padding:"18px 48px",display:"flex",alignItems:"center",justifyContent:"space-between",flexWrap:"wrap",gap:"16px",boxShadow:"0 2px 12px rgba(0,0,0,0.12)",width:"100%",boxSizing:"border-box"},
  logo:        {margin:0,fontSize:"22px",fontWeight:"800",letterSpacing:"-0.3px"},
  logoSub:     {margin:"4px 0 0",opacity:.85,fontSize:"13px"},
  nav:         {display:"flex",gap:"8px",flexWrap:"wrap"},
  navBtn:      {background:"rgba(255,255,255,0.15)",color:"white",border:"1px solid rgba(255,255,255,0.3)",padding:"8px 18px",borderRadius:"20px",cursor:"pointer",fontSize:"13px",fontWeight:"500",transition:"all .15s"},
  navActive:   {background:"white",color:"#F5A623",border:"none",padding:"8px 18px",borderRadius:"20px",cursor:"pointer",fontWeight:"700",fontSize:"13px",boxShadow:"0 2px 8px rgba(0,0,0,0.1)"},
  main:        {width:"100%",maxWidth:"1600px",margin:"0 auto",padding:"28px 48px",boxSizing:"border-box"},
  card:        {backgroundColor:"white",borderRadius:"12px",padding:"24px 28px",marginBottom:"20px",boxShadow:"0 1px 4px rgba(0,0,0,0.06)",border:"1px solid #e5e7eb"},
  cardTitle:   {margin:"0 0 12px",fontSize:"16px",fontWeight:"700",color:"#111827"},
  btn:         {background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",border:"none",padding:"10px 24px",borderRadius:"8px",fontSize:"14px",cursor:"pointer",fontWeight:"600",transition:"opacity .15s"},
  btnDisabled: {background:"#d1d5db",color:"white",border:"none",padding:"10px 24px",borderRadius:"8px",fontSize:"14px",cursor:"not-allowed"},
  smallBtn:    {background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",border:"none",padding:"8px 18px",borderRadius:"6px",cursor:"pointer",fontSize:"13px",fontWeight:"600",marginLeft:"8px"},
  aiBtn:       {background:"#f0fdf4",color:"#15803d",border:"1px solid #86efac",padding:"6px 14px",borderRadius:"14px",cursor:"pointer",fontSize:"13px",fontWeight:"600",transition:"all .15s"},
  ok:          {color:"#047857",marginTop:"12px",fontWeight:"600",fontSize:"14px"},
  input:       {width:"100%",padding:"10px 14px",borderRadius:"8px",border:"1.5px solid #e5e7eb",fontSize:"14px",outline:"none",boxSizing:"border-box",transition:"border .2s"},
  filterRow:   {display:"flex",alignItems:"center",gap:"14px",flexWrap:"wrap"},
  chipRow:     {display:"flex",gap:"6px"},
  chip:        {padding:"6px 14px",borderRadius:"20px",border:"1px solid #e5e7eb",background:"white",cursor:"pointer",fontSize:"13px",color:"#374151",transition:"all .15s"},
  chipActive:  {padding:"6px 14px",borderRadius:"20px",border:"none",background:"linear-gradient(135deg,#F5A623,#F47B5E)",cursor:"pointer",fontSize:"13px",color:"white",fontWeight:"600"},
  searchRow:   {display:"flex",gap:"12px",marginBottom:"20px",alignItems:"center"},
  table:       {width:"100%",borderCollapse:"collapse",fontSize:"13px"},
  th:          {padding:"12px 16px",textAlign:"left",fontWeight:"700",background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",fontSize:"13px",whiteSpace:"nowrap"},
  td:          {padding:"12px 16px",borderBottom:"1px solid #f3f4f6",verticalAlign:"middle",fontSize:"13px"},
  banner:      {background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",padding:"20px 28px",borderRadius:"12px",marginBottom:"20px",display:"flex",alignItems:"center",justifyContent:"space-between"},
  actionBox:   {background:"#eff6ff",border:"1px solid #bfdbfe",borderRadius:"10px",padding:"14px 18px",marginBottom:"20px",fontSize:"14px",color:"#1e40af"},
  insightGrid: {display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(240px,1fr))",gap:"16px",marginBottom:"20px"},
  insightCard: {background:"#fafafa",borderRadius:"10px",padding:"18px",border:"1px solid #e5e7eb",borderTop:"3px solid #F5A623"},
  insightLabel:{fontSize:"12px",color:"#6b7280",fontWeight:"700",marginBottom:"8px",textTransform:"uppercase",letterSpacing:"0.3px"},
  insightVal:  {fontSize:"14px",fontWeight:"500",color:"#1f2937",lineHeight:"1.6"},
  wikiCard:    {background:"#f5f3ff",border:"1px solid #ddd6fe",borderLeft:"4px solid #8b5cf6",borderRadius:"12px",padding:"24px",marginBottom:"20px"},
  wikiGrid:    {display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:"12px",marginBottom:"16px"},
  wikiFactCard:{background:"white",borderRadius:"8px",padding:"12px",boxShadow:"0 1px 3px rgba(0,0,0,0.06)"},
  wikiLink:    {color:"#6d28d9",fontWeight:"700",fontSize:"14px",textDecoration:"none",display:"inline-block",marginTop:"10px"},
  tagRow:      {display:"flex",flexWrap:"wrap",gap:"8px",marginTop:"10px"},
  tag:         {background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",padding:"5px 14px",borderRadius:"20px",fontSize:"13px",fontWeight:"600"},
  loadBox:     {textAlign:"center",padding:"32px",color:"#F5A623",fontSize:"15px",fontWeight:"600"},
  placeholder: {textAlign:"center",padding:"40px 20px",color:"#6b7280"},
  ctaBox:      {display:"flex",alignItems:"center",gap:"12px",background:"#f0fdf4",border:"1px solid #bbf7d0",borderRadius:"10px",padding:"14px 18px",marginTop:"16px"},
  warnBox:     {background:"#fffbeb",border:"1px solid #fde68a",borderRadius:"10px",padding:"14px 18px",marginBottom:"16px",display:"flex",alignItems:"center",gap:"8px",fontSize:"14px",color:"#92400e"},
  featGrid:    {display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:"12px",maxWidth:"700px",margin:"0 auto"},
  featCard:    {background:"#fff7ed",border:"1px solid #fed7aa",borderRadius:"10px",padding:"14px",fontSize:"14px",color:"#9a3412",fontWeight:"600",textAlign:"center"},
  kpiGrid:     {display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(280px,1fr))",gap:"16px",marginBottom:"20px"},
  kpiCard:     {background:"white",borderRadius:"12px",padding:"20px",textAlign:"center",border:"1px solid #e5e7eb",borderTop:"4px solid #F5A623"},
  kpiLabel:    {fontSize:"12px",color:"#6b7280",fontWeight:"700",marginBottom:"8px",textTransform:"uppercase",letterSpacing:"0.3px"},
  kpiVal:      {fontSize:"16px",fontWeight:"700",wordBreak:"break-word",lineHeight:"1.4"},
  secTitle:    {color:"#F47B5E",borderBottom:"1px solid #fee2e2",paddingBottom:"8px",marginBottom:"12px",marginTop:0,fontSize:"15px",fontWeight:"700"},
  fieldRow:    {display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:"1px solid #f3f4f6",gap:"12px",alignItems:"flex-start"},
  fieldLabel:  {fontSize:"13px",color:"#6b7280",fontWeight:"600",minWidth:"130px",flexShrink:0},
  fieldVal:    {fontSize:"14px",color:"#111827",fontWeight:"500",textAlign:"right",wordBreak:"break-word"},
  fab:         {position:"fixed",bottom:"32px",right:"32px",background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",padding:"14px 24px",borderRadius:"50px",cursor:"pointer",fontSize:"14px",fontWeight:"700",boxShadow:"0 4px 16px rgba(0,0,0,0.2)",border:"none",zIndex:1000},
  copWin:      {position:"fixed",bottom:"100px",right:"32px",width:"380px",background:"white",borderRadius:"16px",boxShadow:"0 8px 32px rgba(0,0,0,0.18)",zIndex:1000,overflow:"hidden",border:"1px solid #e5e7eb"},
  copHead:     {background:"linear-gradient(135deg,#F5A623,#F47B5E)",color:"white",padding:"14px 20px",display:"flex",justifyContent:"space-between",alignItems:"center",fontWeight:"700",fontSize:"14px"},
};
