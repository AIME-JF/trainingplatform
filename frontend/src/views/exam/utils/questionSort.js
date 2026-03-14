const QUESTION_TYPE_ORDER = {
  single: 0,
  multi: 1,
  judge: 2,
}

export function sortQuestionsByType(questions = []) {
  return questions
    .map((item, index) => ({ item, index }))
    .sort((left, right) => {
      const leftOrder = QUESTION_TYPE_ORDER[left.item?.type] ?? Number.MAX_SAFE_INTEGER
      const rightOrder = QUESTION_TYPE_ORDER[right.item?.type] ?? Number.MAX_SAFE_INTEGER
      if (leftOrder !== rightOrder) {
        return leftOrder - rightOrder
      }
      return left.index - right.index
    })
    .map(({ item }) => item)
}
