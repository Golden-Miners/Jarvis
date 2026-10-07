import { useCallback, useEffect, useState } from 'react';

export type Theme = 'dark' | 'light';

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Read from localStorage or detect from class on html
    const saved = localStorage.getItem('theme') as Theme | null;
    if (saved === 'dark' || saved === 'light') return saved;
    const cls = document.documentElement.classList.contains('light') ? 'light' : 'dark';
    return cls;
  });

  const setTheme = useCallback((t: Theme) => {
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(t);
    document.documentElement.style.colorScheme = t;
    localStorage.setItem('theme', t);
    setThemeState(t);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  }, [theme, setTheme]);

  // Sync if another tab changes theme
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === 'theme' && (e.newValue === 'dark' || e.newValue === 'light')) {
        setTheme(e.newValue as Theme);
      }
    };
    window.addEventListener('storage', handler);
    return () => window.removeEventListener('storage', handler);
  }, []);

  return { theme, setTheme, toggleTheme };
}
