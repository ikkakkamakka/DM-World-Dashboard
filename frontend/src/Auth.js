import React, { useState, useContext, createContext, useEffect, useCallback, useRef } from 'react';

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  
  // Session management state
  const [isSessionWarning, setIsSessionWarning] = useState(false);
  const [sessionWarningCountdown, setSessionWarningCountdown] = useState(120); // 2 minutes in seconds
  const [lastActivity, setLastActivity] = useState(Date.now());
  
  // Refs to store intervals
  const activityCheckInterval = useRef(null);
  const tokenRefreshInterval = useRef(null);
  const warningCountdownInterval = useRef(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

  // Session configuration
  const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes in milliseconds
  const WARNING_TIME = 2 * 60 * 1000; // 2 minutes before logout in milliseconds
  const TOKEN_REFRESH_INTERVAL = 5 * 60 * 1000; // Refresh token every 5 minutes if active
  const ACTIVITY_CHECK_INTERVAL = 60 * 1000; // Check activity every minute

  // Track user activity
  const updateActivity = useCallback(() => {
    setLastActivity(Date.now());
    if (isSessionWarning) {
      setIsSessionWarning(false);
      if (warningCountdownInterval.current) {
        clearInterval(warningCountdownInterval.current);
        warningCountdownInterval.current = null;
      }
    }
  }, [isSessionWarning]);

  // Add activity event listeners
  useEffect(() => {
    if (token && user) {
      const activityEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];
      
      activityEvents.forEach(event => {
        document.addEventListener(event, updateActivity, { passive: true });
      });

      return () => {
        activityEvents.forEach(event => {
          document.removeEventListener(event, updateActivity);
        });
      };
    }
  }, [token, user, updateActivity]);

  // Session timeout and token refresh management
  useEffect(() => {
    if (token && user) {
      // Check activity and handle session timeout
      activityCheckInterval.current = setInterval(() => {
        const now = Date.now();
        const timeSinceActivity = now - lastActivity;
        
        if (timeSinceActivity >= SESSION_TIMEOUT) {
          // Session expired - auto logout
          console.log('Session expired due to inactivity');
          logout();
        } else if (timeSinceActivity >= SESSION_TIMEOUT - WARNING_TIME && !isSessionWarning) {
          // Show warning modal
          setIsSessionWarning(true);
          setSessionWarningCountdown(120); // 2 minutes
          
          // Start countdown timer
          warningCountdownInterval.current = setInterval(() => {
            setSessionWarningCountdown(prev => {
              if (prev <= 1) {
                // Auto logout when countdown reaches 0
                logout();
                return 0;
              }
              return prev - 1;
            });
          }, 1000);
        }
      }, ACTIVITY_CHECK_INTERVAL);

      // Periodic token refresh for active users
      tokenRefreshInterval.current = setInterval(async () => {
        const timeSinceActivity = Date.now() - lastActivity;
        
        // Only refresh token if user has been active recently (within last 10 minutes)
        if (timeSinceActivity < 10 * 60 * 1000) {
          try {
            const response = await fetch(`${backendUrl}/api/auth/refresh-token`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });
            
            if (response.ok) {
              const data = await response.json();
              localStorage.setItem('authToken', data.access_token);
              setToken(data.access_token);
              console.log('Token refreshed successfully');
            }
          } catch (error) {
            console.error('Token refresh failed:', error);
          }
        }
      }, TOKEN_REFRESH_INTERVAL);
    }

    return () => {
      if (activityCheckInterval.current) {
        clearInterval(activityCheckInterval.current);
      }
      if (tokenRefreshInterval.current) {
        clearInterval(tokenRefreshInterval.current);
      }
      if (warningCountdownInterval.current) {
        clearInterval(warningCountdownInterval.current);
      }
    };
  }, [token, user, lastActivity, isSessionWarning, backendUrl]);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('authToken');
      const storedUser = localStorage.getItem('authUser');
      
      if (storedToken && storedUser) {
        try {
          // Verify token is still valid
          const response = await fetch(`${backendUrl}/api/auth/verify-token`, {
            headers: {
              'Authorization': `Bearer ${storedToken}`
            }
          });
          
          if (response.ok) {
            setToken(storedToken);
            setUser(JSON.parse(storedUser));
            setLastActivity(Date.now()); // Update activity time on successful auth
          } else {
            // Token is invalid, clear storage
            localStorage.removeItem('authToken');
            localStorage.removeItem('authUser');
            setToken(null);
            setUser(null);
          }
        } catch (error) {
          console.error('Token verification failed:', error);
          localStorage.removeItem('authToken');
          localStorage.removeItem('authUser');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, [backendUrl]);

  const login = async (username, password) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Store token and user info
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('authUser', JSON.stringify(data.user_info));
        
        setToken(data.access_token);
        setUser(data.user_info);
        setLastActivity(Date.now()); // Update activity on login
        
        return { success: true };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.detail || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const signup = async (username, email, password) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, email, password }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Store token and user info
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('authUser', JSON.stringify(data.user_info));
        
        setToken(data.access_token);
        setUser(data.user_info);
        setLastActivity(Date.now()); // Update activity on signup
        
        return { success: true };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.detail || 'Signup failed' };
      }
    } catch (error) {
      console.error('Signup error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const logout = useCallback(() => {
    // Clear intervals
    if (activityCheckInterval.current) {
      clearInterval(activityCheckInterval.current);
    }
    if (tokenRefreshInterval.current) {
      clearInterval(tokenRefreshInterval.current);
    }
    if (warningCountdownInterval.current) {
      clearInterval(warningCountdownInterval.current);
    }
    
    // Clear storage and state
    localStorage.removeItem('authToken');
    localStorage.removeItem('authUser');
    setToken(null);
    setUser(null);
    setIsSessionWarning(false);
    setSessionWarningCountdown(120);
  }, []);

  const extendSession = useCallback(() => {
    setLastActivity(Date.now());
    setIsSessionWarning(false);
    if (warningCountdownInterval.current) {
      clearInterval(warningCountdownInterval.current);
      warningCountdownInterval.current = null;
    }
  }, []);

  const value = {
    user,
    token,
    login,
    signup,
    logout,
    loading,
    isAuthenticated: !!user && !!token,
    isSessionWarning,
    sessionWarningCountdown,
    extendSession
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
      {isSessionWarning && <SessionWarningModal />}
    </AuthContext.Provider>
  );
};

