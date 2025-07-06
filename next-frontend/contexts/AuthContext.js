'use client'
import { createContext, useContext, useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  useEffect(() => {
    // Check for existing token on app load
    const token = localStorage.getItem('authToken')
    const studentData = localStorage.getItem('user')
    
    if (token && studentData) {
      try {
        const student = JSON.parse(studentData)
        setUser(student)
      } catch (error) {
        console.error('Error parsing student data:', error)
        logout()
      }
    }
    
    setLoading(false)
  }, [])

  const login = async (rollNo, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ roll_no: rollNo, password }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      const data = await response.json()
      
      // Store token and user data
      localStorage.setItem('authToken', data.token)
      localStorage.setItem('user', JSON.stringify(data.student))
      
      setUser(data.student)
      
      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      return { success: false, error: error.message }
    }
  }

  const logout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('user')
    setUser(null)
    router.replace('/login')
  }

  const getToken = () => {
    return localStorage.getItem('authToken')
  }

  const value = {
    user,
    loading,
    login,
    logout,
    getToken,
    isAuthenticated: !!user,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 