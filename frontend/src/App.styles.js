// App.styles.js - Styles for the App component

const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    backgroundColor: '#f3f4f6'
  },
  header: {
    backgroundColor: '#2563eb',
    color: 'white',
    padding: '16px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  headerTitle: {
    fontSize: '1.25rem',
    fontWeight: 'bold'
  },
  resetButton: {
    backgroundColor: 'white',
    color: '#2563eb',
    border: 'none',
    borderRadius: '6px',
    padding: '6px 12px',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '0.875rem'
  },
  main: {
    flex: 1,
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    padding: '16px'
  },
  messageArea: {
    flex: 1,
    overflowY: 'auto',
    marginBottom: '16px',
    borderRadius: '8px',
    backgroundColor: 'white',
    boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    padding: '16px'
  },
  emptyMessage: {
    textAlign: 'center',
    color: '#6b7280',
    margin: '32px 0'
  },
  messageContainer: {
    marginBottom: '16px'
  },
  messageRight: {
    textAlign: 'right'
  },
  messageLeft: {
    textAlign: 'left'
  },
  messageBubble: {
    display: 'inline-block',
    maxWidth: '80%',
    padding: '8px 16px',
    borderRadius: '8px'
  },
  userBubble: {
    backgroundColor: '#2563eb',
    color: 'white',
    borderBottomRightRadius: 0
  },
  botBubble: {
    backgroundColor: '#e5e7eb',
    color: '#1f2937',
    borderBottomLeftRadius: 0
  },
  form: {
    display: 'flex',
    gap: '8px',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    padding: '8px'
  },
  input: {
    flex: 1,
    padding: '8px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    outline: 'none'
  },
  inputFocus: {
    borderColor: '#2563eb',
    boxShadow: '0 0 0 2px rgba(37, 99, 235, 0.2)'
  },
  button: {
    padding: '8px 16px',
    borderRadius: '6px',
    backgroundColor: '#2563eb',
    color: 'white',
    border: 'none',
    cursor: 'pointer',
    transition: 'background-color 0.2s'
  },
  buttonHover: {
    backgroundColor: '#1d4ed8'
  },
  buttonDisabled: {
    backgroundColor: '#93c5fd',
    cursor: 'not-allowed'
  }
};

export default styles;
