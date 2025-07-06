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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3>Research Plan</h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
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

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <h4>Research Objectives</h4>
          <ul style={{ listStyle: 'disc inside', display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            {safePlan.objectives.map((objective, index) => (
              <li key={index}>{objective}</li>
            ))}
          </ul>
        </div>

        <div>
          <h4>Search Strategy</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {safePlan.search_queries.map((query, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Step {index + 1}:</span>
                <span style={{ fontSize: '0.875rem', background: 'var(--pastel-blue)', color: 'var(--text-primary)', padding: '0.25rem 0.5rem', borderRadius: 'var(--border-radius-small)' }}>
                  {query}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4>Information Sources</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {safePlan.sources.map((source, index) => (
              <span key={index} className="tag">
                {source}
              </span>
            ))}
          </div>
        </div>

        <div>
          <h4>Analysis Framework</h4>
          <ul style={{ listStyle: 'disc inside', display: 'flex', flexDirection: 'column', gap: '0.25rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            {safePlan.analysis_framework.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
} 