import React, { createContext, useContext, useState, useEffect } from 'react';

// Diccionario de traducciones completo (Español / Inglés)
const translations = {
  es: {
    // Menú de navegación
    mainMenu: 'MENÚ PRINCIPAL',
    adminSection: 'ADMINISTRACIÓN',
    dashboard: 'Dashboard',
    aiModule: '🤖 Módulo IA',
    cropManagement: 'Gestión Cultivos',
    users: 'Usuarios',
    dataManagement: 'Gestión Datos',
    audit: 'Auditoría',
    logout: 'Cerrar Sesión',
    theme: 'Tema',
    language: 'Idioma',
    lightMode: 'Claro',
    darkMode: 'Oscuro',
    
    // Dashboard
    dashboardTitle: 'Dashboard: Sistema Inteligente de Gestión Agrícola',
    calculatorTitle: 'Calculadora de Rentabilidad y Producción (IA)',
    selectedCrop: 'Cultivo Seleccionado:',
    plantedAcres: 'Hectáreas Sembradas:',
    salesHorizon: 'Horizonte de Venta:',
    in1Month: 'En 1 mes',
    in3Months: 'En 3 meses',
    in6Months: 'En 6 meses',
    in1Year: 'En 1 año',
    logisticCost: 'Costo Logístico (S/):',
    btnAnalyze: 'Generar Análisis Completo',
    estYield: 'Producción Estimada',
    projPrice: 'Precio Proyectado',
    pestRiskAlert: 'Alerta de Riesgo de Plagas',
    checkPestBtn: 'Consultar Riesgo de Plaga',
    sowingAssistant: 'Asistente de Siembra (Pre-Campaña)',
    sowingSub: '¿Qué será más rentable cosechar en el futuro?',
    seeProfitability: 'Ver rentabilidad para cosecha en:',
    estimatedPrice: 'Precio est:',
    reportsMgmt: 'Gestión de Reportes',
    reportsSub: 'Descarga la bitácora operacional de cosechas y rendimientos del valle.',
    exportPdf: 'Exportar PDF',
    exportExcel: 'Exportar Excel',
    exportCsv: 'Exportar CSV',
    dataIntelTitle: 'Inteligencia de Datos: Rendimientos del Valle',
    qualityTitle: 'Calidad de Producción Actual',

    // Login
    loginTitle: 'AGRO-JEQUETE',
    loginSubtitle: 'Gestión Inteligente del Valle',
    registerSubtitle: 'Crea tu cuenta agrícola',
    names: 'Nombres',
    lastnames: 'Apellidos',
    email: 'Correo Electrónico',
    password: 'Contraseña',
    forgotPassword: '¿Olvidaste tu contraseña?',
    btnLogin: 'Entrar al Dashboard',
    btnRegister: 'Registrarme ahora',
    connecting: 'Conectando...',
    noAccount: '¿Aún no tienes cuenta?',
    haveAccount: '¿Ya eres miembro?',
    registerNow: 'Regístrate',
    loginNow: 'Inicia sesión',

    // Módulo IA
    aiModuleTitle: 'Módulo de Análisis Científico con IA',
    aiModuleSub: 'Valle Jequetepeque — Análisis Comparativo de Modelos ML/DL',
    tabEda: '📊 1. EDA',
    tabTrain: '🤖 2. Entrenamiento',
    tabCv: '🔄 3. Validación Cruzada',
    tabHp: '⚙️ 4. Hiperparámetros',
    tabStats: '🔬 5. Pruebas Estadísticas',
    tabReports: '📄 6. Reportes',

    // General
    status: 'Estado',
    active: 'Activo',
    actions: 'Acciones'
  },
  en: {
    // Menu navigation
    mainMenu: 'MAIN MENU',
    adminSection: 'ADMINISTRATION',
    dashboard: 'Dashboard',
    aiModule: '🤖 AI Module',
    cropManagement: 'Crop Management',
    users: 'Users',
    dataManagement: 'Data Management',
    audit: 'Audit Log',
    logout: 'Logout',
    theme: 'Theme',
    language: 'Language',
    lightMode: 'Light',
    darkMode: 'Dark',

    // Dashboard
    dashboardTitle: 'Dashboard: Intelligent Agricultural Management System',
    calculatorTitle: 'Yield & Profitability Calculator (AI)',
    selectedCrop: 'Selected Crop:',
    plantedAcres: 'Planted Hectares:',
    salesHorizon: 'Sales Horizon:',
    in1Month: 'In 1 month',
    in3Months: 'In 3 months',
    in6Months: 'In 6 months',
    in1Year: 'In 1 year',
    logisticCost: 'Logistics Cost (S/):',
    btnAnalyze: 'Generate Full Analysis',
    estYield: 'Estimated Yield',
    projPrice: 'Projected Price',
    pestRiskAlert: 'Pest Risk Alert',
    checkPestBtn: 'Check Pest Risk',
    sowingAssistant: 'Sowing Assistant (Pre-Campaign)',
    sowingSub: 'What will be most profitable to harvest in the future?',
    seeProfitability: 'View profitability for harvest in:',
    estimatedPrice: 'Est. Price:',
    reportsMgmt: 'Reports Management',
    reportsSub: 'Download operational log of harvests and yields in the valley.',
    exportPdf: 'Export PDF',
    exportExcel: 'Export Excel',
    exportCsv: 'Export CSV',
    dataIntelTitle: 'Data Intelligence: Valley Yields',
    qualityTitle: 'Current Production Quality',

    // Login
    loginTitle: 'AGRO-JEQUETE',
    loginSubtitle: 'Intelligent Valley Management',
    registerSubtitle: 'Create your agricultural account',
    names: 'First Names',
    lastnames: 'Last Names',
    email: 'Email Address',
    password: 'Password',
    forgotPassword: 'Forgot your password?',
    btnLogin: 'Enter Dashboard',
    btnRegister: 'Register Now',
    connecting: 'Connecting...',
    noAccount: "Don't have an account?",
    haveAccount: 'Already a member?',
    registerNow: 'Register',
    loginNow: 'Log in',

    // AI Module
    aiModuleTitle: 'Scientific AI Analysis Module',
    aiModuleSub: 'Jequetepeque Valley — Comparative ML/DL Models Analysis',
    tabEda: '📊 1. EDA',
    tabTrain: '🤖 2. Training',
    tabCv: '🔄 3. Cross-Validation',
    tabHp: '⚙️ 4. Hyperparameters',
    tabStats: '🔬 5. Statistical Tests',
    tabReports: '📄 6. Reports',

    // General
    status: 'Status',
    active: 'Active',
    actions: 'Actions'
  }
};

const ThemeAndLangContext = createContext();

export function ThemeAndLangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('appLang') || 'es');
  const [theme, setTheme] = useState(() => localStorage.getItem('appTheme') || 'light');

  useEffect(() => {
    localStorage.setItem('appLang', lang);
  }, [lang]);

  useEffect(() => {
    localStorage.setItem('appTheme', theme);
    document.body.className = theme === 'dark' ? 'dark-theme' : 'light-theme';
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  const toggleLang = () => {
    setLang(prev => (prev === 'es' ? 'en' : 'es'));
  };

  const t = (key) => {
    return translations[lang]?.[key] || translations['es']?.[key] || key;
  };

  return (
    <ThemeAndLangContext.Provider value={{ lang, setLang, toggleLang, theme, setTheme, toggleTheme, t }}>
      {children}
    </ThemeAndLangContext.Provider>
  );
}

export function useThemeAndLang() {
  const context = useContext(ThemeAndLangContext);
  if (!context) {
    throw new Error('useThemeAndLang must be used within a ThemeAndLangProvider');
  }
  return context;
}
