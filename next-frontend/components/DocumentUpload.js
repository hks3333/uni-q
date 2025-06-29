'use client'
import { useState } from 'react'
import { processDocuments } from '@/lib/ollama'

export default function DocumentUpload({ onDocumentsProcessed, disabled }) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [files, setFiles] = useState([])
  const [processedChunks, setProcessedChunks] = useState(0)

  const handleFileChange = (e) => {
    setFiles(Array.from(e.target.files))
  }

  const handleSubmit = async () => {
    if (files.length === 0 || disabled) return
    
    setIsProcessing(true)
    try {
      const vectorStore = await processDocuments(files, (chunks) => {
        setProcessedChunks(chunks)
      })
      onDocumentsProcessed(vectorStore)
    } catch (error) {
      console.error('Error processing documents:', error)
      alert('Failed to process documents')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow mb-6">
      <h2 className="text-lg font-semibold mb-2">Document Setup</h2>
      <input 
        type="file" 
        accept=".pdf" 
        multiple 
        onChange={handleFileChange}
        disabled={disabled || isProcessing}
        className="mb-3 block w-full text-sm text-gray-500
          file:mr-4 file:py-2 file:px-4
          file:rounded-md file:border-0
          file:text-sm file:font-semibold
          file:bg-blue-50 file:text-blue-700
          hover:file:bg-blue-100
          disabled:opacity-50"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || isProcessing || files.length === 0}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        {isProcessing ? (
          <span className="flex items-center">
            Processing... {processedChunks > 0 && `(${processedChunks} chunks)`}
          </span>
        ) : 'Process Documents'}
      </button>
    </div>
  )
}