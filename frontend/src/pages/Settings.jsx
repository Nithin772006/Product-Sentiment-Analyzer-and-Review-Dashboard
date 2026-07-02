import { useState, useEffect } from "react";
import { FiSettings, FiVolume2, FiSun, FiMoon, FiGlobe } from "react-icons/fi";

export default function Settings() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "dark");
  const [soundEnabled, setSoundEnabled] = useState(
    localStorage.getItem("soundEnabled") === "true"
  );
  const [autoExport, setAutoExport] = useState(
    localStorage.getItem("autoExport") === "true"
  );

  // Sync HTML class on mount (in case navigated here after a reload)
  useEffect(() => {
    if (theme === "light") {
      document.documentElement.classList.add("light");
    } else {
      document.documentElement.classList.remove("light");
    }
  }, []);

  const handleThemeChange = (newTheme) => {
    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
    if (newTheme === "light") {
      document.documentElement.classList.add("light");
    } else {
      document.documentElement.classList.remove("light");
    }
  };

  const handleSoundChange = (e) => {
    const val = e.target.checked;
    setSoundEnabled(val);
    localStorage.setItem("soundEnabled", val);
  };

  const handleAutoExportChange = (e) => {
    const val = e.target.checked;
    setAutoExport(val);
    localStorage.setItem("autoExport", val);
  };

  const cardStyle = {
    backgroundColor: "var(--color-bg-card)",
    borderColor: "var(--color-border)",
    boxShadow: "var(--shadow-card)",
  };

  const dividerStyle = { borderColor: "var(--color-divider)" };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-6">
      {/* Title */}
      <div
        className="border-b pb-4 transition-colors duration-200"
        style={dividerStyle}
      >
        <h1
          className="page-title flex items-center gap-2"
          style={{ color: "var(--color-text-primary)" }}
        >
          <FiSettings className="text-[#3361ff]" /> Application Settings
        </h1>
        <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
          Customize display layout preferences, notification sound triggers, and default export criteria.
        </p>
      </div>

      {/* Grid panels */}
      <div className="flex flex-col gap-6 mt-2">
        {/* Theme Settings Card */}
        <div
          className="rounded-2xl border p-6 transition-all duration-200"
          style={cardStyle}
        >
          <h3
            className="section-title mb-3 flex items-center gap-2"
            style={{ color: "var(--color-text-primary)" }}
          >
            <FiSun className="text-[#f59e0b]" /> Theme Layout Mode
          </h3>
          <p className="text-xs mb-4" style={{ color: "var(--color-text-muted)" }}>
            Select an interface theme preference for the analytics portal.
          </p>

          <div className="flex gap-4">
            {/* Dark mode button */}
            <button
              onClick={() => handleThemeChange("dark")}
              className="flex-1 p-4 rounded-xl border flex flex-col items-center gap-2 font-bold text-sm transition-all duration-200"
              style={
                theme === "dark"
                  ? {
                      borderColor: "#3361ff",
                      backgroundColor: "rgba(51,97,255,0.12)",
                      color: "var(--color-text-primary)",
                    }
                  : {
                      borderColor: "var(--color-border)",
                      backgroundColor: "var(--color-bg-card-hover)",
                      color: "var(--color-text-muted)",
                    }
              }
            >
              <FiMoon className="text-2xl" />
              <span>Sleek Dark Mode (Default)</span>
            </button>

            {/* Light mode button */}
            <button
              onClick={() => handleThemeChange("light")}
              className="flex-1 p-4 rounded-xl border flex flex-col items-center gap-2 font-bold text-sm transition-all duration-200"
              style={
                theme === "light"
                  ? {
                      borderColor: "#3361ff",
                      backgroundColor: "rgba(51,97,255,0.12)",
                      color: "var(--color-text-primary)",
                    }
                  : {
                      borderColor: "var(--color-border)",
                      backgroundColor: "var(--color-bg-card-hover)",
                      color: "var(--color-text-muted)",
                    }
              }
            >
              <FiSun className="text-2xl" />
              <span>Classic Light Mode</span>
            </button>
          </div>
        </div>

        {/* Sound Notifications Settings */}
        <div
          className="rounded-2xl border p-6 flex flex-col gap-4 transition-all duration-200"
          style={cardStyle}
        >
          <h3
            className="section-title flex items-center gap-2"
            style={{ color: "var(--color-text-primary)" }}
          >
            <FiVolume2 className="text-[#3361ff]" /> Notification Triggers
          </h3>
          <p className="text-xs -mt-2" style={{ color: "var(--color-text-muted)" }}>
            Control visual toasts and audio heartbeats during scraping completions.
          </p>

          <div
            className="flex items-center justify-between border-t pt-4 transition-colors duration-200"
            style={dividerStyle}
          >
            <div>
              <span
                className="text-xs font-semibold block"
                style={{ color: "var(--color-text-primary)" }}
              >
                Enable Audio Alerts
              </span>
              <span className="text-[10px]" style={{ color: "var(--color-text-muted)" }}>
                Play subtle audio beats when jobs complete
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={soundEnabled}
                onChange={handleSoundChange}
                className="sr-only peer"
              />
              <div
                className="w-11 h-6 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#3361ff] peer-checked:after:bg-white"
                style={{
                  backgroundColor: "var(--color-bg-card-hover)",
                  borderColor: "var(--color-border)",
                }}
              />
            </label>
          </div>
        </div>

        {/* Local Caching preferences */}
        <div
          className="rounded-2xl border p-6 flex flex-col gap-4 transition-all duration-200"
          style={cardStyle}
        >
          <h3
            className="section-title flex items-center gap-2"
            style={{ color: "var(--color-text-primary)" }}
          >
            <FiGlobe className="text-[#22c55e]" /> Preferences
          </h3>
          <p className="text-xs -mt-2" style={{ color: "var(--color-text-muted)" }}>
            Optimize database lookups and file downloads.
          </p>

          <div
            className="flex items-center justify-between border-t pt-4 transition-colors duration-200"
            style={dividerStyle}
          >
            <div>
              <span
                className="text-xs font-semibold block"
                style={{ color: "var(--color-text-primary)" }}
              >
                Autoload PDF Downloads
              </span>
              <span className="text-[10px]" style={{ color: "var(--color-text-muted)" }}>
                Open reports in secondary tabs immediately on generation
              </span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={autoExport}
                onChange={handleAutoExportChange}
                className="sr-only peer"
              />
              <div
                className="w-11 h-6 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#3361ff] peer-checked:after:bg-white"
                style={{
                  backgroundColor: "var(--color-bg-card-hover)",
                  borderColor: "var(--color-border)",
                }}
              />
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
