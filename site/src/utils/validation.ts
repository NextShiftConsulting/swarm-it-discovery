/**
 * MDX Frontmatter validation for RSCT-certified papers
 * Ensures quality gates (κ-gate) and RSN simplex compliance
 */

export interface PaperFrontmatter {
  // Core metadata
  title: string
  arxiv_id: string
  authors: string[]
  published_date: string
  go_live_date: string

  // RSCT Certification (quality gates)
  kappa: number            // κ-gate score (0-1)
  rsn_score: string        // "R/S/N" format (e.g., "0.75/0.82/0.43")
  R: number                // Relevance (0-1)
  S: number                // Stability (0-1)
  N: number                // Novelty (0-1)

  // Classification
  tags: string[]
  primary_topic: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'

  // Content metadata
  abstract: string
  tldr?: string
  reading_time?: number    // Minutes (auto-calculated)
  word_count?: number      // Words (auto-calculated)

  // Links
  arxiv_url: string
  pdf_url?: string
  github_url?: string

  // Status
  status: 'staging' | 'live'
  featured?: boolean
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * Validates paper frontmatter against RSCT requirements
 * @param frontmatter - Raw frontmatter object from MDX
 * @returns Validation result with errors and warnings
 */
export function validatePaperFrontmatter(
  frontmatter: any
): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // === Required Fields ===
  if (!frontmatter.title) {
    errors.push('Missing required field: title')
  }
  if (!frontmatter.arxiv_id) {
    errors.push('Missing required field: arxiv_id')
  }
  if (!Array.isArray(frontmatter.authors) || frontmatter.authors.length === 0) {
    errors.push('Missing or empty authors array')
  }
  if (!frontmatter.published_date) {
    errors.push('Missing required field: published_date')
  }
  if (!frontmatter.go_live_date) {
    errors.push('Missing required field: go_live_date')
  }
  if (!frontmatter.abstract) {
    errors.push('Missing required field: abstract')
  }
  if (!frontmatter.arxiv_url) {
    errors.push('Missing required field: arxiv_url')
  }
  if (!frontmatter.status) {
    errors.push('Missing required field: status')
  }

  // === RSCT Certification Validation ===

  // Kappa (κ-gate) validation
  if (typeof frontmatter.kappa !== 'number') {
    errors.push('Invalid kappa: must be a number')
  } else {
    if (frontmatter.kappa < 0 || frontmatter.kappa > 1) {
      errors.push(`Invalid kappa: ${frontmatter.kappa} (must be between 0 and 1)`)
    }
    if (frontmatter.kappa < 0.7) {
      warnings.push(`Low kappa score: ${frontmatter.kappa} (recommended ≥ 0.7)`)
    }
  }

  // RSN validation (simplex constraint: R+S+N=1)
  if (typeof frontmatter.R !== 'number' ||
      typeof frontmatter.S !== 'number' ||
      typeof frontmatter.N !== 'number') {
    errors.push('Invalid RSN values: R, S, and N must be numbers')
  } else {
    const rsnSum = frontmatter.R + frontmatter.S + frontmatter.N
    if (Math.abs(rsnSum - 1.0) > 0.01) {
      errors.push(
        `RSN values must sum to 1.0 (simplex constraint). ` +
        `Got R=${frontmatter.R}, S=${frontmatter.S}, N=${frontmatter.N}, sum=${rsnSum.toFixed(3)}`
      )
    }

    // Individual RSN bounds
    if (frontmatter.R < 0 || frontmatter.R > 1) {
      errors.push(`Invalid R: ${frontmatter.R} (must be between 0 and 1)`)
    }
    if (frontmatter.S < 0 || frontmatter.S > 1) {
      errors.push(`Invalid S: ${frontmatter.S} (must be between 0 and 1)`)
    }
    if (frontmatter.N < 0 || frontmatter.N > 1) {
      errors.push(`Invalid N: ${frontmatter.N} (must be between 0 and 1)`)
    }
  }

