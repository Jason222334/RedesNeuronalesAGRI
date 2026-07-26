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

  /* DARK THEME GLOBAL OVERRIDES */
  body.dark-theme {
    background-color: #0f172a !important;
    color: #f8fafc !important;
  }
  body.dark-theme #root, 
  body.dark-theme main {
    background-color: #0f172a !important;
    color: #f8fafc !important;
  }

  /* TABLES IN DARK MODE */
  body.dark-theme table {
    background-color: #1e293b !important;
    color: #f8fafc !important;
    border-color: #334155 !important;
  }
  body.dark-theme thead, 
  body.dark-theme thead tr, 
  body.dark-theme thead th,
  body.dark-theme th {
    background-color: #0f172a !important;
    color: #4ade80 !important;
    border-bottom: 2px solid #334155 !important;
  }
  body.dark-theme tbody, 
  body.dark-theme tbody tr,
  body.dark-theme tr {
    background-color: #1e293b !important;
    color: #f8fafc !important;
  }
  body.dark-theme tbody tr:nth-child(even),
  body.dark-theme tr:nth-child(even) {
    background-color: #0f291e !important;
  }
  body.dark-theme tbody tr:hover,
  body.dark-theme tr:hover {
    background-color: #334155 !important;
  }
  body.dark-theme td {
    color: #f8fafc !important;
    border-bottom: 1px solid #334155 !important;
  }

  /* INPUTS & SELECTS IN DARK MODE */
  body.dark-theme input, 
  body.dark-theme select, 
  body.dark-theme textarea {
    background-color: #0f172a !important;
    color: #f8fafc !important;
    border-color: #334155 !important;
  }
  body.dark-theme option {
    background-color: #1e293b !important;
    color: #f8fafc !important;
  }

  /* CARDS & CONTAINERS IN DARK MODE */
  body.dark-theme .login-card,
  body.dark-theme .card {
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
