// 知识点API已移除，此文件保留以保持向后兼容
import request from './request'

export function getKnowledgePoints(params) {
    return Promise.resolve({ items: [], total: 0 })
}

export function createKnowledgePoint(data) {
    return Promise.reject(new Error('知识点功能已移除'))
}

export function updateKnowledgePoint(id, data) {
    return Promise.reject(new Error('知识点功能已移除'))
}

export function deleteKnowledgePoint(id) {
    return Promise.reject(new Error('知识点功能已移除'))
}
