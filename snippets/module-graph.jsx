/* ---------------------------------------------------------------------------
   The eight-module dependency graph.

   Drawn by hand rather than by a diagram engine for one reason: the layout is
   the argument. Automation sits above five peers because it calls all five;
   directory sits beneath because it is called and calls nobody; audit spans the
   floor because it is written by a capability and never called at all. A layout
   engine chooses none of that.

   Solid = downward synchronous call through client/.
   Dashed = upward asynchronous return through the event stream.

   Colours come from styles.css, which carries the product's own tokens — so the
   accent is never used as a status here either.
--------------------------------------------------------------------------- */

const SANS = 'ui-sans-serif, -apple-system, "Segoe UI", Inter, sans-serif';
const MONO = 'ui-monospace, SFMono-Regular, "JetBrains Mono", Menlo, monospace';

/* five call targets of automation, left to right */
const PEERS = [
  { x: 40,  code: 'process',      role: 'deliberation', action: 'start_process\nsignal_process' },
  { x: 236, code: 'task',         role: 'work',         action: 'create_task' },
  { x: 432, code: 'notification', role: 'delivery',     action: 'notify' },
  { x: 628, code: 'integration',  role: 'egress',       action: 'call' },
  { x: 824, code: 'reporting',    role: 'output',       action: 'project' },
];

const PEER_W = 176;
const PEER_Y = 292;
const PEER_H = 84;

const Box = ({ x, y, w, h, code, role, accent, dashed }) => (
  <g>
    <rect
      x={x} y={y} width={w} height={h} rx="10"
      fill={accent ? 'var(--wo-accent-soft, #EFECFC)' : 'var(--wo-card, #FFFFFF)'}
      stroke={accent ? 'var(--wo-accent, #7B68EE)' : 'var(--wo-border, #E7E5F0)'}
      strokeWidth="1"
      strokeDasharray={dashed ? '5 4' : undefined}
    />
    <text
      x={x + 16} y={y + (role ? 32 : h / 2 + 5)}
      fontFamily={MONO} fontSize="14.5" fontWeight="600"
      fill={accent ? 'var(--wo-accent, #7B68EE)' : 'var(--wo-text, #1D1B2E)'}
    >
      {code}
    </text>
    {role && (
      <text x={x + 16} y={y + 54} fontFamily={SANS} fontSize="11.5" fill="var(--wo-text-3, #757289)">
        {role}
      </text>
    )}
  </g>
);

