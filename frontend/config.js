const LOGIN_URL = "https://staging.jclg.swais.in/";

window.APP_CONFIG = Object.freeze({
  apiBaseUrl: "http://16.112.236.67:16004",
  logoutUrl: LOGIN_URL,
  endpoints: Object.freeze({
    config: "/config",
    health: "/health",
    statistics: "/dashboard/statistics",
    students: "/students",
    performance: "/performance/",
    progressSummary: "/engagement/",
    risk: "/risk",
    reports: "/reports",
    highRisk: "/dashboard/high-risk",
    analyze: "/analyze",
    recommendations: "/recommendations/",
    classReport: "/reports/class/"
  })
});
