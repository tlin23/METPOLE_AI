// App.styles.js - Styles for the App component

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    backgroundColor: "#f3f4f6",
  },
  header: {
    backgroundColor: "#2563eb",
    color: "white",
    padding: "16px",
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerTitle: {
    fontSize: "1.25rem",
    fontWeight: "bold",
  },
  headerControls: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },
  sourceControls: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  sourceToggleLabel: {
    display: "flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "0.875rem",
    cursor: "pointer",
  },
  sourceToggleCheckbox: {
    cursor: "pointer",
  },
  displayModeControls: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  displayModeLabel: {
    fontSize: "0.75rem",
    color: "white",
    textTransform: "capitalize",
  },
  cycleButton: {
    padding: "4px 8px",
    borderRadius: "4px",
    border: "1px solid white",
    backgroundColor: "transparent",
    color: "white",
    fontSize: "0.75rem",
    cursor: "pointer",
  },
  resetButton: {
    backgroundColor: "white",
    color: "#2563eb",
    border: "none",
    borderRadius: "6px",
    padding: "6px 12px",
    cursor: "pointer",
    fontWeight: "bold",
    fontSize: "0.875rem",
  },
  logoutButton: {
    backgroundColor: "#ef4444",
    color: "white",
    border: "none",
    borderRadius: "6px",
    padding: "6px 12px",
    cursor: "pointer",
    fontWeight: "bold",
    fontSize: "0.875rem",
    marginLeft: "8px",
  },
  main: {
    flex: 1,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    padding: "16px",
  },
  messageArea: {
    flex: 1,
    overflowY: "auto",
    marginBottom: "16px",
    borderRadius: "8px",
    backgroundColor: "white",
    boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)",
    padding: "16px",
  },
  emptyMessage: {
    textAlign: "center",
    color: "#6b7280",
    margin: "32px 0",
  },
  messageContainer: {
    marginBottom: "16px",
  },
  messageRight: {
    textAlign: "right",
  },
  messageLeft: {
    textAlign: "left",
  },
  messageBubble: {
    display: "inline-block",
    maxWidth: "80%",
    padding: "8px 16px",
    borderRadius: "8px",
  },
  userBubble: {
    backgroundColor: "#2563eb",
    color: "white",
    borderBottomRightRadius: 0,
  },
  botBubble: {
    backgroundColor: "#e5e7eb",
    color: "#1f2937",
    borderBottomLeftRadius: 0,
  },
  form: {
    display: "flex",
    gap: "8px",
    backgroundColor: "white",
    borderRadius: "8px",
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
    padding: "8px",
  },
  input: {
    flex: 1,
    padding: "8px",
    border: "1px solid #d1d5db",
    borderRadius: "6px",
    outline: "none",
  },
  inputFocus: {
    borderColor: "#2563eb",
    boxShadow: "0 0 0 2px rgba(37, 99, 235, 0.2)",
  },
  button: {
    padding: "8px 16px",
    borderRadius: "6px",
    backgroundColor: "#2563eb",
    color: "white",
    border: "none",
    cursor: "pointer",
    transition: "background-color 0.2s",
  },
  buttonHover: {
    backgroundColor: "#1d4ed8",
  },
  buttonDisabled: {
    backgroundColor: "#93c5fd",
    cursor: "not-allowed",
  },

  // Source information display styles
  sourceTooltipTrigger: {
    position: "absolute",
    bottom: "-18px",
    left: "8px",
    fontSize: "0.75rem",
    color: "#6b7280",
    cursor: "help",
    backgroundColor: "#f3f4f6",
    padding: "2px 6px",
    borderRadius: "4px",
    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.1)",
  },

  sourcePanel: {
    marginTop: "8px",
    backgroundColor: "#f9fafb",
    borderRadius: "6px",
    padding: "4px",
    fontSize: "0.75rem",
    color: "#4b5563",
    maxWidth: "100%",
  },

  sourcePanelSummary: {
    cursor: "pointer",
    fontWeight: "bold",
    padding: "4px",
  },

  sourcePanelContent: {
    padding: "8px",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },

  sourceChunk: {
    backgroundColor: "white",
    padding: "8px",
    borderRadius: "4px",
    boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
    fontSize: "0.75rem",
    lineHeight: "1.4",
  },

  sourceFooter: {
    marginTop: "8px",
    backgroundColor: "#f9fafb",
    borderRadius: "6px",
    padding: "8px",
    fontSize: "0.75rem",
    color: "#4b5563",
  },

  sourceFooterTitle: {
    fontWeight: "bold",
    marginBottom: "4px",
  },

  sourceFooterItem: {
    fontSize: "0.7rem",
    marginBottom: "2px",
    color: "#6b7280",
  },

  sourceInfo: {
    marginTop: "8px",
    border: "1px solid #ddd",
    borderRadius: "4px",
    overflow: "hidden",
  },

  sourceInfoHeader: {
    backgroundColor: "#f5f5f5",
    padding: "8px 12px",
    borderBottom: "1px solid #ddd",
  },

  sourceInfoTitle: {
    margin: 0,
    fontSize: "14px",
    fontWeight: "500",
    color: "#333",
  },

  sourceInfoContent: {
    padding: "12px",
    fontSize: "14px",
    color: "#666",
    whiteSpace: "pre-wrap",
  },
};

export default styles;