export const ModuleGraph = () => (
  <div className="wo-fig">
    <div className="wo-fig__scroll">
      <svg className="wo-fig__svg" viewBox="0 0 1120 620" role="img"
           aria-label="The eight modules of workspace-ops. Automation reads the event stream and calls process, task, notification, integration and reporting synchronously. Task and notification call directory. Those modules return asynchronously by publishing back to the event stream, which only automation reads. Audit is written by a platform capability and is called by nobody.">
        <defs>
          <marker id="wo-arrow" viewBox="0 0 8 8" refX="7" refY="4"
                  markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L8,4 L0,8 z" fill="var(--wo-text-3, #757289)" />
          </marker>
          <marker id="wo-arrow-accent" viewBox="0 0 8 8" refX="7" refY="4"
                  markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L8,4 L0,8 z" fill="var(--wo-accent, #7B68EE)" />
          </marker>
        </defs>

        {/* ---- the event stream, and the single read into automation ---- */}
        <rect x="40" y="24" width="960" height="46" rx="10"
              fill="var(--wo-neu-b, #EFEDF4)" stroke="var(--wo-border, #E7E5F0)"
              strokeWidth="1" strokeDasharray="5 4" />
        <text x="60" y="45" fontFamily={SANS} fontSize="12" fontWeight="600" fill="var(--wo-text-2, #6E6B85)">
          EVENT STREAM
        </text>
        <text x="60" y="60" fontFamily={SANS} fontSize="11" fill="var(--wo-text-3, #757289)">
          every module publishes here — external facts and internal returns are indistinguishable
        </text>

        <line x1="520" y1="70" x2="520" y2="126" stroke="var(--wo-accent, #7B68EE)"
              strokeWidth="1.5" markerEnd="url(#wo-arrow-accent)" />
        <text x="532" y="100" fontFamily={SANS} fontSize="11.5" fontWeight="600" fill="var(--wo-accent, #7B68EE)">
          the only stream reader
        </text>

        {/* ---- automation ---- */}
        <Box x={40} y={130} w={960} h={78} code="automation" accent />
        <text x={168} y={161} fontFamily={SANS} fontSize="12" fill="var(--wo-text-2, #6E6B85)">
          reflex · stateless per event · both ingress doors · the matcher
        </text>
        <text x={168} y={180} fontFamily={SANS} fontSize="11.5" fill="var(--wo-text-3, #757289)">
          nothing is ever &quot;in progress&quot; here
        </text>

        {/* ---- automation's five calls ---- */}
        {PEERS.map(p => {
          const cx = p.x + PEER_W / 2;
          const lines = p.action.split('\n');
          return (
            <g key={p.code}>
              <line x1={cx} y1={208} x2={cx} y2={PEER_Y - 6}
                    stroke="var(--wo-text-3, #757289)" strokeWidth="1.25" markerEnd="url(#wo-arrow)" />
              {lines.map((l, i) => (
                <text key={l} x={cx + 8} y={234 + i * 14}
                      fontFamily={MONO} fontSize="10.5" fill="var(--wo-text-2, #6E6B85)">
                  {l}
                </text>
              ))}
            </g>
          );
        })}

        {PEERS.map(p => (
          <Box key={p.code} x={p.x} y={PEER_Y} w={PEER_W} h={PEER_H}
               code={p.code} role={p.role} />
        ))}

        {/* ---- task and notification resolve responsibility ---- */}
        {[324, 520].map(cx => (
          <line key={cx} x1={cx} y1={PEER_Y + PEER_H} x2={cx} y2={442}
                stroke="var(--wo-text-3, #757289)" strokeWidth="1.25" markerEnd="url(#wo-arrow)" />
        ))}
        <text x="532" y="429" fontFamily={MONO} fontSize="10.5" fill="var(--wo-text-2, #6E6B85)">
          resolveResponsible
        </text>

        <Box x={236} y={448} w={372} h={74} code="directory" role="foundation — called, calls nobody" />

        {/* ---- the return path: risers, gather, and the bus up the right ---- */}
        <g stroke="var(--wo-accent-line, #C9C0F6)" strokeWidth="1.25" strokeDasharray="5 4" fill="none">
          {[128, 324, 716, 912].map(cx => (
            <line key={cx} x1={cx} y1={PEER_Y + PEER_H} x2={cx} y2={410} />
          ))}
          <line x1="128" y1="410" x2="1050" y2="410" />
          <line x1="608" y1="485" x2="1050" y2="485" />
          <line x1="1050" y1="485" x2="1050" y2="47" />
          <line x1="1050" y1="47" x2="1006" y2="47" markerEnd="url(#wo-arrow)" />
        </g>

        <text x="1062" y="250" fontFamily={SANS} fontSize="11" fontWeight="600"
              fill="var(--wo-text-3, #757289)" transform="rotate(-90 1062 250)">
          RETURN PATH — ASYNCHRONOUS
        </text>

        {/* ---- audit: written by a capability, called by nobody ---- */}
        <Box x={40} y={548} w={960} h={56} code="audit" dashed />
        <text x={130} y={572} fontFamily={SANS} fontSize="12" fill="var(--wo-text-2, #6E6B85)">
          read-only · written by a platform capability, inside the caller&apos;s transaction
        </text>
        <text x={130} y={590} fontFamily={SANS} fontSize="11.5" fill="var(--wo-text-3, #757289)">
          no module ever calls it — which is the same fact as it being permanently un-extractable
        </text>
      </svg>
    </div>

    <div className="wo-legend">
      <span className="wo-legend__item">
        <span className="wo-legend__rule" /> downward call — synchronous, through <code>client/</code>
      </span>
      <span className="wo-legend__item">
        <span className="wo-legend__rule wo-legend__rule--dashed" /> upward return — asynchronous, through the stream
      </span>
      <span className="wo-legend__item">
        <span className="wo-legend__swatch wo-legend__swatch--accent" /> the only stream reader
      </span>
      <span className="wo-legend__item">
        <span className="wo-legend__swatch wo-legend__swatch--muted" /> written by a capability, never called
      </span>
    </div>

    <div className="wo-fig__caption">
      <b>The layout is the argument.</b> Automation sits above five peers because it calls all five;
      directory sits beneath because it is called and calls nobody; audit spans the floor because it
      is written by a capability and never called at all.
    </div>
  </div>
);
