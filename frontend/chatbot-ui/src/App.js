import { useState, useRef, useEffect } from "react";

const API = "http://localhost:8000";

const SUGGESTIONS = [
  "Show me top 10 prospects",
  "Show HIGH priority accounts",
  "Give me a summary",
  "Which tech companies should I target?",
  "Accounts in Texas",
  "Revenue over $100M",
  "Who haven't I contacted in 6 months?",
  "Show existing customers",
  "Tell me about Wells Fargo",
];

function formatReply(text) {
  return text
    .split("\n")
    .map((line, i) => {
      line = line
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/^•\s/, "")
        .replace(/^\d+\.\s/, "");
      if (line.startsWith("🎯") || line.startsWith("📊") ||
          line.startsWith("⭐") || line.startsWith("🏭") ||
          line.startsWith("💰") || line.startsWith("📍") ||
          line.startsWith("⏰") || line.startsWith("🤝") ||
          line.startsWith("🔍") || line.startsWith("🤖") ||
          line.startsWith("👔") || line.startsWith("🏢")) {
        return `<div key=${i} style="font-size:1rem;font-weight:700;margin-bottom:10px;color:#1f2937">${line}</div>`;
      }
      if (line.trim() === "") return `<br key=${i}/>`;
      return `<div key=${i} style="padding:4px 0;border-bottom:1px solid #f3f4f6;font-size:0.88rem;color:#374151">${line}</div>`;
    })
    .join("");
}

