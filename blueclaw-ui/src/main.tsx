import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './app/App';

// ReactFlow styles
import 'reactflow/dist/style.css';

// Global styles
import './styles/global.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
