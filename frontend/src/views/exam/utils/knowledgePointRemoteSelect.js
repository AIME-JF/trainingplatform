// 知识点功能已移除，此文件保留以保持向后兼容
export function createKnowledgePointRemoteSelect() {
  return {
    knowledgePointOptions: [],
    knowledgePointLoading: false,
    knowledgePointSelectOptions: [],
    pinKnowledgePointOptions: () => {},
    loadKnowledgePointOptions: async () => {},
    handleKnowledgePointSearch: () => {},
    handleKnowledgePointFocus: () => {},
  }
}

export function mergeKnowledgePointOptions(...groups) {
  return []
}