function AccountCard({ account }) {
  const priColor = {
    HIGH: {bg:"#fde8e8",border:"#e53935",
           text:"#b71c1c"},
    MEDIUM: {bg:"#fff8e1",border:"#F5A623",
             text:"#e65100"},
    LOW: {bg:"#e8f5e9",border:"#43a047",
          text:"#1b5e20"},
  }[account.priority] || {
    bg:"#f5f5f5",border:"#999",text:"#333"};

  return (
    <div style={{
      border:`1px solid ${priColor.border}`,
      borderLeft:`4px solid ${priColor.border}`,
      borderRadius:10,
      padding:"12px 14px",
      marginBottom:10,
      backgroundColor:priColor.bg,
      fontSize:"0.88rem",
    }}>
      <div style={{
        fontWeight:"bold",
        fontSize:"0.95rem",
        color:"#1a1a1a",
        marginBottom:4
      }}>
        🏢 {account.name}
      </div>

      <div style={{
        display:"flex",flexWrap:"wrap",
        gap:8,color:"#555"
      }}>
        <span>💰 {account.revenue_fmt||"N/A"}</span>
        <span>👥 {account.employees_fmt||"N/A"}</span>
        <span>🏭 {account.industry||"N/A"}</span>
      </div>

      <div style={{
        display:"flex",flexWrap:"wrap",
        gap:8,marginTop:4,color:"#555"
      }}>
        <span>📍 {[
          account.billing_city,
          account.billing_state
        ].filter(Boolean).join(", ")||"N/A"}</span>
        <span style={{
          backgroundColor:priColor.border,
          color:"white",borderRadius:10,
          padding:"1px 8px",fontSize:"0.78rem",
          fontWeight:"bold",
        }}>
          {account.priority||"N/A"}
        </span>
        <span style={{
          color:"#F5A623",fontWeight:"bold"
        }}>
          Score: {account.score}/100
        </span>
      </div>

      {/* ── LUMEN SERVICES ── */}
      {account.active_services &&
       account.active_services.length > 0 && (
        <div style={{marginTop:8,borderTop:"1px solid #ddd",paddingTop:8}}>
          <div style={{
            fontSize:"0.85rem",
            color:"#2e7d32",
            fontWeight:"bold",
            marginBottom:8,
            display:"flex",
            alignItems:"center",
            gap:6
          }}>
            🔗 Lumen Services ({account.active_services.length})
          </div>
          <div style={{
            display:"flex",
            flexWrap:"wrap",gap:6
          }}>
            {account.active_services.map(
              (svc,i) => (
              <span key={i} style={{
                backgroundColor:"#c8e6c9",
                color:"#1b5e20",
                border:"2px solid #2e7d32",
                borderRadius:12,
                padding:"4px 12px",
                fontSize:"0.78rem",
                fontWeight:"bold"
              }}>
                {svc}
              </span>
            ))}
          </div>
        </div>
      )}

      {account.recommended_services &&
       account.recommended_services.length > 0 && (
        <div style={{marginTop:6}}>
          <div style={{
            fontSize:"0.78rem",
            color:"#F47B5E",
            fontWeight:"bold",
            marginBottom:4
          }}>
            🎯 Recommended:
          </div>
          <div style={{
            display:"flex",
            flexWrap:"wrap",gap:4
          }}>
            {account.recommended_services.map(
              (svc,i) => (
              <span key={i} style={{
                backgroundColor:"#fff5f0",
                color:"#F47B5E",
                border:"1px solid #F47B5E",
                borderRadius:10,
                padding:"2px 8px",
                fontSize:"0.75rem",
                fontWeight:"bold"
              }}>
                {svc}
              </span>
            ))}
          </div>
        </div>
      )}

      {account.recommended_action && (
        <div style={{
          marginTop:6,color:"#1565c0",
          fontSize:"0.82rem"
        }}>
          🚀 {account.recommended_action}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [messages, setMessages]   = useState([
    {
      role: "bot",
      text: "👋 Hi! I'm your **Lumen Sales Assistant**.\n\nAsk me anything about your Salesforce accounts!\n\n🤖 Try: 'Show me top 10 prospects' or 'Give me a summary'",
    },
  ]);
  const [input,    setInput]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const bottomRef               = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    const msg = (text || input).trim();
    if (!msg) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: msg }]);
    setLoading(true);
    try {
      const res  = await fetch(`${API}/chat`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "bot", text: data.reply || "No response" }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: "bot",
        text: "❌ Cannot connect to backend. Make sure it's running on port 8000.",
      }]);
    }
    setLoading(false);
  };

  return (
    <div style={s.root}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.headerLeft}>
          <div style={s.avatar}>🤖</div>
          <div>
            <div style={s.headerTitle}>Lumen Sales Assistant</div>
            <div style={s.headerSub}>Powered by Salesforce · Always Online</div>
          </div>
        </div>
        <div style={s.onlineDot}/>
      </div>

      {/* Messages */}
      <div style={s.messages}>
        {messages.map((m, i) => (
          <div key={i} style={{
            display:       "flex",
            justifyContent: m.role === "user" ? "flex-end" : "flex-start",
            marginBottom:  "14px",
            alignItems:    "flex-end",
            gap:           "8px",
          }}>
            {m.role === "bot" && (
              <div style={s.botAvatar}>🤖</div>
            )}
            <div style={m.role === "user" ? s.userBubble : s.botBubble}>
              {m.role === "bot"
                ? <div dangerouslySetInnerHTML={{ __html: formatReply(m.text) }}/>
                : m.text
              }
            </div>
            {m.role === "user" && (
              <div style={s.userAvatar}>👤</div>
            )}
          </div>
        ))}

        {loading && (
          <div style={{ display:"flex", alignItems:"flex-end", gap:"8px", marginBottom:"14px" }}>
            <div style={s.botAvatar}>🤖</div>
            <div style={s.botBubble}>
              <div style={s.typing}>
                <span/><span/><span/>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef}/>
      </div>

      {/* Suggestions */}
      <div style={s.suggestions}>
        {SUGGESTIONS.slice(0,4).map((sg, i) => (
          <button key={i} style={s.suggBtn} onClick={() => send(sg)}>
            {sg}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={s.inputRow}>
        <input
          style={s.input}
          placeholder="Ask about your accounts..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !loading && send()}
          disabled={loading}
        />
        <button
          style={loading || !input.trim() ? s.sendDisabled : s.send}
          onClick={() => send()}
          disabled={loading || !input.trim()}
        >
          ➤
        </button>
      </div>

      <style>{`
        @keyframes bounce {
          0%,80%,100% { transform: scale(0); }
          40%          { transform: scale(1); }
        }
      `}</style>
    </div>
  );
}

const s = {
  root:        { display:"flex", flexDirection:"column", height:"100vh", backgroundColor:"#f9fafb", fontFamily:"'Segoe UI',Arial,sans-serif", maxWidth:"800px", margin:"0 auto" },
  header:      { background:"linear-gradient(135deg,#F5A623,#F47B5E)", padding:"16px 20px", display:"flex", alignItems:"center", justifyContent:"space-between", boxShadow:"0 2px 8px rgba(0,0,0,0.12)" },
  headerLeft:  { display:"flex", alignItems:"center", gap:"12px" },
  avatar:      { width:"44px", height:"44px", borderRadius:"50%", background:"rgba(255,255,255,0.2)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1.4rem" },
  headerTitle: { color:"white", fontWeight:"700", fontSize:"1rem" },
  headerSub:   { color:"rgba(255,255,255,0.8)", fontSize:"0.75rem", marginTop:"2px" },
  onlineDot:   { width:"10px", height:"10px", borderRadius:"50%", background:"#22c55e", boxShadow:"0 0 0 2px white" },
  messages:    { flex:1, overflowY:"auto", padding:"20px 16px" },
  botAvatar:   { width:"32px", height:"32px", borderRadius:"50%", background:"linear-gradient(135deg,#F5A623,#F47B5E)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1rem", flexShrink:0 },
  userAvatar:  { width:"32px", height:"32px", borderRadius:"50%", background:"#e5e7eb", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"1rem", flexShrink:0 },
  botBubble:   { background:"white", borderRadius:"18px 18px 18px 4px", padding:"14px 16px", maxWidth:"85%", boxShadow:"0 1px 4px rgba(0,0,0,0.08)", border:"1px solid #e5e7eb" },
  userBubble:  { background:"linear-gradient(135deg,#F5A623,#F47B5E)", color:"white", borderRadius:"18px 18px 4px 18px", padding:"12px 16px", maxWidth:"75%", fontSize:"0.9rem", fontWeight:"500" },
  suggestions: { display:"flex", gap:"8px", padding:"10px 16px", overflowX:"auto", borderTop:"1px solid #e5e7eb", background:"white" },
  suggBtn:     { background:"#fff7ed", color:"#c2410c", border:"1px solid #fed7aa", padding:"6px 12px", borderRadius:"20px", cursor:"pointer", fontSize:"0.78rem", fontWeight:"600", whiteSpace:"nowrap" },
  inputRow:    { display:"flex", gap:"10px", padding:"14px 16px", background:"white", borderTop:"1px solid #e5e7eb", boxShadow:"0 -2px 8px rgba(0,0,0,0.06)" },
  input:       { flex:1, padding:"12px 16px", borderRadius:"25px", border:"1.5px solid #e5e7eb", fontSize:"0.95rem", outline:"none", background:"#fafafa" },
  send:        { width:"46px", height:"46px", borderRadius:"50%", background:"linear-gradient(135deg,#F5A623,#F47B5E)", color:"white", border:"none", cursor:"pointer", fontSize:"1.1rem", display:"flex", alignItems:"center", justifyContent:"center" },
  sendDisabled:{ width:"46px", height:"46px", borderRadius:"50%", background:"#d1d5db", color:"white", border:"none", cursor:"not-allowed", fontSize:"1.1rem", display:"flex", alignItems:"center", justifyContent:"center" },
  typing:      { display:"flex", gap:"4px", padding:"4px 0", "& span":{ width:"8px", height:"8px", borderRadius:"50%", background:"#9ca3af", animation:"bounce 1.4s infinite ease-in-out" } },
};