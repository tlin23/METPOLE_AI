import { useState, useEffect } from "react";

const ErrorNotification = ({ error, onDismiss, duration = 5000 }) => {
  const [isVisible, setIsVisible] = useState(!!error);

  useEffect(() => {
    if (error) {
      setIsVisible(true);

      // Auto-dismiss after duration
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onDismiss && onDismiss(), 300); // Wait for fade out
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [error, duration, onDismiss]);

  if (!error) return null;

  const getErrorType = (error) => {
    if (error.status === 401 || error.status === 403) return "auth";
    if (error.status === 429) return "rateLimit";
    if (error.status >= 500) return "server";
    if (error.status >= 400) return "client";
    return "network";
  };

  const getErrorMessage = (error) => {
    // Custom messages for different error types
    if (error.status === 401) {
      return "Your session has expired. Please sign in again.";
    }
    if (error.status === 403) {
      return "You don't have permission to access this resource.";
    }
    if (error.status === 429) {
      return (
        error.data?.message ||
        "You've reached your daily limit. Please try again tomorrow."
      );
    }
    if (error.status >= 500) {
      return "Our service is temporarily unavailable. Please try again in a few moments.";
    }
    if (error.data?.message) {
      return error.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return "An unexpected error occurred. Please try again.";
  };

  const getErrorIcon = (type) => {
    switch (type) {
      case "auth":
        return "🔒";
      case "rateLimit":
        return "⏰";
      case "server":
        return "🚫";
      case "client":
        return "⚠️";
      case "network":
        return "📡";
      default:
        return "❌";
    }
  };

  const errorType = getErrorType(error);
  const message = getErrorMessage(error);
  const icon = getErrorIcon(errorType);

  const styles = {
    container: {
      position: "fixed",
      top: "20px",
      right: "20px",
      zIndex: 1000,
      maxWidth: "400px",
      opacity: isVisible ? 1 : 0,
      transform: isVisible ? "translateX(0)" : "translateX(100%)",
      transition: "all 0.3s ease-in-out",
    },
    notification: {
      background:
        errorType === "auth"
          ? "#f56565"
          : errorType === "rateLimit"
          ? "#ed8936"
          : errorType === "server"
          ? "#e53e3e"
          : "#f56565",
      color: "white",
      padding: "16px",
      borderRadius: "8px",
      boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
      display: "flex",
      alignItems: "center",
      gap: "12px",
    },
    icon: {
      fontSize: "20px",
      flexShrink: 0,
    },
    content: {
      flex: 1,
    },
    message: {
      margin: 0,
      fontSize: "14px",
      lineHeight: "1.4",
    },
    closeButton: {
      background: "none",
      border: "none",
      color: "white",
      fontSize: "18px",
      cursor: "pointer",
      padding: "4px",
      borderRadius: "4px",
      opacity: 0.8,
      transition: "opacity 0.2s",
    },
    closeButtonHover: {
      opacity: 1,
    },
  };

  return (
    <div style={styles.container}>
      <div style={styles.notification}>
        <div style={styles.icon}>{icon}</div>
        <div style={styles.content}>
          <p style={styles.message}>{message}</p>
        </div>
        <button
          style={styles.closeButton}
          onClick={() => {
            setIsVisible(false);
            setTimeout(() => onDismiss && onDismiss(), 300);
          }}
          onMouseEnter={(e) => (e.target.style.opacity = 1)}
          onMouseLeave={(e) => (e.target.style.opacity = 0.8)}
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default ErrorNotification;
