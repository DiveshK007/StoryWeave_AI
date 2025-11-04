import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useLocation } from 'react-router-dom';
import { 
  BookOpen, Home, Plus, Users, BarChart3, Menu, X, 
  Sparkles, User, Settings, ChevronRight
} from 'lucide-react';
import { setUserContext, addBreadcrumb, setTag } from './lib/sentry';
import { Dashboard } from './pages/Dashboard';
import { StoryEditor } from './pages/StoryEditor';
import { StoriesList } from './pages/StoriesList';
import { CharactersPage } from './pages/CharactersPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

function App() {
  useEffect(() => {
    const userId = localStorage.getItem('user_id') || '1';
    const userEmail = localStorage.getItem('user_email') || 'user@storyweave.ai';
    
    setUserContext(userId, userEmail);
    addBreadcrumb('App initialized', 'app', 'info', { userId });
    setTag('app', 'storyweave');
    setTag('environment', import.meta.env.MODE);
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-bg-primary">
        <AppLayout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stories" element={<StoriesList />} />
            <Route path="/stories/:storyId" element={<StoryEditor />} />
            <Route path="/stories/:storyId/characters" element={<CharactersPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      </div>
    </Router>
  );
}

function AppLayout({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/stories', icon: BookOpen, label: 'Projects' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Top Navigation Bar */}
      <nav className="navbar fixed top-0 left-0 right-0 px-6 flex items-center justify-between">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center shadow-lg group-hover:shadow-glow-primary transition-shadow">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text-brand">
              StoryWeave
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || 
                (item.path === '/stories' && location.pathname.startsWith('/stories'));
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`nav-link ${isActive ? 'active' : ''}`}
                >
                  <Icon className="w-4 h-4 mr-2 inline" />
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Right Side Actions */}
        <div className="flex items-center gap-4">
          <Link
            to="/stories"
            className="btn-primary btn-sm hidden sm:inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            <span>New Story</span>
          </Link>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="md:hidden btn-icon"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* User Menu */}
          <div className="hidden md:flex items-center gap-3 pl-4 border-l border-border-subtle">
            <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-bg-tertiary border border-border-subtle hover:bg-bg-hover transition-colors cursor-pointer">
              <div className="w-8 h-8 rounded-full bg-gradient-brand flex items-center justify-center">
                <User className="w-4 h-4 text-white" />
              </div>
              <div className="hidden lg:block">
                <p className="text-sm font-medium text-text-primary">
                  {localStorage.getItem('user_email')?.split('@')[0] || 'User'}
                </p>
                <p className="text-xs text-text-tertiary">
                  {localStorage.getItem('user_email') || 'user@storyweave.ai'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Sidebar Backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 md:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-bg-secondary border-r border-border-subtle transform transition-transform duration-300 ease-out md:hidden ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Sidebar Header */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-border-subtle">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold gradient-text-brand">StoryWeave</span>
            </Link>
            <button
              onClick={() => setSidebarOpen(false)}
              className="btn-icon"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Sidebar Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || 
                (item.path === '/stories' && location.pathname.startsWith('/stories'));
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-primary-500/15 text-primary-500 font-semibold'
                      : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                  {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
                </Link>
              );
            })}

            <div className="pt-6 mt-6 border-t border-border-subtle">
              <Link
                to="/settings"
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-hover transition-all"
                onClick={() => setSidebarOpen(false)}
              >
                <Settings className="w-5 h-5" />
                <span>Settings</span>
              </Link>
            </div>
          </nav>

          {/* Sidebar Footer */}
          <div className="p-4 border-t border-border-subtle">
            <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-bg-tertiary border border-border-subtle">
              <div className="w-10 h-10 rounded-full bg-gradient-brand flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">
                  {localStorage.getItem('user_email')?.split('@')[0] || 'User'}
                </p>
                <p className="text-xs text-text-tertiary truncate">
                  {localStorage.getItem('user_email') || 'user@storyweave.ai'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden pt-16">
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-6 py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
