import { describe, expect, it } from 'vitest'
import { ApiError } from '../services/api'

describe('ask and capture error mapping', () => {
  it('keeps network failures user-facing', () => {
    const error = new ApiError("Nura couldn't connect to the AI service. Please check your connection.", 0)
    expect(error.message).toMatch(/check your connection/i)
    expect(error.message).not.toMatch(/axios|fetch failed|500/i)
  })
})
