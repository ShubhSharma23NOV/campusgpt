export default function StatCard({ title, value, subtitle, icon: Icon, color = 'blue', trend }) {
    const colors = {
        blue: { bg: 'bg-blue-50', text: 'text-blue-600', icon: 'bg-blue-100' },
        green: { bg: 'bg-green-50', text: 'text-green-600', icon: 'bg-green-100' },
        red: { bg: 'bg-red-50', text: 'text-red-600', icon: 'bg-red-100' },
        yellow: { bg: 'bg-yellow-50', text: 'text-yellow-600', icon: 'bg-yellow-100' },
        purple: { bg: 'bg-purple-50', text: 'text-purple-600', icon: 'bg-purple-100' },
    }
    const c = colors[color] || colors.blue

    return (
        <div className="card-hover">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{title}</p>
                    <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
                    {subtitle && <p className="mt-0.5 text-xs text-gray-500">{subtitle}</p>}
                    {trend && (
                        <p className={`mt-1 text-xs font-medium ${trend.positive ? 'text-green-600' : 'text-red-600'}`}>
                            {trend.positive ? '↑' : '↓'} {trend.label}
                        </p>
                    )}
                </div>
                {Icon && (
                    <div className={`w-10 h-10 rounded-xl ${c.icon} flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 ${c.text}`} />
                    </div>
                )}
            </div>
        </div>
    )
}
