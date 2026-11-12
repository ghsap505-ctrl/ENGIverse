import { useEffect, useState } from 'react'
import { Activity, BookOpen, BrainCircuit, Boxes, FlaskConical, GraduationCap, Network, Sparkles } from 'lucide-react'
import { getHealth } from './lib/api'

const modules = [
  { icon: BookOpen, title: 'Course Intelligence', desc: 'Organize courses, documents, concepts, and references.' },
  { icon: BrainCircuit, title: 'AI Learning Tutor', desc: 'Learn step by step with explanations adapted to your level.' },
  { icon: FlaskConical, title: 'Simulation Studio', desc: 'Explore scientific and engineering systems through models.' },
  { icon: Network, title: 'Knowledge Graph', desc: 'Connect concepts and reveal prerequisite relationships.' },
]

export default function App() {
  const [apiStatus, setApiStatus] = useState('Checking API…')
  useEffect(() => { getHealth().then(() => setApiStatus('API connected')).catch(() => setApiStatus('API unavailable')) }, [])

  return <main className="shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Boxes size={22}/></div><div><b>ENGIverse</b><small>ENGINEERING INTELLIGENCE</small></div></div>
      <div className="nav-label">WORKSPACE</div>
      <a className="nav active"><Activity size={17}/> Overview</a>
      <a className="nav"><BookOpen size={17}/> My courses</a>
      <a className="nav"><BrainCircuit size={17}/> AI tutor</a>
      <a className="nav"><FlaskConical size={17}/> Simulations</a>
      <div className="sidebar-bottom"><span className="status-dot"/><span>{apiStatus}</span></div>
    </aside>
    <section className="content">
      <header><div><span className="eyebrow">UNIVERSAL ENGINEERING LEARNING</span><h1>Build understanding.<br/><em>Engineer what’s next.</em></h1><p className="lead">One intelligent workspace for learning, exploring, and solving engineering problems.</p></div><div className="header-icon"><GraduationCap size={30}/></div></header>
      <div className="section-head"><div><span className="eyebrow">YOUR WORKSPACE</span><h2>Learning environment</h2></div><span className="version">FOUNDATION · v0.1.2</span></div>
      <div className="module-grid">{modules.map(({icon: Icon,title,desc},i)=><article className="module" key={title}><div className="module-top"><div className="module-icon"><Icon size={20}/></div><span>0{i+1}</span></div><h3>{title}</h3><p>{desc}</p><div className="module-foot">FOUNDATION MODULE <span>↗</span></div></article>)}</div>
      <div className="callout"><div className="spark"><Sparkles size={19}/></div><div><b>A platform designed to grow with your studies</b><p>Start by creating a course and adding your learning materials. More intelligent tools will be introduced incrementally.</p></div></div>
      <footer>ENGIverse <span>·</span> A modular engineering learning ecosystem</footer>
    </section>
  </main>
}
