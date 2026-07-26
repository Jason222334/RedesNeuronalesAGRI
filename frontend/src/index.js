import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { ThemeAndLangProvider } from './context/ThemeAndLangContext';

const root = ReactDOM.createRoot(document.getElementById('root'));

// Global CSS Reset & Theme Variable definitions
const style = document.createElement('style');
style.innerHTML = `
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
  }
  html, body, #root {
    width: 100%;
    min-height: 100vh;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
  }
  body.light-theme {
    background-color: #f8f9fa;
    color: #2c3e50;
  }
  body.dark-theme {
    background-color: #0f172a;
    color: #f8fafc;
  }
  body.dark-theme input, body.dark-theme select, body.dark-theme textarea {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border-color: #334155 !important;
  }
  body.dark-theme .login-card {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border: 1px solid #334155 !important;
  }
`;
document.head.appendChild(style);

root.render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeAndLangProvider>
        <App />
      </ThemeAndLangProvider>
    </BrowserRouter>
  </React.StrictMode>
);
