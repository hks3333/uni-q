// app/page.js
'use client'
import './chat.css'
import { useEffect, useRef, useState } from 'react'
import { loadMemoryVectorStore, queryLlama3, checkOllamaServer } from '@/lib/ollama'
import ResearchPlan from '@/components/ResearchPlan'

export default function ChatPage() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [researchMode, setResearchMode] = useState(false)
  const [researchState, setResearchState] = useState(null) // 'planning', 'executing', 'synthesizing'
  const [currentPlan, setCurrentPlan] = useState(null)
  const abortRef = useRef(null)
  const messagesEndRef = useRef(null)
  const messageContainerRef = useRef(null)
 
  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // Scroll to bottom when loading state changes
  useEffect(() => {
    if (loading && messageContainerRef.current) {
      messageContainerRef.current.scrollTop = messageContainerRef.current.scrollHeight
    }
  }, [loading])

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
      
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      <div className="chat-header">
        <h1>Uni-Q Chat</h1>
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
              {msg.content || (
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
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
        <div className="input-wrapper">
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
          <button 
            type="button"
            onClick={toggleResearchMode}
            className={`research-toggle ${researchMode ? 'active' : ''}`}
            title={researchMode ? "Switch to Document Mode" : "Switch to Research Mode"}
          >
            {researchMode ? '📚' : '🔍'} Research
          </button>
        </div>
        <div className="button-group">
          <button 
            type="submit" 
            disabled={loading || !input.trim()}
            title="Send message"
            className="btn"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 2L11 13"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z"/>
            </svg>
          </button>
          {loading && (
            <button 
              type="button" 
              onClick={handleStop}
              title="Stop generation"
              className="btn"
              style={{ background: '#dc2626' }}
            >
              Stop
            </button>
          )}
        </div>
      </form>
    </div>
  )
}