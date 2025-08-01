import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Login from "./components/Login";
import Feedback from "./components/Feedback";
import AdminMenu from "./components/AdminMenu";
import ErrorNotification from "./components/ErrorNotification";
import "./App.css";
import styles from "./App.styles.js";

// Get Google Client ID from environment
const GOOGLE_CLIENT_ID = import.meta.env.VITE_OAUTH_CLIENT_ID;

function ChatApp() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const [showSourceInfo, setShowSourceInfo] = useState(false);
  const [currentError, setCurrentError] = useState(null);
  const messagesEndRef = useRef(null);

  // Welcome message
  const welcomeMessage = {
    id: "welcome",
    text: "Welcome to Metropole.AI! I can help answer questions about the building, maintenance, rules, and more. How can I assist you today?",
    sender: "bot",
    sourceInfo: null,
    chunks: [],
  };

  // Display welcome message on initial load
  useEffect(() => {
    setMessages([welcomeMessage]);
  }, []);

  // Scroll to bottom of messages when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Reset chat function
  const handleReset = () => {
    setMessages([welcomeMessage]);
    setInputValue("");
    setCurrentError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      text: inputValue,
      sender: "user",
    };

    // Add user message to chat
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputValue("");
    setIsLoading(true);
    setCurrentError(null); // Clear any existing errors

    try {
      const response = await axios.post(
        `${import.meta.env.VITE_BACKEND_URL}/api/ask`,
        {
          question: userMessage.text,
          top_k: 5,
        }
      );

      if (response.data.success) {
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: Date.now().toString(),
            text: (
              response.data.answer ||
              "I'm sorry, I couldn't find an answer to that."
            ).replace(/\n+Source:.*/s, ""),
            sender: "bot",
            sourceInfo: response.data.source_info,
            chunks: response.data.chunks || [],
            prompt: response.data.prompt || "",
          },
        ]);
      } else {
        // Handle backend success=false responses
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: Date.now().toString(),
            text:
              response.data.message ||
              "Sorry, there was an error processing your request.",
            sender: "bot",
            sourceInfo: null,
            chunks: [],
          },
        ]);
      }
    } catch (error) {
      console.error("API error:", error);

      // Set error for notification instead of chat message
      const errorDetails = {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      };

      setCurrentError(errorDetails);

      // For critical errors that don't auto-logout, still show a bot message
      if (error.response?.status !== 401 && error.response?.status !== 403) {
        let errorMsg =
          "Sorry, there was an error processing your request. Please try again.";

        // Rate limit gets special handling
        if (error.response?.status === 429) {
          errorMsg =
            error.response?.data?.detail?.message ||
            error.response?.data?.message ||
            "You've reached your daily limit. Please try again tomorrow.";
        }

        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: Date.now().toString(),
            text: errorMsg,
            sender: "bot",
          },
        ]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle source info display
  const toggleSourceInfo = () => {
    setShowSourceInfo(!showSourceInfo);
  };

  if (!user) {
    return <Login />;
  }

  return (
    <div style={styles.container}>
      {/* Error Notification */}
      <ErrorNotification
        error={currentError}
        onDismiss={() => setCurrentError(null)}
        duration={currentError?.status === 429 ? 8000 : 5000} // Longer for rate limits
      />

      {/* App Header */}
      <header style={styles.header}>
        <h1 style={styles.headerTitle}>Metropole.AI</h1>
        <div style={styles.headerControls}>
          <div style={styles.sourceControls}>
            <label style={styles.sourceToggleLabel}>
              <input
                type="checkbox"
                checked={showSourceInfo}
                onChange={toggleSourceInfo}
                style={styles.sourceToggleCheckbox}
              />
              Show Sources
            </label>
          </div>
          <button onClick={handleReset} style={styles.resetButton}>
            Start Over
          </button>
          <AdminMenu />
          <button onClick={logout} style={styles.logoutButton}>
            Sign Out
          </button>
        </div>
      </header>

      {/* Chat Container */}
      <main style={styles.main}>
        {/* Message Display Area (Scrollable) */}
        <div style={styles.messageArea}>
          {messages.length === 0 ? (
            <div style={styles.emptyMessage}>
              No messages yet. Start a conversation!
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                style={{
                  ...styles.messageContainer,
                  ...(message.sender === "user"
                    ? styles.messageRight
                    : styles.messageLeft),
                }}
              >
                <div style={{ position: "relative" }}>
                  <div
                    style={{
                      ...styles.messageBubble,
                      ...(message.sender === "user"
                        ? styles.userBubble
                        : styles.botBubble),
                      ...(message.sender === "bot"
                        ? { whiteSpace: "pre-wrap" }
                        : {}),
                    }}
                  >
                    {message.text}
                  </div>

                  {/* Source Information Display */}
                  {message.sender === "bot" &&
                    showSourceInfo &&
                    message.sourceInfo && (
                      <>
                        {/* Collapsible Panel Source Display */}
                        <div style={styles.sourceInfo}>
                          <div style={styles.sourceInfoHeader}>
                            <h3 style={styles.sourceInfoTitle}>
                              Source Information
                            </h3>
                          </div>
                          <div style={styles.sourceInfoContent}>
                            {message.sourceInfo}
                          </div>
                        </div>
                      </>
                    )}

                  {/* Feedback Component */}
                  {message.sender === "bot" && message.id !== "welcome" && (
                    <Feedback answerId={message.id} />
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onFocus={() => setInputFocused(true)}
            onBlur={() => setInputFocused(false)}
            placeholder="Ask a question about the building..."
            style={{
              ...styles.input,
              ...(inputFocused ? styles.inputFocus : {}),
            }}
          />
          <button
            type="submit"
            disabled={isLoading}
            style={{
              ...styles.button,
              ...(isLoading ? styles.buttonDisabled : {}),
            }}
          >
            {isLoading ? "Sending..." : "Send"}
          </button>
        </form>
      </main>
    </div>
  );
}

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <ChatApp />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

export default App;
