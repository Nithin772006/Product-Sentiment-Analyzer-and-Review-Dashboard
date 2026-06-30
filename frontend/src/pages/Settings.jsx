import { useState, useEffect } from "react";
import { FiSettings, FiVolume2, FiSun, FiMoon, FiGlobe } from "react-icons/fi";

export default function Settings() {
  const [theme, setTheme] = useState(localStorage.getItem("theme") || "dark");
  const [soundEnabled, setSoundEnabled] = useState(localStorage.getItem("soundEnabled") === "true");
  const [autoExport, setAutoExport] = useState(localStorage.getItem("autoExport") === "true");

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

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 w-full flex-1 flex flex-col gap-6">
      {/* Title */}
      <div className="border-b border-[rgba(255,255,255,0.05)] pb-4">
        <h1 className="page-title text-[#e8eaf6] flex items-center gap-2">
          <FiSettings className="text-[#3361ff]" /> Application Settings
        </h1>
        <p className="text-sm text-[#8892b0] mt-1">
          Customize display layout preferences, notification sound triggers, and default export criteria.
        </p>
      </div>

      {/* Grid panels */}
      <div className="flex flex-col gap-6 mt-2">
        {/* Theme Settings Card */}
        <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] p-6">
          <h3 className="section-title text-[#e8eaf6] mb-3 flex items-center gap-2">
            <FiSun className="text-[#f59e0b]" /> Theme Layout Mode
          </h3>
          <p className="text-xs text-[#8892b0] mb-4">
            Select a interface theme preference for the analytics portal.
          </p>

          <div className="flex gap-4">
            <button
              onClick={() => handleThemeChange("dark")}
              className={`flex-1 p-4 rounded-xl border flex flex-col items-center gap-2 font-bold text-sm ${
                theme === "dark"
                  ? "border-[#3361ff] bg-[#3361ff]/10 text-white"
                  : "border-[rgba(255,255,255,0.08)] bg-[#1c2333] text-[#8892b0] hover:text-[#e8eaf6]"
              }`}
            >
              <FiMoon className="text-2xl" />
              <span>Sleek Dark Mode (Default)</span>
            </button>

            <button
              onClick={() => handleThemeChange("light")}
              className={`flex-1 p-4 rounded-xl border flex flex-col items-center gap-2 font-bold text-sm ${
                theme === "light"
                  ? "border-[#3361ff] bg-[#3361ff]/10 text-[#161b27]"
                  : "border-[rgba(255,255,255,0.08)] bg-[#1c2333] text-[#8892b0] hover:text-[#e8eaf6]"
              }`}
            >
              <FiSun className="text-2xl" />
              <span>Classic Light Mode</span>
            </button>
          </div>
        </div>

        {/* Sound Notifications Settings */}
        <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] p-6 flex flex-col gap-4">
          <h3 className="section-title text-[#e8eaf6] flex items-center gap-2">
            <FiVolume2 className="text-[#3361ff]" /> Notification Triggers
          </h3>
          <p className="text-xs text-[#8892b0] -mt-2">
            Control visual toasts and audio heartbeats during scraping completions.
          </p>

          <div className="flex items-center justify-between border-t border-[rgba(255,255,255,0.05)] pt-4">
            <div>
              <span className="text-xs font-semibold text-[#e8eaf6] block">Enable Audio Alerts</span>
              <span className="text-[10px] text-[#8892b0]">Play subtle audio beats when jobs complete</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={soundEnabled}
                onChange={handleSoundChange}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#1c2333] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#8892b0] after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#3361ff] peer-checked:after:bg-white"></div>
            </label>
          </div>
        </div>

        {/* Local Caching preferences */}
        <div className="card bg-[#161b27] border-[rgba(255,255,255,0.06)] p-6 flex flex-col gap-4">
          <h3 className="section-title text-[#e8eaf6] flex items-center gap-2">
            <FiGlobe className="text-[#22c55e]" /> Preferences
          </h3>
          <p className="text-xs text-[#8892b0] -mt-2">
            Optimize database lookups and file downloads.
          </p>

          <div className="flex items-center justify-between border-t border-[rgba(255,255,255,0.05)] pt-4">
            <div>
              <span className="text-xs font-semibold text-[#e8eaf6] block">Autoload PDF Downloads</span>
              <span className="text-[10px] text-[#8892b0]">Open reports in secondary tabs immediately on generation</span>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={autoExport}
                onChange={handleAutoExportChange}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-[#1c2333] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-[#8892b0] after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#3361ff] peer-checked:after:bg-white"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
