import { useState } from "react";
import { AlertTriangle, CheckCircle2, FileText, Languages, Printer, ShieldCheck, Volume2 } from "lucide-react";

const API = (import.meta as any).env?.VITE_API_URL || "http://localhost:8001";

const DEMO = `Discharge Summary
Tab Metformin 500 mg BD pc x 30 days
Tab Amlodipine 5 mg OD x 30 days
Review OPD 26/10/2026
Warning signs: severe dizziness, chest pain
Diet: low salt diet`;

type Result = {
  plan: any;
  verification: any;
  rendered: any;
};

export default function App() {
  const [summary, setSummary] = useState(DEMO);
  const [result, setResult] = useState<Result | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setBusy(true); setError("");
    try {
      const r = await fetch(`${API}/api/generate`, {
        method: "POST", headers: {"Content-Type":"application/json"},
        body: JSON.stringify({summary})
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e:any) {
      setError(e.message || "Unable to connect to CareBridge API.");
    } finally { setBusy(false); }
  }

  async function downloadPdf() {
    const r = await fetch(`${API}/api/pdf`, {
      method: "POST", headers: {"Content-Type":"application/json"},
      body: JSON.stringify({summary})
    });
    if (!r.ok) { setError(await r.text()); return; }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "carebridge-fridge-sheet.pdf"; a.click();
    URL.revokeObjectURL(url);
  }

  function speak(text:string) {
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  }

  return <div className="app">
    <header className="topbar">
      <div className="brand"><div className="logo">CB</div><div><b>CareBridge</b><span>Verified discharge care plans</span></div></div>
      <div className="status"><span className="dot"/> Safety-first prototype</div>
    </header>

    <main>
      <section className="hero">
        <div>
          <p className="eyebrow">HEALTHCARE · H2</p>
          <h1>From discharge summary<br/><em>to a plan families can follow.</em></h1>
          <p className="lead">Extract facts. Render reviewed language. Verify every medicine and date. Block anything uncertain.</p>
        </div>
        <div className="promise">
          <div><strong>0</strong><span>dropped or altered<br/>medicines</span></div>
          <div><strong>2</strong><span>languages<br/>English + Telugu</span></div>
          <div><strong>1</strong><span>page<br/>fridge sheet</span></div>
        </div>
      </section>

      <section className="workspace">
        <div className="panel source">
          <div className="panel-head"><div><span className="step">01</span><b>Discharge summary</b></div><button onClick={()=>setSummary(DEMO)}>Load demo</button></div>
          <textarea value={summary} onChange={e=>setSummary(e.target.value)} />
          <button className="primary" disabled={busy} onClick={generate}>{busy ? "Checking…" : "Generate & verify plan"}</button>
          {error && <div className="error">{error}</div>}
        </div>

        <div className="panel result">
          <div className="panel-head"><div><span className="step">02</span><b>Verification</b></div>
            {result && <span className={result.verification.passed ? "badge pass":"badge block"}>{result.verification.passed ? "PASS":"BLOCKED"}</span>}
          </div>
          {!result ? <div className="empty"><ShieldCheck size={38}/><b>Nothing released yet</b><span>CareBridge will extract and verify the source before rendering patient-facing text.</span></div> :
          <div>
            <div className="metrics">
              <Metric icon={<CheckCircle2/>} label="Fields checked" value={result.verification.checked_fields}/>
              <Metric icon={<ShieldCheck/>} label="Mismatches" value={result.verification.mismatch_count}/>
              <Metric icon={<FileText/>} label="Reading grade" value={result.rendered.readability_grade}/>
            </div>
            {result.verification.issues.length > 0 && <div className="issues">
              {result.verification.issues.map((x:any,i:number)=><div className="issue" key={i}><AlertTriangle size={16}/><span>{x.message}</span></div>)}
            </div>}
            <div className="plan-grid">
              <Plan title="English" icon={<Languages/>} text={result.rendered.english} />
              <Plan title="తెలుగు" icon={<Languages/>} text={result.rendered.telugu} />
            </div>
            <div className="actions">
              <button onClick={()=>speak(result.rendered.english)}><Volume2 size={16}/> English audio</button>
              <button onClick={()=>speak(result.rendered.telugu)}><Volume2 size={16}/> Telugu audio</button>
              <button disabled={!result.verification.passed} onClick={downloadPdf}><Printer size={16}/> Fridge sheet</button>
            </div>
          </div>}
        </div>
      </section>

      <section className="flow">
        <div><b>Extract</b><span>Fixed schema</span></div><i>→</i>
        <div><b>Ground</b><span>Source spans</span></div><i>→</i>
        <div><b>Render</b><span>Locked templates</span></div><i>→</i>
        <div><b>Round-trip</b><span>Mismatch blocks</span></div><i>→</i>
        <div><b>Nurse review</b><span>Only when needed</span></div>
      </section>

      <footer>CareBridge is a hackathon prototype. Patient-facing output requires authorized clinical review.</footer>
    </main>
  </div>
}

function Metric({icon,label,value}:{icon:any,label:string,value:any}) {
  return <div className="metric"><span>{icon}</span><small>{label}</small><strong>{value}</strong></div>
}
function Plan({title,icon,text}:{title:string,icon:any,text:string}) {
  return <div className="plan"><div className="plan-title">{icon}<b>{title}</b></div><pre>{text}</pre></div>
}