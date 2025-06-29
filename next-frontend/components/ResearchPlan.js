'use client'
import { useState } from 'react'

export default function ResearchPlan({ plan, onPlanRefine, onExecute }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedPlan, setEditedPlan] = useState(plan)

  // Ensure plan properties are arrays with fallbacks
  const safePlan = {
    objectives: Array.isArray(plan?.objectives) ? plan.objectives : [],
    search_queries: Array.isArray(plan?.search_queries) ? plan.search_queries : [],
    sources: Array.isArray(plan?.sources) ? plan.sources : [],
    analysis_framework: Array.isArray(plan?.analysis_framework) ? plan.analysis_framework : []
  }

  const handleEdit = () => setIsEditing(true)
  const handleSave = () => {
    setIsEditing(false)
    onPlanRefine(editedPlan)
  }
  const handleCancel = () => {
    setIsEditing(false)
    setEditedPlan(plan)
  }

  return (
    <div className="research-plan">
      <div className="flex justify-between items-center mb-4">
        <h3>Research Plan</h3>
        <div className="flex gap-2">
          {!isEditing ? (
            <>
              <button onClick={handleEdit} className="btn-secondary">
                Edit Plan
              </button>
              <button onClick={() => onExecute(plan)} className="btn">
                Execute Plan
              </button>
            </>
          ) : (
            <>
              <button onClick={handleSave} className="btn">
                Save
              </button>
              <button onClick={handleCancel} className="btn-secondary">
                Cancel
              </button>
            </>
          )}
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <h4>Research Objectives</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
            {safePlan.objectives.map((objective, index) => (
              <li key={index}>{objective}</li>
            ))}
          </ul>
        </div>

        <div>
          <h4>Search Strategy</h4>
          <div className="space-y-2">
            {safePlan.search_queries.map((query, index) => (
              <div key={index} className="flex items-center gap-2">
                <span className="text-sm text-gray-400">Step {index + 1}:</span>
                <span className="text-sm bg-gray-100 text-gray-800 px-2 py-1 rounded">
                  {query}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4>Information Sources</h4>
          <div className="flex flex-wrap gap-2">
            {safePlan.sources.map((source, index) => (
              <span key={index} className="tag">
                {source}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h4>Analysis Framework</h4>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
            {safePlan.analysis_framework.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
} 