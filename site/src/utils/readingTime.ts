/**
 * Reading time calculation for MDX paper content
 * Uses industry-standard 200 words per minute
 */

import readingTime from 'reading-time'

export interface ReadingTimeResult {
  text: string       // "5 min read"
  minutes: number    // 5.2
  time: number       // milliseconds
  words: number      // 1040
}

/**
 * Calculate reading time from MDX content
 * @param content - Raw MDX content (including frontmatter)
 * @returns Reading time statistics
 */
export function calculateReadingTime(content: string): ReadingTimeResult {
  return readingTime(content)
}

/**
 * Format reading time for display
 * @param minutes - Reading time in minutes
 * @returns Formatted string (e.g., "5 min read", "< 1 min read")
 */
export function formatReadingTime(minutes: number): string {
  const roundedMinutes = Math.ceil(minutes)

  if (roundedMinutes < 1) {
    return '< 1 min read'
  }

  return `${roundedMinutes} min read`
}

/**
 * Get reading time estimate based on word count
 * @param wordCount - Number of words in content
 * @param wordsPerMinute - Reading speed (default: 200 wpm)
 * @returns Reading time in minutes
 */
export function estimateReadingTime(
  wordCount: number,
  wordsPerMinute: number = 200
): number {
  return wordCount / wordsPerMinute
}

/**
 * Calculate difficulty-adjusted reading time
 * Beginner papers may take longer to read
 */
export function adjustReadingTimeByDifficulty(
  baseMinutes: number,
  difficulty: 'beginner' | 'intermediate' | 'advanced'
): number {
  const multipliers = {
    beginner: 1.0,      // No adjustment
    intermediate: 1.2,  // 20% longer
    advanced: 1.5       // 50% longer
  }

  return baseMinutes * multipliers[difficulty]
}
