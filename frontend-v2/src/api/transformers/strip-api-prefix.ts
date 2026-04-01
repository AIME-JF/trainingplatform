import { defineTransformer } from 'orval'

const API_PREFIX = '/api/v1'

export default defineTransformer((schema) => {
  const paths = schema.paths ?? {}

  return {
    ...schema,
    paths: Object.fromEntries(
      Object.entries(paths).map(([path, value]) => {
        if (!path.startsWith(API_PREFIX)) {
          return [path, value]
        }

        const nextPath = path.slice(API_PREFIX.length) || '/'
        return [nextPath, value]
      }),
    ),
  }
})
