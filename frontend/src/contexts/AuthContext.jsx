import { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetchAndSetUser(token);
    }
  }, []);

  // Initialize axios with auth interceptor
  useEffect(() => {
    const interceptor = axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem("token");
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor to handle 401s and 403s
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401 || error.response?.status === 403) {
          setUser(null);
          localStorage.removeItem("token");
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.request.eject(interceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  const fetchAndSetUser = async (token) => {
    try {
      // Set token in localStorage
      localStorage.setItem("token", token);
      // Call backend to get user info (including is_admin)
      const res = await axios.get(
        `${import.meta.env.VITE_BACKEND_URL}/admin/me`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      setUser({ token, ...res.data });
    } catch (error) {
      console.error("Error fetching user info:", error);
      setUser(null);
      localStorage.removeItem("token");
    }
  };

  const login = (token) => {
    fetchAndSetUser(token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const value = {
    user,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
