import { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import styles from './App.styles.js'

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [inputFocused, setInputFocused] = useState(false)
  const [showSourceInfo, setShowSourceInfo] = useState(false)
  const [sourceDisplayMode, setSourceDisplayMode] = useState('tooltip') // 'tooltip', 'panel', or 'footer'
  const messagesEndRef = useRef(null)

  // Welcome message
  const welcomeMessage = {
    id: 'welcome',
    text: 'Welcome to Metropole.AI! I can help answer questions about the building, maintenance, rules, and more. How can I assist you today?',
    sender: 'bot',
    sourceInfo: null,
    chunks: []
  }

  // Display welcome message on initial load
  useEffect(() => {
    setMessages([welcomeMessage])
  }, [])

  // Scroll to bottom of messages when messages change
  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  // Reset chat function
  const handleReset = () => {
    setMessages([welcomeMessage])
    setInputValue('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      sender: 'user'
    }

    // Add user message to chat
    setMessages(prevMessages => [...prevMessages, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // Send request to backend API
      const response = await axios.post(`${import.meta.env.BACKEND_API_URL}/api/ask`, {
        question: userMessage.text,
        top_k: 5
      })

      // Check if the request was successful
      if (response.data.success) {
        // Add bot response to chat
        setMessages(prevMessages => [
          ...prevMessages,
          {
            id: Date.now(),
            text: response.data.answer || "I'm sorry, I couldn't find an answer to that.",
            sender: 'bot',
            sourceInfo: response.data.source_info,
            chunks: response.data.chunks || []
          }
        ])
      } else {
        // Handle unsuccessful response
        setMessages(prevMessages => [
          ...prevMessages,
          {
            id: Date.now(),
            text: response.data.message || "Sorry, there was an error processing your request.",
            sender: 'bot',
            sourceInfo: null,
            chunks: []
          }
        ])
      }
    } catch (error) {   
      console.error('Error calling API:', error)
      // Add error message to chat
      setMessages(prevMessages => [
        ...prevMessages,
        {
          id: Date.now(),
          text: "Sorry, there was an error processing your request. Please try again.",
          sender: 'bot'
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  // Toggle source info display
  const toggleSourceInfo = () => {
    setShowSourceInfo(!showSourceInfo);
  }

  // Change source display mode
  const changeSourceDisplayMode = (mode) => {
    setSourceDisplayMode(mode);
  }

  // Cycle through display modes
  const cycleDisplayMode = () => {
    const modes = ['tooltip', 'panel', 'footer'];
    const currentIndex = modes.indexOf(sourceDisplayMode);
    const nextIndex = (currentIndex + 1) % modes.length;
    setSourceDisplayMode(modes[nextIndex]);
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
            {showSourceInfo && (
              <div style={styles.displayModeControls}>
                <span style={styles.displayModeLabel}>Mode: {sourceDisplayMode}</span>
                <button 
                  onClick={cycleDisplayMode}
                  style={styles.cycleButton}
                >
                  Change Mode
                </button>
              </div>
            )}
          </div>
          <button 
            onClick={handleReset} 
            style={styles.resetButton}
          >
            Start Over
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
            messages.map(message => (
              <div 
                key={message.id}
                style={{
                  ...styles.messageContainer,
                  ...(message.sender === 'user' ? styles.messageRight : styles.messageLeft)
                }}
              >
                <div style={{ position: 'relative' }}>
                  <div 
                    style={{
                      ...styles.messageBubble,
                      ...(message.sender === 'user' ? styles.userBubble : styles.botBubble),
                      ...(message.sender === 'bot' ? { whiteSpace: 'pre-wrap' } : {})
                    }}
                  >
                    {message.text}
                  </div>
                  
                  {/* Source Information Display */}
                  {message.sender === 'bot' && showSourceInfo && message.sourceInfo && (
                    <>
                      {/* Tooltip Source Display */}
                      {sourceDisplayMode === 'tooltip' && (
                        <div style={styles.sourceTooltipTrigger} title={message.sourceInfo}>
                          ℹ️ Source
                        </div>
                      )}
                      
                      {/* Collapsible Panel Source Display */}
                      {sourceDisplayMode === 'panel' && (
                        <details style={styles.sourcePanel}>
                          <summary style={styles.sourcePanelSummary}>Source Information</summary>
                          <div style={styles.sourcePanelContent}>
                            {message.chunks.map((chunk, index) => (
                              <div key={index} style={styles.sourceChunk}>
                                <strong>Chunk ID:</strong> {chunk.metadata?.chunk_id || 'Unknown'}<br />
                                <strong>Section:</strong> {chunk.metadata?.section_header || 'N/A'}<br />
                                <strong>Page:</strong> {chunk.metadata?.page_title || 'Unknown'}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                      
                      {/* Footer Source Display */}
                      {sourceDisplayMode === 'footer' && (
                        <div style={styles.sourceFooter}>
                          <div style={styles.sourceFooterTitle}>Sources:</div>
                          {message.chunks.map((chunk, index) => (
                            <div key={index} style={styles.sourceFooterItem}>
                              {chunk.metadata?.chunk_id || 'Unknown'} 
                              {chunk.metadata?.section_header ? ` (${chunk.metadata.section_header})` : ''}
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Form */}
        <form 
          onSubmit={handleSubmit}
          style={styles.form}
        >
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onFocus={() => setInputFocused(true)}
            onBlur={() => setInputFocused(false)}
            placeholder="Ask a question about the building..."
            style={{
              ...styles.input,
              ...(inputFocused ? styles.inputFocus : {})
            }}
          />
          <button
            type="submit"
            disabled={isLoading}
            style={{
              ...styles.button,
              ...(isLoading ? styles.buttonDisabled : {})
            }}
          >
            {isLoading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </main>
    </div>
  )
}

export default App
