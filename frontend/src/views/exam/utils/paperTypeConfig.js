export function summarizePaperTypeConfigs(configs = []) {
  return (configs || []).reduce((summary, item) => {
    const count = Number(item?.count || 0)
    const score = Number(item?.score || 0)
    summary.totalCount += count
    summary.totalScore += count * score
    return summary
  }, { totalCount: 0, totalScore: 0 })
}

export function formatPaperTypeConfigs(configs = [], typeLabels = {}) {
  return (configs || [])
    .map((item) => {
      const parts = [`${typeLabels[item?.type] || item?.type || '未知题型'} ${Number(item?.count || 0)}题`]
      if (item?.difficulty) {
        parts.push(`难度${item.difficulty}级`)
      }
      if (item?.score) {
        parts.push(`单题${item.score}分`)
      }
      return parts.join('，')
    })
    .join(' / ')
}
