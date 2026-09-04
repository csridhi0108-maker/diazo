import { useState } from 'react'

function RecommendationCard({ recommendation }) {
  const [isExpanded, setIsExpanded] = useState(false)

  const formatTitle = (type) => type.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden hover:shadow-md transition-all duration-300">
      {/* Clickable Header */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-4 cursor-pointer flex items-start gap-3 group"
      >
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 group-hover:bg-emerald-200 transition-colors">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-slate-900">
              {formatTitle(recommendation.insight_type)}
            </p>
            {/* Chevron Icon */}
            <svg 
              className={`h-4 w-4 text-slate-400 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} 
              fill="none" viewBox="0 0 24 24" stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
          
          <p className="text-sm text-slate-600 mt-1 line-clamp-2">
            {recommendation.llm_phrased_text}
          </p>
          
          <p className="text-xs text-emerald-600 mt-2 font-medium">
            {isExpanded ? 'Click to collapse' : 'Click to see details'}
          </p>
        </div>
      </div>

      {/* Expanding Details Section */}
      <div 
        className={`transition-all duration-300 ease-in-out overflow-hidden ${
          isExpanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="px-4 pb-4 pt-0 space-y-3 border-t border-slate-100 bg-slate-50/50">
          
          {/* Recommendation Box */}
          <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100 mt-3">
            <p className="text-[10px] font-bold text-emerald-900 uppercase tracking-wider mb-1">Recommendation</p>
            <p className="text-sm text-emerald-800 leading-relaxed">
              {recommendation.llm_phrased_text}
            </p>
          </div>
          
          {/* Analysis Details Box */}
          <div className="p-3 bg-white rounded-lg border border-slate-200 shadow-sm">
            <p className="text-[10px] font-bold text-slate-900 uppercase tracking-wider mb-2">Analysis Details</p>
            <div className="space-y-1.5 text-sm">
              {recommendation.insight_type === 'adherence' ? (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Logging window:</span>
                    <span className="font-semibold text-slate-900">{recommendation.raw_data?.window_days ?? 'N/A'} days</span>
                  </div>
                  {recommendation.raw_data?.glucose_adherence_pct !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Glucose rate:</span>
                      <span className="font-semibold text-slate-900">{recommendation.raw_data.glucose_adherence_pct}%</span>
                    </div>
                  )}
                  {recommendation.raw_data?.meal_adherence_pct !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Meal rate:</span>
                      <span className="font-semibold text-slate-900">{recommendation.raw_data.meal_adherence_pct}%</span>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-500">Data points:</span>
                    <span className="font-semibold text-slate-900">
                      {recommendation.raw_data?.sample_count ?? recommendation.raw_data?.sample_size ?? 'N/A'}
                    </span>
                  </div>
                  {recommendation.raw_data?.avg_glucose_increase && (
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Avg glucose impact:</span>
                      <span className="font-semibold text-slate-900">
                        {recommendation.raw_data.avg_glucose_increase.toFixed(1)} mg/dL
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
          
          {/* Timestamp */}
          <div className="text-[10px] text-slate-400 text-center pt-1">
            Generated: {new Date(recommendation.created_at).toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default RecommendationCard