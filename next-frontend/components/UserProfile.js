// components/UserProfile.js
'use client'
import { useContext } from 'react'
import { UserContext } from '@/context/UserContext'

export default function UserProfile({ user, onLogout, visible, toggleVisibility }) {
  const { logout } = useContext(UserContext)

  const handleLogout = () => {
    logout()
    onLogout()
  }

  return (
    <div className="profile-container">
      <div className="profile-header" onClick={toggleVisibility}>
        <img src="/user-icon.png" alt="Profile" />
        <span>{user.name}</span>
      </div>
      
      {visible && (
        <div className="profile-dropdown">
          <div className="profile-info">
            <p>Department: {user.department}</p>
            <p>Semester: {user.semester}</p>
            <p>Type: {user.type}</p>
          </div>
          <button onClick={handleLogout}>Logout</button>
        </div>
      )}
    </div>
  )
}