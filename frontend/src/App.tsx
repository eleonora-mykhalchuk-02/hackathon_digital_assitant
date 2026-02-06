import { useState } from 'react';
import { ChatUI } from './components/ChatUI';
import type { JudgeEvaluation } from './types';
import './App.css';

function App() {
  const [currentEvaluation, setCurrentEvaluation] = useState<JudgeEvaluation | null>(null);
  const [currentIteration, setCurrentIteration] = useState<number | undefined>(undefined);

  return (
    <div style={styles.app}>
      <div style={styles.layout}>
        <div style={styles.chatColumn}>
          <ChatUI
            onEvaluationUpdate={setCurrentEvaluation}
            onIterationUpdate={setCurrentIteration}
          />
        </div>
        {/* Judge panel hidden - traffic lights shown inline in messages */}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    height: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f8f9fa',
  },
  layout: {
    flex: 1,
    display: 'flex',
    overflow: 'hidden',
  },
  chatColumn: {
    flex: 1,
    height: '100%',
    overflow: 'hidden',
  },
};

export default App;
