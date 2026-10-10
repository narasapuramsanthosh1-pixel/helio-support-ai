import { Activity, ArrowRight, Bot, CheckCircle2, Database, FileText, Gauge, Headphones, MessageSquareText, ShieldCheck, Sparkles, UploadCloud } from 'lucide-react';
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

const documentActivity = [
  { name: 'Mon', indexed: 8 },
  { name: 'Tue', indexed: 12 },
  { name: 'Wed', indexed: 9 },
  { name: 'Thu', indexed: 15 },
  { name: 'Fri', indexed: 18 },
  { name: 'Sat', indexed: 10 },
  { name: 'Sun', indexed: 14 },
];

const questionActivity = [
  { name: 'Mon', questions: 22 },
  { name: 'Tue', questions: 35 },
  { name: 'Wed', questions: 28 },
  { name: 'Thu', questions: 48 },
  { name: 'Fri', questions: 62 },
  { name: 'Sat', questions: 41 },
  { name: 'Sun', questions: 55 },
];

const metrics = [
  { label: 'Total indexed documents', value: '0', icon: FileText },
  { label: 'Total indexed chunks', value: '0', icon: Database },
  { label: 'Questions answered', value: '0', icon: MessageSquareText },
  { label: 'Grounded-answer rate', value: '0%', icon: ShieldCheck },
];

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-indigo-500/15 p-2 text-indigo-300 ring-1 ring-indigo-400/30">
              <Sparkles size={18} />
            </div>
            <div>
              <p className="text-lg font-semibold tracking-tight">Helio Support AI</p>
            </div>
          </div>
          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
            <a href="#overview" className="transition hover:text-white">Overview</a>
            <a href="#assistant" className="transition hover:text-white">Assistant</a>
            <a href="#knowledge-base" className="transition hover:text-white">Knowledge base</a>
            <a href="#models" className="transition hover:text-white">Models</a>
          </nav>
          <button className="rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm font-medium text-slate-100 transition hover:border-slate-500">
            Open AI Assistant
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        <section id="overview" className="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-900">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(99,102,241,0.18),transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(45,212,191,0.18),transparent_32%)]" />
          <div className="relative grid gap-8 px-6 py-8 md:grid-cols-[1.3fr_0.7fr] md:px-8 lg:px-10">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-200">
                <Bot size={14} />
                Trusted support intelligence
              </div>
              <div>
                <h1 className="max-w-xl text-4xl font-semibold tracking-tight text-white md:text-5xl">
                  Answers that help. Support that scales.
                </h1>
                <p className="mt-4 max-w-xl text-base text-slate-300 md:text-lg">
                  Connect your knowledge base to AI and deliver clear, evidence-grounded customer support.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                {['Open AI Assistant', 'Upload Documents', 'Manage Models'].map((label) => (
                  <button
                    key={label}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition ${label === 'Open AI Assistant' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/25 hover:bg-indigo-400' : 'border border-slate-700 bg-slate-900 text-slate-100 hover:border-slate-500'}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-slate-700 bg-slate-950/60 p-4 shadow-2xl shadow-slate-950/40">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-300">
                  <Headphones size={16} />
                  <span className="text-sm font-medium">Live support overview</span>
                </div>
                <span className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  Healthy
                </span>
              </div>
              <div className="mt-6 space-y-4">
                {[
                  { label: 'Retrieval success', value: '0%' },
                  { label: 'Avg. latency', value: '0 ms' },
                  { label: 'Vector health', value: 'Empty' },
                ].map((item) => (
                  <div key={item.label} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/80 px-3 py-2">
                    <span className="text-sm text-slate-300">{item.label}</span>
                    <span className="text-sm font-semibold text-white">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map(({ icon: Icon, label, value }) => (
            <div key={label} className="rounded-2xl border border-slate-800 bg-slate-900 p-4 shadow-lg shadow-slate-950/20">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-300">{label}</p>
                <div className="rounded-lg bg-slate-800 p-2 text-indigo-300">
                  <Icon size={16} />
                </div>
              </div>
              <p className="mt-5 text-3xl font-semibold text-white">{value}</p>
            </div>
          ))}
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Document ingestion</p>
                <h2 className="text-xl font-semibold text-white">Recent activity</h2>
              </div>
              <Activity className="text-teal-300" size={18} />
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={documentActivity}>
                  <defs>
                    <linearGradient id="ingestionFill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="5%" stopColor="#818cf8" stopOpacity={0.7} />
                      <stop offset="95%" stopColor="#818cf8" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#334155" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Area type="monotone" dataKey="indexed" stroke="#818cf8" fill="url(#ingestionFill)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Support volume</p>
                <h2 className="text-xl font-semibold text-white">User questions</h2>
              </div>
              <Gauge className="text-indigo-300" size={18} />
            </div>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={questionActivity}>
                  <CartesianGrid stroke="#334155" vertical={false} />
                  <XAxis dataKey="name" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip />
                  <Bar dataKey="questions" radius={[8, 8, 0, 0]} fill="#2dd4bf" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </section>

        <section id="assistant" className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <MessageSquareText className="text-indigo-300" size={18} />
                <h2 className="text-xl font-semibold text-white">AI Support Assistant</h2>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-300">
                <span className="rounded-full border border-slate-700 bg-slate-800 px-2 py-1">Primary model: qwen3.6:latest</span>
              </div>
            </div>
            <div className="mt-4 space-y-4">
              <div className="rounded-2xl bg-slate-950/70 p-3 text-sm text-slate-200">
                <p className="font-medium text-white">Assistant</p>
                <p className="mt-2 text-slate-300">I can answer based on the support knowledge base and cite the relevant retrieved passages.</p>
              </div>
              <div className="rounded-2xl bg-indigo-500/10 p-3 text-sm text-slate-200 ring-1 ring-indigo-500/20">
                <p className="font-medium text-white">User</p>
                <p className="mt-2 text-slate-300">What are the return and refund policies for premium support customers?</p>
              </div>
              <div className="rounded-2xl border border-slate-700 bg-slate-950/50 p-3 text-sm text-slate-200">
                <p className="font-medium text-white">Sources</p>
                <ul className="mt-2 space-y-2 text-slate-300">
                  <li>• Returns policy — support_manual.pdf (page 4)</li>
                  <li>• Premium subscriptions — faq.md</li>
                </ul>
              </div>
            </div>
          </div>

          <div id="knowledge-base" className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UploadCloud className="text-teal-300" size={18} />
                <h2 className="text-xl font-semibold text-white">Knowledge base</h2>
              </div>
              <button className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1.5 text-sm text-slate-100 hover:border-slate-500">
                Upload
              </button>
            </div>
            <div className="space-y-3">
              {['billing_policy.pdf', 'support_faq.md', 'refunds.csv'].map((doc) => (
                <div key={doc} className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-200">
                  <div className="flex items-center gap-2">
                    <FileText size={16} className="text-slate-400" />
                    <span>{doc}</span>
                  </div>
                  <span className="inline-flex items-center gap-1 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs text-emerald-300">
                    <CheckCircle2 size={12} /> Indexed
                  </span>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="models" className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="mb-4 flex items-center gap-2">
              <Database className="text-indigo-300" size={18} />
              <h2 className="text-xl font-semibold text-white">Model management</h2>
            </div>
            <div className="space-y-3 text-sm text-slate-300">
              <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
                <span>Primary</span>
                <span className="font-medium text-white">qwen3.6:latest</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
                <span>Fast model</span>
                <span className="font-medium text-white">not configured</span>
              </div>
              <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">
                <span>Fallback</span>
                <span className="font-medium text-white">not configured</span>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4">
            <div className="mb-4 flex items-center gap-2">
              <ArrowRight className="text-teal-300" size={18} />
              <h2 className="text-xl font-semibold text-white">Next actions</h2>
            </div>
            <ul className="space-y-3 text-sm text-slate-300">
              <li className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">Add a support policy PDF and index it for chat retrieval.</li>
              <li className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">Verify the Ollama runtime and model availability.</li>
              <li className="rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2">Review response citations before shipping to production.</li>
            </ul>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
