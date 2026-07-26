import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useThemeAndLang } from '../context/ThemeAndLangContext';

function MenuNavegacion() {
  const location = useLocation();
  const navigate = useNavigate();
  const { lang, setLang, theme, toggleTheme, t } = useThemeAndLang();
  
  const authPaths = ['/login', '/recuperar'];
  if (authPaths.includes(location.pathname) || location.pathname.startsWith('/restablecer-password/')) {
    return null;
  }

  const sesionStr = localStorage.getItem('sesionAgricola');
  const usuario = sesionStr ? JSON.parse(sesionStr) : null;

  const cerrarSesion = () => {
    localStorage.removeItem('sesionAgricola');
    sessionStorage.removeItem('visitaRegistrada');
    navigate('/login');
  };

  const isActive = (path) => location.pathname === path;
  const isDark = theme === 'dark';

  const currentSidebarStyle = {
    ...sidebarStyle,
    background: isDark ? '#0b291a' : '#1b5e20',
    borderRight: isDark ? '1px solid #1e3a29' : 'none'
  };

  return (
    <aside style={currentSidebarStyle}>
      <div style={logoWrapper}>
        <div style={logoIcon}>🌱</div>
        <h2 style={logoStyle}>AGRO<span style={{color: '#81c784'}}>JEQUE</span></h2>
      </div>

      {/* CONTROLES DE TEMA E IDIOMA */}
      <div style={toggleContainerStyle}>
        <div style={toggleButtonGroup}>
          <button 
            onClick={() => setLang('es')} 
            style={{ ...toggleBtn, background: lang === 'es' ? '#81c784' : 'transparent', color: lang === 'es' ? '#0f291e' : '#e8f5e9' }}
            title="Español"
          >
            🇪🇸 ES
          </button>
          <button 
            onClick={() => setLang('en')} 
            style={{ ...toggleBtn, background: lang === 'en' ? '#81c784' : 'transparent', color: lang === 'en' ? '#0f291e' : '#e8f5e9' }}
            title="English"
          >
            🇬🇧 EN
          </button>
        </div>

        <button onClick={toggleTheme} style={themeToggleBtn} title={isDark ? t('lightMode') : t('darkMode')}>
          {isDark ? '☀️' : '🌙'} {isDark ? t('lightMode') : t('darkMode')}
        </button>
      </div>
      
      {usuario && (
        <div style={navLinks}>
          <div style={sectionLabel}>{t('mainMenu')}</div>
          <Link to="/" style={isActive('/') ? activeLinkStyle : linkStyle}>
             {t('dashboard')}
          </Link>
          <Link to="/ia" style={isActive('/ia') ? activeLinkStyle : linkStyle}>
             {t('aiModule')}
          </Link>
          
          {usuario.rol === 'Admin' && (
            <>
              <div style={sectionLabel}>{t('adminSection')}</div>
              <Link to="/cultivos" style={isActive('/cultivos') ? activeLinkStyle : linkStyle}>
                 {t('cropManagement')}
              </Link>
              <Link to="/usuarios" style={isActive('/usuarios') ? activeLinkStyle : linkStyle}>
                 {t('users')}
              </Link>
              <Link to="/datos" style={isActive('/datos') ? activeLinkStyle : linkStyle}>
                 {t('dataManagement')}
              </Link>
              <Link to="/auditoria" style={isActive('/auditoria') ? activeLinkStyle : linkStyle}>
                 {t('audit')}
              </Link>
            </>
          )}
        </div>
      )}

      <div style={footerStyle}>
        {usuario && (
          <>
            <div style={userBadge}>
              <div style={userAvatar}>{usuario.nombres ? usuario.nombres[0] : 'U'}</div>
              <div style={userInfo}>
                <span style={userName}>{usuario.nombres}</span>
                <span style={userRole}>{usuario.rol}</span>
              </div>
            </div>
            <button onClick={cerrarSesion} style={logoutBtn}>
              {t('logout')}
            </button>
          </>
        )}
      </div>
    </aside>
  );
}

const toggleContainerStyle = {
  padding: '0 20px 20px 20px',
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
};

const toggleButtonGroup = {
  display: 'flex',
  background: 'rgba(0,0,0,0.2)',
  borderRadius: '8px',
  padding: '3px',
  gap: '2px',
};

const toggleBtn = {
  flex: 1,
  border: 'none',
  padding: '6px 0',
  borderRadius: '6px',
  cursor: 'pointer',
  fontSize: '0.8rem',
  fontWeight: 'bold',
  transition: 'all 0.2s ease',
};

const themeToggleBtn = {
  background: 'rgba(255,255,255,0.12)',
  color: 'white',
  border: 'none',
  padding: '8px 12px',
  borderRadius: '8px',
  cursor: 'pointer',
  fontSize: '0.85rem',
  fontWeight: '600',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  gap: '6px',
  transition: 'all 0.2s ease',
};

const sidebarStyle = {
  width: '260px',
  height: '100vh',
  background: '#1b5e20',
  color: 'white',
  position: 'fixed',
  left: 0,
  top: 0,
  display: 'flex',
  flexDirection: 'column',
  boxShadow: '4px 0 15px rgba(0,0,0,0.1)',
  zIndex: 1000,
  padding: '30px 0',
};

const logoWrapper = {
  padding: '0 25px 40px 25px',
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
};

const logoIcon = { fontSize: '2rem' };

const logoStyle = {
  margin: 0,
  fontSize: '1.4rem',
  fontWeight: '800',
  letterSpacing: '1px',
};

const navLinks = {
  display: 'flex',
  flexDirection: 'column',
  gap: '8px',
  padding: '0 15px',
  flex: 1,
};

const sectionLabel = {
  fontSize: '0.7rem',
  fontWeight: '700',
  color: 'rgba(255,255,255,0.4)',
  padding: '20px 10px 10px 10px',
  letterSpacing: '1px',
};

const linkStyle = {
  display: 'flex',
  alignItems: 'center',
  color: '#e8f5e9',
  textDecoration: 'none',
  padding: '12px 15px',
  borderRadius: '12px',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  fontSize: '0.95rem',
  fontWeight: '500',
};

const activeLinkStyle = {
  ...linkStyle,
  background: 'rgba(255, 255, 255, 0.15)',
  color: 'white',
  boxShadow: 'inset 0 0 10px rgba(0,0,0,0.1)',
};

const footerStyle = {
  padding: '20px 20px',
  borderTop: '1px solid rgba(255,255,255,0.1)',
  display: 'flex',
  flexDirection: 'column',
  gap: '15px',
};

const userBadge = {
  display: 'flex',
  alignItems: 'center',
  gap: '12px',
  padding: '0 5px',
};

const userAvatar = {
  width: '40px',
  height: '40px',
  borderRadius: '50%',
  background: '#43a047',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '1.2rem',
  fontWeight: 'bold',
};

const userInfo = {
  display: 'flex',
  flexDirection: 'column',
};

const userName = { fontSize: '0.9rem', fontWeight: '600' };
const userRole = { fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)' };

const logoutBtn = {
  background: 'rgba(255, 255, 255, 0.1)',
  color: 'white',
  border: 'none',
  padding: '12px',
  borderRadius: '10px',
  cursor: 'pointer',
  fontSize: '0.9rem',
  fontWeight: '600',
  transition: 'all 0.3s',
  width: '100%',
};

export default MenuNavegacion;