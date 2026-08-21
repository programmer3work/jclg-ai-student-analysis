const DEFAULT_API_BASE_URL = "http://16.112.236.67:16004";
const LOCAL_API_BASE_URL = "http://127.0.0.1:16004";
const currentHost = typeof window !== "undefined" ? window.location.hostname : "";
const apiBaseUrl = (currentHost === "localhost" || currentHost === "127.0.0.1") ? LOCAL_API_BASE_URL : DEFAULT_API_BASE_URL;

window.APP_CONFIG = Object.freeze({
  apiBaseUrl,
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
