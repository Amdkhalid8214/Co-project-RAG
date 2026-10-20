import React from "react";
import "./WeatherCard.css";

export default function WeatherCard({ weather }) {
  if (!weather) return null;

  const {
    location = "Goa, India",
    current_temp = 28,
    current_temp_display = "28°C",
    condition = "Clear skies",
    condition_category = "clear",
    feels_like_desc = "Feels warm and humid",
    today_high_display = "34°C",
    today_low_display = "23°C",
    rain_chance_desc = "55% daytime",
    tonight_temp = "27–28°C",
    humidity_display,
    wind_speed_display,
    hourly_forecast = [],
    last_updated = "Live",
    source = "Live weather data and forecast."
  } = weather;

  // Determine if it's currently night time based on last_updated or client hour
  const isNight = (() => {
    if (typeof last_updated === "string" && (last_updated.includes("PM") || last_updated.includes("AM"))) {
      const isPM = last_updated.includes("PM");
      const hourPart = parseInt(last_updated.split(":")[0], 10);
      if (isPM && (hourPart >= 7 || hourPart === 12)) return true;
      if (!isPM && hourPart < 6) return true;
    }
    const curHour = new Date().getHours();
    return curHour >= 19 || curHour < 6;
  })();

  return (
    <div className="docuchat-weather-card">
      {/* Top Main Section */}
      <div className="weather-card-top-row">
        <div className="weather-card-meta-col">
          <h3 className="weather-location-heading">{location}</h3>
          <div className="weather-timestamp-sub">
            Current weather &bull; {last_updated}
          </div>
          <div className="weather-main-temp-val">{current_temp_display}</div>
          <div className="weather-condition-title">{condition}</div>
          {feels_like_desc && (
            <div className="weather-feels-like-text">{feels_like_desc}</div>
          )}
        </div>

        {/* Thematic Scenic Artwork Thumbnail matching Screenshot 2 */}
        <div className="weather-card-art-box">
          <div className={`weather-art-canvas ${condition_category} ${isNight ? "night" : "day"}`}>
            {isNight ? (
              // Starry night with palm tree silhouette matching Screenshot 2
              <svg viewBox="0 0 160 120" className="weather-art-svg" preserveAspectRatio="xMidYMid slice">
                <defs>
                  <linearGradient id="nightSky" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0a1128" />
                    <stop offset="60%" stopColor="#1c2541" />
                    <stop offset="100%" stopColor="#3a506b" />
                  </linearGradient>
                  <radialGradient id="moonGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="rgba(255,255,255,0.9)" />
                    <stop offset="40%" stopColor="rgba(200,225,255,0.4)" />
                    <stop offset="100%" stopColor="rgba(10,17,40,0)" />
                  </radialGradient>
                </defs>
                <rect width="160" height="120" fill="url(#nightSky)" />
                {/* Glowing celestial light */}
                <circle cx="120" cy="30" r="14" fill="url(#moonGlow)" />
                <circle cx="120" cy="30" r="5" fill="#f8fafc" />
                {/* Stars */}
                <circle cx="20" cy="25" r="1.2" fill="#fff" opacity="0.8" />
                <circle cx="45" cy="15" r="1" fill="#fff" opacity="0.9" />
                <circle cx="70" cy="35" r="1.5" fill="#fff" opacity="0.7" />
                <circle cx="95" cy="18" r="0.8" fill="#fff" opacity="0.6" />
                <circle cx="35" cy="55" r="1.2" fill="#fff" opacity="0.8" />
                <circle cx="80" cy="65" r="1" fill="#fff" opacity="0.5" />
                {/* Tropical Palm Tree Silhouette */}
                <path d="M135 120 Q128 85 130 55 Q131 40 134 32" stroke="#050811" strokeWidth="3.5" fill="none" strokeLinecap="round" />
                {/* Fronds */}
                <path d="M133 33 Q110 25 90 35 Q115 32 133 35" fill="#050811" />
                <path d="M134 33 Q120 12 105 15 Q125 18 134 33" fill="#050811" />
                <path d="M134 33 Q140 10 152 18 Q142 22 134 33" fill="#050811" />
                <path d="M134 33 Q155 25 160 40 Q148 35 134 35" fill="#050811" />
                <path d="M133 35 Q120 45 105 52 Q122 43 133 37" fill="#050811" />
                <path d="M134 35 Q145 50 155 58 Q144 48 134 37" fill="#050811" />
                {/* Distant Shore / Hill */}
                <path d="M0 120 L0 105 Q60 98 110 108 Q140 102 160 115 L160 120 Z" fill="#030509" />
              </svg>
            ) : condition_category === "rain" ? (
              // Rain scene
              <svg viewBox="0 0 160 120" className="weather-art-svg" preserveAspectRatio="xMidYMid slice">
                <defs>
                  <linearGradient id="rainSky" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#1e293b" />
                    <stop offset="100%" stopColor="#334155" />
                  </linearGradient>
                </defs>
                <rect width="160" height="120" fill="url(#rainSky)" />
                {/* Storm Clouds */}
                <path d="M30 45 Q40 25 65 30 Q85 20 110 32 Q135 28 140 50 Q145 65 125 70 L35 70 Q20 65 30 45 Z" fill="#475569" opacity="0.9" />
                {/* Raindrops */}
                <line x1="45" y1="78" x2="40" y2="92" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
                <line x1="65" y1="74" x2="60" y2="88" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
                <line x1="85" y1="80" x2="80" y2="94" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
                <line x1="105" y1="76" x2="100" y2="90" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
                <line x1="125" y1="82" x2="120" y2="96" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.8" />
                <line x1="55" y1="96" x2="50" y2="110" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
                <line x1="95" y1="98" x2="90" y2="112" stroke="#60a5fa" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
              </svg>
            ) : (
              // Daytime tropical / sunny scene
              <svg viewBox="0 0 160 120" className="weather-art-svg" preserveAspectRatio="xMidYMid slice">
                <defs>
                  <linearGradient id="daySky" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0284c7" />
                    <stop offset="60%" stopColor="#38bdf8" />
                    <stop offset="100%" stopColor="#bae6fd" />
                  </linearGradient>
                  <radialGradient id="sunGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#fef08a" />
                    <stop offset="40%" stopColor="rgba(253, 224, 71, 0.6)" />
                    <stop offset="100%" stopColor="rgba(2, 132, 199, 0)" />
                  </radialGradient>
                </defs>
                <rect width="160" height="120" fill="url(#daySky)" />
                <circle cx="125" cy="35" r="22" fill="url(#sunGlow)" />
                <circle cx="125" cy="35" r="10" fill="#fef08a" />
                {/* Light clouds */}
                <path d="M20 50 Q30 38 45 42 Q58 35 72 44 Q85 40 90 52 L22 52 Z" fill="#ffffff" opacity="0.75" />
                {/* Palm tree */}
                <path d="M135 120 Q128 85 130 65 Q131 52 134 45" stroke="#1e293b" strokeWidth="3.5" fill="none" strokeLinecap="round" />
                <path d="M133 46 Q112 38 95 48 Q118 45 133 47" fill="#1e293b" />
                <path d="M134 46 Q122 28 108 30 Q126 33 134 46" fill="#1e293b" />
                <path d="M134 46 Q140 25 150 32 Q142 36 134 46" fill="#1e293b" />
                <path d="M134 46 Q152 40 158 52 Q146 48 134 48" fill="#1e293b" />
                <path d="M0 120 L0 110 Q60 102 110 112 Q140 108 160 118 L160 120 Z" fill="#0f172a" />
              </svg>
            )}
          </div>
        </div>
      </div>

      {/* Metrics Row (Today's High, Low, Rain chance, Tonight) */}
      <div className="weather-metrics-grid">
        <div className="weather-metric-tile">
          <div className="metric-header-row">
            <span className="metric-icon">🌡</span>
            <span className="metric-label">Today's high</span>
          </div>
          <div className="metric-val-text">{today_high_display}</div>
        </div>

        <div className="weather-metric-tile">
          <div className="metric-header-row">
            <span className="metric-icon">❄️</span>
            <span className="metric-label">Today's low</span>
          </div>
          <div className="metric-val-text">{today_low_display}</div>
        </div>

        <div className="weather-metric-tile">
          <div className="metric-header-row">
            <span className="metric-icon">🌧</span>
            <span className="metric-label">Rain chance</span>
          </div>
          <div className="metric-val-text">{rain_chance_desc}</div>
        </div>

        <div className="weather-metric-tile">
          <div className="metric-header-row">
            <span className="metric-icon">🌙</span>
            <span className="metric-label">Tonight</span>
          </div>
          <div className="metric-val-text">{tonight_temp}</div>
        </div>
      </div>

      {/* Secondary pills if available */}
      {(humidity_display || wind_speed_display) && (
        <div className="weather-secondary-badges">
          {humidity_display && (
            <span className="weather-badge-chip">
              💧 Humidity: <strong>{humidity_display}</strong>
            </span>
          )}
          {wind_speed_display && (
            <span className="weather-badge-chip">
              💨 Wind: <strong>{wind_speed_display}</strong>
            </span>
          )}
        </div>
      )}

      {/* Hourly forecast strip if available */}
      {hourly_forecast && hourly_forecast.length > 0 && (
        <div className="weather-hourly-strip">
          {hourly_forecast.map((h, i) => (
            <div key={i} className="hourly-forecast-item">
              <span className="hourly-time">{h.time}</span>
              <span className="hourly-temp">{h.temp}</span>
              <span className="hourly-cond" title={h.condition}>{h.condition}</span>
              {h.rain_chance && parseInt(h.rain_chance, 10) > 0 && (
                <span className="hourly-rain">🌧 {h.rain_chance}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Source Attribution matching Screenshot 2 */}
      <div className="weather-source-attribution">{source}</div>
    </div>
  );
}
