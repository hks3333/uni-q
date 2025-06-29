// context/UserContext.js
import { createContext, useState } from 'react'

export const UserContext = createContext()  // Must be exported

export function UserProvider({ children }) {  // Must be exported
  const [user, setUser] = useState(null)
  
  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  )
}