  // RSN score string format validation
  if (!frontmatter.rsn_score) {
    errors.push('Missing required field: rsn_score')
  } else if (typeof frontmatter.rsn_score === 'string') {
    const match = frontmatter.rsn_score.match(/^(\d+\.\d+)\/(\d+\.\d+)\/(\d+\.\d+)$/)
    if (!match) {
      errors.push(
        `Invalid rsn_score format: "${frontmatter.rsn_score}" ` +
        `(expected "R/S/N" format, e.g., "0.75/0.82/0.43")`
      )
    } else {
      // Verify rsn_score matches R/S/N values
      const [, rStr, sStr, nStr] = match
      const scoreR = parseFloat(rStr)
      const scoreS = parseFloat(sStr)
      const scoreN = parseFloat(nStr)

      if (Math.abs(scoreR - frontmatter.R) > 0.01 ||
          Math.abs(scoreS - frontmatter.S) > 0.01 ||
          Math.abs(scoreN - frontmatter.N) > 0.01) {
        warnings.push(
          `rsn_score "${frontmatter.rsn_score}" does not match R/S/N values ` +
          `(${frontmatter.R}/${frontmatter.S}/${frontmatter.N})`
        )
      }
    }
  }

  // === Classification Validation ===
  if (!Array.isArray(frontmatter.tags) || frontmatter.tags.length === 0) {
    errors.push('Must have at least one tag')
  }
  if (!frontmatter.primary_topic) {
    errors.push('Missing required field: primary_topic')
  }
  if (!frontmatter.difficulty) {
    errors.push('Missing required field: difficulty')
  } else if (!['beginner', 'intermediate', 'advanced'].includes(frontmatter.difficulty)) {
    errors.push(
      `Invalid difficulty: "${frontmatter.difficulty}" ` +
      `(must be "beginner", "intermediate", or "advanced")`
    )
  }

  // === Status Validation ===
  if (frontmatter.status && !['staging', 'live'].includes(frontmatter.status)) {
    errors.push(
      `Invalid status: "${frontmatter.status}" (must be "staging" or "live")`
    )
  }

  // === Date Validation ===
  if (frontmatter.published_date && !isValidDate(frontmatter.published_date)) {
    errors.push(`Invalid published_date format: "${frontmatter.published_date}" (expected YYYY-MM-DD)`)
  }
  if (frontmatter.go_live_date && !isValidDate(frontmatter.go_live_date)) {
    errors.push(`Invalid go_live_date format: "${frontmatter.go_live_date}" (expected YYYY-MM-DD)`)
  }

  // === URL Validation ===
  if (frontmatter.arxiv_url && !frontmatter.arxiv_url.startsWith('https://arxiv.org/')) {
    errors.push(`Invalid arxiv_url: must start with "https://arxiv.org/"`)
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * Determines quality tier based on κ-gate score
 */
export function getQualityTier(kappa: number): string {
  if (kappa >= 0.9) return 'exceptional'  // Gold tier
  if (kappa >= 0.8) return 'high-quality' // Silver tier
  if (kappa >= 0.7) return 'certified'    // Bronze tier
  return 'pending'                        // Below certification threshold
}

/**
 * Gets quality tier color for badges
 */
export function getQualityColor(tier: string): string {
  const colors: Record<string, string> = {
    exceptional: 'text-amber-400',   // Gold
    'high-quality': 'text-gray-300', // Silver
    certified: 'text-orange-700',    // Bronze
    pending: 'text-gray-500'         // Gray
  }
  return colors[tier] || colors.pending
}

/**
 * Simple date validation (YYYY-MM-DD format)
 */
function isValidDate(dateStr: string): boolean {
  const match = dateStr.match(/^(\d{4})-(\d{2})-(\d{2})$/)
  if (!match) return false

  const [, year, month, day] = match
  const date = new Date(parseInt(year), parseInt(month) - 1, parseInt(day))

  return date.getFullYear() === parseInt(year) &&
         date.getMonth() === parseInt(month) - 1 &&
         date.getDate() === parseInt(day)
}
