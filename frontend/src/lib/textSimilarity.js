/**
 * Jaccard similarity between two texts.
 * Used to detect rubber-stamping (decision ≈ AI recommendation).
 */

function normalize(text) {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')  // strip combining diacriticals
    .replace(/[^\w\s]/g, '')          // remove punctuation
}

function tokenize(text) {
  return new Set(
    normalize(text)
      .split(/\s+/)
      .filter((w) => w.length > 2)
  )
}

export function jaccardSimilarity(textA, textB) {
  if (!textA || !textB) return 0
  const a = tokenize(textA)
  const b = tokenize(textB)
  if (a.size === 0 && b.size === 0) return 1
  if (a.size === 0 || b.size === 0) return 0

  let intersection = 0
  for (const w of a) {
    if (b.has(w)) intersection++
  }
  const union = a.size + b.size - intersection
  return union === 0 ? 0 : intersection / union
}

export const RUBBER_STAMP_THRESHOLD = 0.70
