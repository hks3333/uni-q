// app/page.js
'use client'
import './chat.css'
import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import ResearchPlan from '@/components/ResearchPlan'
import ReactMarkdown from 'react-markdown'
import { useAuth } from '../contexts/AuthContext'

export default function ChatPage() {
  const { user, loading: authLoading, logout, getToken, isAuthenticated } = useAuth()
  const router = useRouter()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [researchMode, setResearchMode] = useState(false)
  const [researchState, setResearchState] = useState(null) // 'planning', 'executing', 'synthesizing'
  const [currentPlan, setCurrentPlan] = useState(null)
  const abortRef = useRef(null)
  const messagesEndRef = useRef(null)
  const messageContainerRef = useRef(null)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login')
    }
  }, [authLoading, isAuthenticated, router])

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current && isAuthenticated) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' }) 
    }
  }, [messages, isAuthenticated])

  // Scroll to bottom when loading state changes
  useEffect(() => {
    if (loading && messageContainerRef.current && isAuthenticated) {
      messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight
    }
  }, [loading, isAuthenticated])

  // Show loading while checking authentication
  if (authLoading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading...</p>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return null
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)
    
    // Add user message immediately
    setMessages((msgs) => [...msgs, { role: 'user', content: userMessage }])
    
    if (researchMode) {
      await handleResearchQuery(userMessage)
    } else {
      await handleRegularQuery(userMessage)
    }
  }

  const handleRegularQuery = async (userMessage) => {
    let responseText = ''
    try {
      const controller = new AbortController()
      abortRef.current = controller
      
      const token = getToken()
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ question: userMessage }),
        signal: controller.signal,
      })
      
      if (!res.body) throw new Error('No response body')
      
      const reader = res.body.getReader()
      let done = false
      
      // Add bot message placeholder
      setMessages((msgs) => [...msgs, { role: 'bot', content: '' }])
      
      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        
        if (value) {
          const chunk = new TextDecoder().decode(value)
          responseText += chunk
          
          setMessages((msgs) => {
            const newMsgs = [...msgs]
            const lastMessage = newMsgs[newMsgs.length - 1]
            
            if (lastMessage && lastMessage.role === 'bot') {
              lastMessage.content = responseText
            }
            
            return newMsgs
        })
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setMessages((msgs) => {
          const newMsgs = [...msgs]
          const lastMessage = newMsgs[newMsgs.length - 1]
          if (lastMessage && lastMessage.role === 'bot') {
            lastMessage.content = 'Response cancelled.'
          }
          return newMsgs
        })
      } else {
        setMessages((msgs) => {
          const newMsgs = [...msgs]
          const lastMessage = newMsgs[newMsgs.length - 1]
          if (lastMessage && lastMessage.role === 'bot') {
            lastMessage.content = '⚠️ Failed to get response from model. Please try again.'
          }
          return newMsgs
        })
      }
    } finally {
      setLoading(false)
      abortRef.current = null
    }
  }

  const handleResearchQuery = async (userMessage) => {
    try {
      setResearchState('planning')
      
      // Generate research plan
      const planRes = await fetch('/api/research/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage }),
      })
      
      if (!planRes.ok) throw new Error('Failed to generate research plan')
      
      const planData = await planRes.json()
      setCurrentPlan(planData.plan)
      
      // Add bot message with plan
      setMessages((msgs) => [...msgs, { 
        role: 'bot', 
        content: 'I\'ve created a detailed research plan for your query. Please review it below.',
        type: 'research_plan',
        plan: planData.plan
      }])
      
    } catch (error) {
      setMessages((msgs) => [...msgs, { 
        role: 'bot', 
        content: `⚠️ Failed to generate research plan: ${error.message}` 
      }])
    } finally {
      setLoading(false)
      setResearchState(null)
    }
  }

  const handlePlanRefine = (refinedPlan) => {
    setCurrentPlan(refinedPlan)
    setMessages((msgs) => {
      const newMsgs = [...msgs]
      const lastMessage = newMsgs[newMsgs.length - 1]
      if (lastMessage && lastMessage.type === 'research_plan') {
        lastMessage.plan = refinedPlan
      }
      return newMsgs
    })
  }

  const handlePlanExecute = async (plan) => {
    try {
      setResearchState('executing')
      setLoading(true)
      
      // Execute research plan
      const executeRes = await fetch('/api/research/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: messages[messages.length - 2].content, // Get the original query
          plan: plan 
        }),
      })
      
      if (!executeRes.ok) throw new Error('Failed to execute research plan')
      
      const executeData = await executeRes.json()
      
      // Skip showing search results, go directly to synthesis
      await handleSynthesis(executeData.sources, plan)
      
    } catch (error) {
      setMessages((msgs) => [...msgs, { 
        role: 'bot', 
        content: `⚠️ Failed to execute research plan: ${error.message}` 
      }])
      setLoading(false)
      setResearchState(null)
    }
  }

  const handleSynthesis = async (searchResults, plan) => {
    try {
      setResearchState('synthesizing')
      
      const originalQuery = messages.find(msg => msg.role === 'user' && !msg.type)?.content
      
      // Stream synthesis response
      const res = await fetch('/api/research/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: originalQuery,
          plan: plan,
          search_results: searchResults
        }),
      })
      
      if (!res.body) throw new Error('No response body')
      
      const reader = res.body.getReader()
      let done = false
      let responseText = ''
      
      // Add bot message placeholder
      setMessages((msgs) => [...msgs, { role: 'bot', content: '', type: 'synthesis' }])
      
      while (!done) {
        const { value, done: doneReading } = await reader.read()
        done = doneReading
        
        if (value) {
          const chunk = new TextDecoder().decode(value)
          responseText += chunk
          
          setMessages((msgs) => {
            const newMsgs = [...msgs]
            const lastMessage = newMsgs[newMsgs.length - 1]
            
            if (lastMessage && lastMessage.role === 'bot' && lastMessage.type === 'synthesis') {
              lastMessage.content = responseText
            }
            
            return newMsgs
        })
        }
      }
      
    } catch (error) {
      setMessages((msgs) => [...msgs, { 
        role: 'bot', 
        content: `⚠️ Failed to synthesize research results: ${error.message}` 
      }])
    } finally {
      setLoading(false)
      setResearchState(null)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage()
  }

  const handleStop = () => {
    if (abortRef.current) {
      abortRef.current.abort()
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const toggleResearchMode = () => {
    setResearchMode(!researchMode)
    setResearchState(null)
    setCurrentPlan(null)
  }

  return (
    <div className={`chat-container ${researchMode ? 'research-mode' : ''}`}>
      <div className="topbar-wrapper">
        <div className="chat-header">
          <h1>Uni-Q Chat</h1>
          <div className="user-info">
            <span className="user-name">{user.name}</span>
            <span className="user-details">{user.department} • {user.semester}</span>
            <button onClick={logout} className="logout-btn">Logout</button>
          </div>
        </div>
      </div>

      <div className="message-container" ref={messageContainerRef}>
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>
              Welcome to Uni-Q Chat! 
              {researchMode 
                ? ' Research mode is active. Ask me to research any topic and I\'ll create a detailed plan, search the web, and provide a comprehensive analysis.'
                : ' Ask me anything about your uploaded documents.'
              }
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.role === 'bot' ? (
                <ReactMarkdown>{msg.content || ''}</ReactMarkdown>
              ) : (
                msg.content || (
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                )
              )}
              {/* Render research plan */}
              {msg.type === 'research_plan' && msg.plan && (
                <ResearchPlan 
                  plan={msg.plan} 
                  onPlanRefine={handlePlanRefine}
                  onExecute={handlePlanExecute}
                />
              )}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message bot">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              {researchState && (
                <div className="mt-2 text-sm text-gray-600">
                  {researchState === 'planning' && 'Creating detailed research plan...'}
                  {researchState === 'executing' && 'Searching the web for relevant sources...'}
                  {researchState === 'synthesizing' && 'Synthesizing research findings...'}
                </div>
              )}
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="input-area">
        <div className="input-row">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={researchMode ? "Ask me to research any topic..." : "Ask something about your PDF..."}
            disabled={loading}
            autoComplete="off"
            className="input"
          />
          {loading ? (
            <button 
              type="button" 
              onClick={handleStop}
              title="Stop generation"
              className="btn stop-btn"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
              </svg>
            </button>
          ) : (
            <button 
              type="submit" 
              disabled={!input.trim()}
              title="Send message"
              className="btn send-btn"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 2L11 13"/>
                <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
              </svg>
            </button>
          )}
        </div>
        <button 
          type="button"
          onClick={toggleResearchMode}
          className={`research-toggle-minimal${researchMode ? ' active' : ''}`}
          title={researchMode ? "Switch to Document Mode" : "Switch to Research Mode"}
        >
          Research
        </button>
      </form>
    </div>
  )
}