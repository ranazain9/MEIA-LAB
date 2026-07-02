import { Layers, Mic, ShieldCheck } from "lucide-react";

const icons = {
  mic: Mic,
  layers: Layers,
  shield: ShieldCheck,
};

export function AgentStatusCard({ agent }) {
  const Icon = icons[agent.icon] || ShieldCheck;

  return (
    <article className="agent-card">
      <div className="agent-card-head">
        <Icon size={18} />
        <div>
          <h3>{agent.title}</h3>
          <p>{agent.subtitle}</p>
        </div>
      </div>
      <div className="terminal-lines">
        {agent.messages.map((message) => (
          <p key={`${agent.title}-${message.text}`}>
            <span className={`log-token ${message.severity}`}>[{message.severity}]</span>
            {message.text}
          </p>
        ))}
      </div>
    </article>
  );
}