// Session Warning Modal Component
const SessionWarningModal = () => {
  const { sessionWarningCountdown, extendSession, logout } = useAuth();

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg shadow-2xl w-full max-w-md p-6 border border-red-600">
        <div className="text-center">
          <div className="text-red-400 text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-red-400 mb-4">Session Timeout Warning</h2>
          <p className="text-slate-300 mb-4">
            Your session will expire in <strong className="text-red-400">{formatTime(sessionWarningCountdown)}</strong> due to inactivity.
          </p>
          <p className="text-slate-400 text-sm mb-6">
            Click "Stay Logged In" to extend your session, or you will be automatically logged out.
          </p>
          <div className="flex space-x-4">
            <button
              onClick={extendSession}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Stay Logged In
            </button>
            <button
              onClick={logout}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              Logout Now
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Login/Signup Component
export const AuthScreen = () => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, signup } = useAuth();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLoginMode) {
        // Login
        const result = await login(formData.username, formData.password);
        if (!result.success) {
          setError(result.error);
        }
      } else {
        // Signup
        if (formData.password !== formData.confirmPassword) {
          setError('Passwords do not match');
          setLoading(false);
          return;
        }
        
        if (formData.password.length < 6) {
          setError('Password must be at least 6 characters long');
          setLoading(false);
          return;
        }

        const result = await signup(formData.username, formData.email, formData.password);
        if (!result.success) {
          setError(result.error);
        }
      }
    } catch (error) {
      setError('An unexpected error occurred. Please try again.');
    }
    
    setLoading(false);
  };

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setFormData({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    });
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-slate-800 flex items-center justify-center p-4">
      <div className="bg-slate-800 rounded-lg shadow-2xl w-full max-w-md p-8 border border-blue-700">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-yellow-400 mb-2">⚔️ Faerûn Campaign Manager</h1>
          <p className="text-slate-300">
            {isLoginMode ? 'Welcome back, Dungeon Master!' : 'Begin your legendary campaign'}
          </p>
        </div>

        {/* Auth Toggle */}
        <div className="flex mb-6 bg-slate-700 rounded-lg p-1">
          <button
            type="button"
            onClick={() => setIsLoginMode(true)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              isLoginMode
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setIsLoginMode(false)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              !isLoginMode
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-slate-300 hover:text-white'
            }`}
          >
            Sign Up
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/50 border border-red-700 rounded-md">
            <p className="text-red-200 text-sm">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your username"
            />
          </div>

          {/* Email (only for signup) */}
          {!isLoginMode && (
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter your email"
              />
            </div>
          )}

          {/* Password */}
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your password"
            />
          </div>

          {/* Confirm Password (only for signup) */}
          {!isLoginMode && (
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Confirm your password"
              />
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center"
          >
            {loading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {isLoginMode ? 'Logging in...' : 'Creating account...'}
              </>
            ) : (
              isLoginMode ? 'Login' : 'Create Account'
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-slate-400 text-sm">
            {isLoginMode ? "Don't have an account? " : "Already have an account? "}
            <button
              type="button"
              onClick={toggleMode}
              className="text-blue-400 hover:text-blue-300 font-medium"
            >
              {isLoginMode ? 'Sign up here' : 'Login here'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
};

// User Profile Component (optional)
export const UserProfile = () => {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center space-x-3">
      <div className="text-right">
        <p className="text-sm font-medium text-slate-200">{user.username}</p>
        <p className="text-xs text-slate-400">{user.email}</p>
      </div>
      <button
        onClick={logout}
        className="px-3 py-1 text-sm bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
      >
        Logout
      </button>
    </div>
  );
};