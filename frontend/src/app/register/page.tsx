"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"
import { useToast } from "@/hooks/use-toast"

export default function RegisterPage() {
  const router = useRouter()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    name: "",
    birth_year: "",
    birth_month: "",
    birth_day: "",
    birth_hour: "",
    birth_minute: "0",
    is_male: true,
    is_leap_month: false,
    birth_location: "",
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // 비밀번호 확인
    if (formData.password !== formData.confirmPassword) {
      toast({
        title: "회원가입 실패",
        description: "비밀번호가 일치하지 않습니다.",
        variant: "destructive",
      })
      setIsLoading(false)
      return
    }

    try {
      const requestData = {
        email: formData.email,
        password: formData.password,
        name: formData.name,
        birth_year: parseInt(formData.birth_year),
        birth_month: parseInt(formData.birth_month),
        birth_day: parseInt(formData.birth_day),
        birth_hour: parseInt(formData.birth_hour),
        birth_minute: parseInt(formData.birth_minute),
        is_male: formData.is_male,
        is_leap_month: formData.is_leap_month,
        birth_location: formData.birth_location || null,
      }

      const response = await fetch("http://localhost:8000/api/auth/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "회원가입에 실패했습니다.")
      }

      toast({
        title: "회원가입 성공",
        description: "계정이 생성되었습니다. 로그인 페이지로 이동합니다.",
      })

      // 로그인 페이지로 리다이렉트
      router.push("/login")
    } catch (error) {
      toast({
        title: "회원가입 실패",
        description: error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">회원가입</CardTitle>
          <p className="text-sm text-muted-foreground text-center">
            새 계정을 만들어 사주 상담을 시작하세요
          </p>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">이메일 *</Label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="이메일을 입력하세요"
                value={formData.email}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">비밀번호 *</Label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="비밀번호를 입력하세요"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">비밀번호 확인 *</Label>
              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="비밀번호를 다시 입력하세요"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">이름 *</Label>
              <Input
                id="name"
                name="name"
                type="text"
                placeholder="이름을 입력하세요"
                value={formData.name}
                onChange={handleChange}
                required
                disabled={isLoading}
              />
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="space-y-2">
                <Label htmlFor="birth_year">년도 *</Label>
                <Input
                  id="birth_year"
                  name="birth_year"
                  type="number"
                  placeholder="1990"
                  min="1900"
                  max="2100"
                  value={formData.birth_year}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="birth_month">월 *</Label>
                <Input
                  id="birth_month"
                  name="birth_month"
                  type="number"
                  placeholder="5"
                  min="1"
                  max="12"
                  value={formData.birth_month}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="birth_day">일 *</Label>
                <Input
                  id="birth_day"
                  name="birth_day"
                  type="number"
                  placeholder="15"
                  min="1"
                  max="31"
                  value={formData.birth_day}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-2">
                <Label htmlFor="birth_hour">시 *</Label>
                <Input
                  id="birth_hour"
                  name="birth_hour"
                  type="number"
                  placeholder="14"
                  min="0"
                  max="23"
                  value={formData.birth_hour}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="birth_minute">분 *</Label>
                <Input
                  id="birth_minute"
                  name="birth_minute"
                  type="number"
                  placeholder="30"
                  min="0"
                  max="59"
                  value={formData.birth_minute}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="is_male">성별 *</Label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="is_male"
                    value="true"
                    checked={formData.is_male === true}
                    onChange={() => setFormData(prev => ({ ...prev, is_male: true }))}
                    disabled={isLoading}
                    className="cursor-pointer"
                  />
                  <span>남성</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="is_male"
                    value="false"
                    checked={formData.is_male === false}
                    onChange={() => setFormData(prev => ({ ...prev, is_male: false }))}
                    disabled={isLoading}
                    className="cursor-pointer"
                  />
                  <span>여성</span>
                </label>
              </div>
            </div>
            <div className="space-y-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  name="is_leap_month"
                  checked={formData.is_leap_month}
                  onChange={(e) => setFormData(prev => ({ ...prev, is_leap_month: e.target.checked }))}
                  disabled={isLoading}
                  className="cursor-pointer"
                />
                <span className="text-sm">윤달 여부</span>
              </label>
            </div>
            <div className="space-y-2">
              <Label htmlFor="birth_location">출생지 (선택사항)</Label>
              <Input
                id="birth_location"
                name="birth_location"
                type="text"
                placeholder="서울"
                value={formData.birth_location}
                onChange={handleChange}
                disabled={isLoading}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full" 
              disabled={isLoading}
            >
              {isLoading ? "가입 중..." : "회원가입"}
            </Button>
            <p className="text-sm text-center text-muted-foreground">
              이미 계정이 있으신가요?{" "}
              <Link href="/login" className="text-primary hover:underline">
                로그인
              </Link>
            </p>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}