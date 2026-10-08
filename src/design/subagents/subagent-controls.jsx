/* subagents/subagent-controls.jsx — act on a running agent from the
   inspector: message it as its user (`steer_subagent`) or stop it
   (`cancel_subagent`, behind a confirm step). Mounted for as long as
   SubagentInspector shows the agent (its per-agent key), so the draft and
   the note start fresh per agent. Once the agent stops running the controls
   hide, except for text that never got through: a draft typed meanwhile or a
   message the ending agent refused stays, with a note, so it can be copied.
   Nothing here edits the agent record: a delivered message shows up as a
   `you ›` line in the Output stream, a stop as omp's `aborted` lifecycle frame. */

const { Icon: _SAC_Icon } = window;

function SubagentControls({ agentId, running, onSteer, onStop }) {
  const [draft, setDraft] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [stopPhase, setStopPhase] = React.useState(null); // null | "confirm" | "stopping"
  const [note, setNote] = React.useState(null); // { err, text }
  const inputRef = React.useRef(null);
  React.useEffect(() => {
    if (running) { setNote(null); return; } // a re-run of the same id starts clean
    // The confirm row goes with `running`: if it held focus, hand it to the
    // kept box rather than <body> (same reason as endConfirm below).
    if (stopPhase === "confirm" && document.activeElement === document.body) inputRef.current?.focus();
    setStopPhase(null);
  }, [running]);

  const text = draft.trim();
  if (!running && !text && !sending) return null;
  const canSend = running && text && !sending && stopPhase !== "stopping";

  const send = async () => {
    if (!canSend) return;
    setSending(true);
    setNote(null);
    try {
      await onSteer(agentId, text);
      setDraft(""); // read-only while sending, so this is still the text that went out
      setNote({ err: false, text: "已发送。智能体会在下一步读取。" });
    } catch (e) {
      // A timeout is not a refusal: omp may still deliver the message.
      setNote(e?.timedOut
        ? { err: false, text: "omp 还没有回答；消息可能仍在路上。" }
        : { err: true, text: String(e?.message ?? e) });
    } finally {
      setSending(false);
    }
  };
  // Leaving the confirm step hands focus back to the box, not to <body>,
  // where the next Escape would reach the window keymap.
  const endConfirm = () => { setStopPhase(null); inputRef.current?.focus(); };
  const stop = async () => {
    inputRef.current?.focus(); // as endConfirm
    setStopPhase("stopping");
    setNote(null);
    let stopped = false;
    try {
      stopped = await onStop(agentId);
      setNote({ err: false, text: stopped ?"已停止。" : "它已经不在运行了。" });
    } catch (e) {
      setNote({ err: true, text: String(e?.message ?? e) });
    }
    // A stopped agent takes no more messages: stay disabled until its
    // `aborted` frame ends `running` (the second click of a double-click on
    // the confirm button would otherwise land on `send`).
    if (!stopped) setStopPhase(null);
  };

  return (
    // One Escape handler for the whole box, prevented so the window keymap
    // does not abort the main turn: it leaves the confirm step, else blurs.
    <div className="sa-ctl" onKeyDown={e => {
      if (e.key !== "Escape") return;
      e.preventDefault();
      if (stopPhase === "confirm") endConfirm();
      else e.target.blur?.();
    }}>
      <textarea ref={inputRef} className="sa-ctl-input" rows={2} value={draft} readOnly={sending}
        placeholder="给该智能体发消息…" aria-label={`message ${agentId}`}
        onChange={e => { setDraft(e.target.value); setNote(null); }}
        onKeyDown={e => {
          if (running && window.isSubmitEnter(e) && !e.shiftKey) { e.preventDefault(); send(); }
        }} />
      {note && <div className={`sa-ctl-note${note.err ? " err" : ""}`}>{note.text}</div>}
      {!running && !sending && <div className="sa-ctl-note">智能体已不在运行；这段文本没有发出。</div>}
      {running && stopPhase === "confirm" && (
        <div className="sa-ctl-row confirm">
          <span className="sa-ctl-ask">停止该智能体？父任务会收到已中止的结果。</span>
          <button autoFocus className="btn ghost outlined" onClick={endConfirm}>继续运行</button>
          <button className="btn danger" onClick={stop}><_SAC_Icon name="stop" size={10} /> stop</button>
        </div>
      )}
      {running && stopPhase !== "confirm" && (
        <div className="sa-ctl-row">
          <button className="btn ghost outlined" onClick={() => setStopPhase("confirm")} disabled={stopPhase === "stopping"} title="停止该智能体">
            <_SAC_Icon name="stop" size={10} /> {stopPhase === "stopping" ? "正在停止…" : "stop"}
          </button>
          <div style={{ flex: 1 }} />
          <button className="btn primary" onClick={send} disabled={!canSend}>
            {sending ? "发送中…" : "send"} <_SAC_Icon name="arrow" size={11} />
          </button>
        </div>
      )}
    </div>
  );
}

Object.assign(window, { SubagentControls });
