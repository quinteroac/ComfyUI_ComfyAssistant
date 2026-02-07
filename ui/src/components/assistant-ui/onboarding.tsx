/**
 * First-time onboarding: personality, goals, experience level.
 * Persisted via POST /api/user-context/onboarding; then chat is shown.
 */

import { useState } from 'react'
import { Button } from '@/components/ui/button'

const API_STATUS = '/api/user-context/status'
const API_ONBOARDING = '/api/user-context/onboarding'

export type OnboardingData = {
  personality: string
  goals: string
  experienceLevel: string
}

export async function fetchOnboardingStatus(): Promise<{ needsOnboarding: boolean }> {
  const res = await fetch(API_STATUS)
  if (!res.ok) return { needsOnboarding: true }
  const data = await res.json()
  return { needsOnboarding: Boolean(data?.needsOnboarding) }
}

export async function submitOnboarding(data: OnboardingData): Promise<void> {
  const res = await fetch(API_ONBOARDING, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      personality: data.personality,
      goals: data.goals,
      experienceLevel: data.experienceLevel,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.error || res.statusText)
  }
}

export async function skipOnboarding(): Promise<void> {
  const res = await fetch(API_ONBOARDING, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skip: true }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err?.error || res.statusText)
  }
}

interface OnboardingViewProps {
  onComplete: () => void
}

const EXPERIENCE_OPTIONS = [
  { value: '', label: 'Select…' },
  { value: 'novice', label: 'Novice' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
]

export function OnboardingView({ onComplete }: OnboardingViewProps) {
  const [personality, setPersonality] = useState('')
  const [goals, setGoals] = useState('')
  const [experienceLevel, setExperienceLevel] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    setError(null)
    setLoading(true)
    try {
      await submitOnboarding({ personality, goals, experienceLevel })
      onComplete()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setLoading(false)
    }
  }

  const handleSkip = async () => {
    setError(null)
    setLoading(true)
    try {
      await skipOnboarding()
      onComplete()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to skip')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col items-center justify-center overflow-auto p-6">
      <div className="w-full max-w-md space-y-6 rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <h2 className="text-xl font-semibold">Welcome to ComfyUI Assistant</h2>
        <p className="text-muted-foreground text-sm">
          Optional: set your preferences so the assistant can adapt. You can skip and edit later in the user_context folder.
        </p>

        <div className="space-y-2">
          <label className="text-sm font-medium">Personality / tone</label>
          <textarea
            className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            placeholder="e.g. more technical, didactic, or concise"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            rows={3}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Goals with ComfyUI</label>
          <textarea
            className="min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            placeholder="e.g. create images for social media, learn workflows"
            value={goals}
            onChange={(e) => setGoals(e.target.value)}
            rows={3}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium">Experience level</label>
          <select
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            value={experienceLevel}
            onChange={(e) => setExperienceLevel(e.target.value)}
          >
            {EXPERIENCE_OPTIONS.map((opt) => (
              <option key={opt.value || 'empty'} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <p className="text-destructive text-sm">{error}</p>
        )}

        <div className="flex gap-2">
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? 'Saving…' : 'Save'}
          </Button>
          <Button variant="outline" onClick={handleSkip} disabled={loading}>
            Skip
          </Button>
        </div>
      </div>
    </div>
  )
}
