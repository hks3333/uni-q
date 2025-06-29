import { MemoryVectorStore } from 'langchain/vectorstores/memory'
import { HuggingFaceInferenceEmbeddings } from '@langchain/community/embeddings/hf'

export const checkOllamaServer = async () => {
  try {
    const response = await fetch('http://localhost:11434', { method: 'HEAD' })
    return response.ok
  } catch {
    return false
  }
}

export const loadMemoryVectorStore = async () => {
  const data = await fetch('/vectors/memory_vectors.json').then(res => res.json())

  const embeddings = new HuggingFaceInferenceEmbeddings({
    model: 'sentence-transformers/all-MiniLM-L6-v2',
    apiKey: "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"
  })

  const store = new MemoryVectorStore(embeddings)
  store.memoryVectors = data
  return store
}

export const queryLlama3 = async (query, vectorStore, onStream) => {
  const retriever = vectorStore.asRetriever()
  const context = await getRelevantContext(query, retriever)

  const prompt = `Answer the following question clearly and concisely based only on the provided context. Avoid unnecessary repetition or lengthy explanations, but include all essential information.\n\nContext:\n${context}\n\nQuestion:\n${query}`

  const response = await fetch('http://localhost:11434/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'llama3.2:3b-instruct-q4_K_M',
      prompt,
      stream: true,
      options: {
        temperature: 0.3,
        top_p: 0.9,
        repeat_penalty: 1.1
      }
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    console.error('❌ Ollama error:', errorText)
    throw new Error('Failed to query Llama 3')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n')
    buffer = parts.pop()

    for (const part of parts) {
      if (!part.trim()) continue
      try {
        const parsed = JSON.parse(part)
        if (parsed.response) {
          onStream(parsed.response)
        }
      } catch (e) {
        console.error('❌ Failed to parse chunk:', part)
      }
    }
  }
}

const getRelevantContext = async (query, retriever) => {
  const docs = await retriever.getRelevantDocuments(query)
  return docs.map(doc => doc.pageContent).join('\n\n')
}
