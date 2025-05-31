import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Login from "./components/Login";
import "./App.css";
import styles from "./App.styles.js";

// Get Google Client ID from environment
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function ChatApp() {
  const { user, logout } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const [showSourceInfo, setShowSourceInfo] = useState(false);
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
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: "user",
    };

    // Add user message to chat
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInputValue("");
    setIsLoading(true);

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
            id: Date.now(),
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
        setMessages((prevMessages) => [
          ...prevMessages,
          {
            id: Date.now(),
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
      console.error("API error:", error.response?.data || error.message);
      let errorMsg =
        "Sorry, there was an error processing your request. Please try again.";
      if (
        error.response?.status === 429 &&
        error.response?.data?.detail?.message
      ) {
        errorMsg = error.response.data.detail.message;
      }
      setMessages((prevMessages) => [
        ...prevMessages,
        {
          id: Date.now(),
          text: errorMsg,
          sender: "bot",
        },
      ]);
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
                        {
                          <details style={styles.sourcePanel}>
                            <summary style={styles.sourcePanelSummary}>
                              Source Information
                            </summary>
                            Prompt: {message.prompt}
                            <div style={styles.sourcePanelContent}>
                              {message.chunks.map((chunk, index) => (
                                <div key={index} style={styles.sourceChunk}>
                                  <strong>Chunk ID:</strong>{" "}
                                  {chunk.metadata?.chunk_id || "Unknown"}
                                  <br />
                                  <strong>Section:</strong>{" "}
                                  {chunk.metadata?.section || "N/A"}
                                  <br />
                                  <strong>Page:</strong>{" "}
                                  {chunk.metadata?.document_title || "Unknown"}
                                  <br />
                                  <strong>Text:</strong>{" "}
                                  {chunk.text || "No text available"}
                                  <br />
                                  <strong>Relevance Score:</strong>{" "}
                                  {chunk.distance
                                    ? chunk.distance.toFixed(3)
                                    : "N/A"}
                                </div>
                              ))}
                            </div>
                          </details>
                        }
                      </>
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
