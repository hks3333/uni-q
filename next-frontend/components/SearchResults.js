'use client'

export default function SearchResults({ results, onContinue }) {
  if (!results || results.length === 0) {
    return (
      <div className="search-results bg-white rounded-lg shadow-md p-6 mb-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Search Results</h3>
        <p className="text-gray-600">No relevant results found. Please try refining your search queries.</p>
      </div>
    )
  }

  return (
    <div className="search-results bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">Search Results</h3>
        <button
          onClick={onContinue}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
        >
          Continue with Synthesis
        </button>
      </div>

      <div className="space-y-4">
        {results.map((result, index) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-medium text-blue-600 hover:text-blue-800">
                <a href={result.url} target="_blank" rel="noopener noreferrer">
                  {result.title}
                </a>
              </h4>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{result.source_type}</span>
                <span className={`text-xs px-2 py-1 rounded ${
                  result.relevance_score > 0.7 ? 'bg-green-100 text-green-800' :
                  result.relevance_score > 0.4 ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {Math.round(result.relevance_score * 100)}% relevant
                </span>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 mb-2">
              <a href={result.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
                {result.url}
              </a>
            </p>
            
            <p className="text-sm text-gray-700 leading-relaxed">
              {result.content.length > 300 
                ? `${result.content.substring(0, 300)}...` 
                : result.content
              }
            </p>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Found {results.length} relevant sources. Click "Continue with Synthesis" to generate the final research report.
        </p>
      </div>
    </div>
  )
} 