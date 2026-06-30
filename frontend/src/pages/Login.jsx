import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiLock, FiUser, FiArrowRight, FiShield } from "react-icons/fi";
import apiService from "../api/api";

export default function Login() {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("user");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");
    
    if (!username.trim() || !password.trim()) {
      setErrorMsg("Please fill in all credentials fields.");
      return;
    }
    
    if (username.trim().length < 3) {
      setErrorMsg("Username must be at least 3 characters long.");
      return;
    }

    if (password.length < 6) {
      setErrorMsg("Password must be at least 6 characters long.");
      return;
    }

    setIsLoading(true);

    try {
      if (isRegister) {
        // Register account
        await apiService.register(username.trim(), password, role);
        setSuccessMsg("Registration successful! You can now log in.");
        setIsRegister(false);
      } else {
        // Login account
        const response = await apiService.login(username.trim(), password);
        const { access_token, role: userRole } = response.data;
        
        localStorage.setItem("token", access_token);
        localStorage.setItem("username", username.trim());
        localStorage.setItem("role", userRole);
        
        navigate("/");
      }
    } catch (err) {
      setErrorMsg(err.message || "Credential authentication failed. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f1117] p-6 relative">
      {/* Decorative ambient light */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-[#3361ff]/10 rounded-full blur-[90px] pointer-events-none"></div>

      <div className="card w-full max-w-md bg-[#161b27] border-[rgba(255,255,255,0.06)] p-8 shadow-2xl relative z-10">
        {/* Header Title */}
        <div className="text-center mb-8">
          <span className="text-4xl">🛍️</span>
          <h2 className="text-2xl font-extrabold text-[#e8eaf6] tracking-tight mt-3">
            {isRegister ? "Create Account" : "Access Studio Portal"}
          </h2>
          <p className="text-xs text-[#8892b0] mt-1.5 leading-relaxed">
            {isRegister ? "Join SentimentLens review analytics system" : "Log in to view scrapers and NLP summaries"}
          </p>
        </div>

        {errorMsg && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 text-[#ef4444] rounded-xl text-xs text-center">
            ⚠️ {errorMsg}
          </div>
        )}

        {successMsg && (
          <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 text-[#22c55e] rounded-xl text-xs text-center">
            🎉 {successMsg}
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-[#8892b0] uppercase font-bold tracking-wider">Username</label>
            <div className="relative flex items-center">
              <FiUser className="absolute left-3.5 text-[#8892b0]" />
              <input
                type="text"
                required
                className="w-full bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl pl-11 pr-4 py-3 text-xs text-[#e8eaf6] focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-[10px] text-[#8892b0] uppercase font-bold tracking-wider">Password</label>
            <div className="relative flex items-center">
              <FiLock className="absolute left-3.5 text-[#8892b0]" />
              <input
                type="password"
                required
                className="w-full bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl pl-11 pr-4 py-3 text-xs text-[#e8eaf6] focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {isRegister && (
            <div className="flex flex-col gap-1">
              <label className="text-[10px] text-[#8892b0] uppercase font-bold tracking-wider">Role Access</label>
              <div className="relative flex items-center">
                <FiShield className="absolute left-3.5 text-[#8892b0]" />
                <select
                  className="w-full bg-[#1c2333] border border-[rgba(255,255,255,0.08)] rounded-xl pl-11 pr-4 py-3 text-xs text-[#e8eaf6] focus:outline-none focus:ring-1 focus:ring-[#3361ff]"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="user">Standard User</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary justify-center w-full py-3.5 rounded-xl font-bold mt-2"
          >
            {isLoading ? "Validating Account..." : isRegister ? "Register" : "Login"}
            {!isLoading && <FiArrowRight />}
          </button>
        </form>

        {/* Register switcher */}
        <div className="text-center mt-6 text-xs text-[#8892b0]">
          {isRegister ? "Already registered?" : "New to the platform?"}{" "}
          <button
            onClick={() => {
              setIsRegister(!isRegister);
              setErrorMsg("");
              setSuccessMsg("");
            }}
            className="text-[#3361ff] font-semibold hover:underline focus:outline-none"
          >
            {isRegister ? "Sign In" : "Create Account"}
          </button>
        </div>
      </div>
    </div>
  );
}
