export default function AttendanceBadge({ percentage }) {
    if (percentage >= 75) return <span className="badge badge-green">{percentage}% ✓</span>
    if (percentage >= 65) return <span className="badge badge-yellow">{percentage}% ⚠</span>
    return <span className="badge badge-red">{percentage}% ✗</span>
}

export function AttendanceProgressBar({ percentage }) {
    const color =
        percentage >= 75 ? 'bg-green-500' :
            percentage >= 65 ? 'bg-yellow-500' : 'bg-red-500'

    return (
        <div className="w-full">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{percentage}%</span>
                <span>Min: 75%</span>
            </div>
            <div className="progress-track">
                <div
                    className={`progress-bar ${color}`}
                    style={{ width: `${Math.min(percentage, 100)}%` }}
                />
            </div>
            {/* 75% marker */}
            <div className="relative h-2 -mt-2">
                <div
                    className="absolute top-0 w-0.5 h-2 bg-gray-400"
                    style={{ left: '75%' }}
                    title="75% minimum"
                />
            </div>
        </div>
    )
}
