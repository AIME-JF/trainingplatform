import { defineConfig } from 'orval'

export default defineConfig({
  policeTraining: {
    input: {
      target: process.env.ORVAL_INPUT_TARGET || 'http://127.0.0.1:8001/api/v1/openapi.json',
      override: {
        transformer: 'src/api/transformers/strip-api-prefix.ts',
      },
    },
    output: {
      mode: 'tags-split',
      target: 'src/api/generated',
      schemas: 'src/api/generated/model',
      client: 'axios-functions',
      override: {
        mutator: {
          path: 'src/api/custom-instance.ts',
          name: 'customInstance',
        },
      },
    },
  },
})
