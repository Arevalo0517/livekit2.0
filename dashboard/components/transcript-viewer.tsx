interface Props {
  transcript: string;
}

export default function TranscriptViewer({ transcript }: Props) {
  if (!transcript.trim()) {
    return <p className="text-gray-400 italic">Sin transcripción</p>;
  }

  const lines = transcript.split('\n').filter(Boolean);

  return (
    <div className="space-y-2">
      {lines.map((line, i) => {
        const isAgent = line.startsWith('Agent:');
        return (
          <div key={i} className={`flex gap-3 ${isAgent ? '' : 'flex-row-reverse'}`}>
            <span className="shrink-0 text-xs font-semibold text-gray-400 mt-1 w-12 text-right">
              {isAgent ? 'Agente' : 'User'}
            </span>
            <div
              className={`rounded-lg px-4 py-2 text-sm max-w-2xl ${
                isAgent
                  ? 'bg-indigo-50 text-indigo-900'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {line.replace(/^(Agent|User):\s*/, '')}
            </div>
          </div>
        );
      })}
    </div>
  );
}
