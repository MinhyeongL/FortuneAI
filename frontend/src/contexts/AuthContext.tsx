"use client"

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

interface User {
  id: string  // UUID
  email: string
  name: string
  birth_year: number
  birth_month: number
  birth_day: number
  birth_hour: number
  birth_minute: number
  is_male: boolean
  is_leap_month: boolean
  birth_location?: string
  created_at: string
  last_login?: string
  is_active: boolean
  premium_until?: string
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (token: string) => Promise<void>
  logout: () => void
  updateUser: (userData: Partial<User>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = !!user

  // 토큰으로부터 사용자 정보 가져오기
  const fetchUserFromToken = async (token: string): Promise<User | null> => {
    try {
      const response = await fetch('http://localhost:8000/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch user')
      }

      return await response.json()
    } catch (error) {
      console.error('Error fetching user:', error)
      return null
    }
  }

  // 로그인
  const login = async (token: string) => {
    try {
      localStorage.setItem('access_token', token)
      const userData = await fetchUserFromToken(token)
      setUser(userData)
    } catch (error) {
      console.error('Login error:', error)
      localStorage.removeItem('access_token')
    }
  }

  // 로그아웃
  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
  }

  // 사용자 정보 업데이트
  const updateUser = (userData: Partial<User>) => {
    setUser(prev => prev ? { ...prev, ...userData } : null)
  }

  // 페이지 로드 시 토큰 확인
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('access_token')
      
      if (token) {
        const userData = await fetchUserFromToken(token)
        if (userData) {
          setUser(userData)
        } else {
          // 토큰이 유효하지 않으면 제거
          localStorage.removeItem('access_token')
        }
      }
      
      setIsLoading(false)
    }

    initializeAuth()
  }, [])

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    logout,
    updateUser,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export type { User, AuthContextType }