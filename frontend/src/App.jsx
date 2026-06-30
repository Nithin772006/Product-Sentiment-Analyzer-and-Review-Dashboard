import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Footer from "./components/Footer";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import ProductPage from "./pages/ProductPage";
import SearchPage from "./pages/SearchPage";
import About from "./pages/About";
import NotFound from "./pages/NotFound";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import Login from "./pages/Login";

import { useEffect } from "react";

// Layout wrapper for all authenticated dashboard panels
function DashboardLayout() {
  const token = localStorage.getItem("token");

  useEffect(() => {
    if (!token) return;

    // Connect to real-time events WebSocket
    const wsUrl = "ws://localhost:8000/api/realtime";
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[WebSocket] Connected to real-time event stream");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("[WebSocket Event Received]", data);
        
        // Push simple browser notifications if allowed
        if (Notification.permission === "granted") {
          new Notification("SentimentLens Notification", {
            body: data.message || `Event: ${data.event}`,
          });
        }
      } catch (err) {
        console.error("[WebSocket Message Parse Error]", err);
      }
    };

    ws.onclose = () => {
      console.log("[WebSocket] Connection closed");
    };

    // Request browser notification permissions
    if (Notification.permission === "default") {
      Notification.requestPermission();
    }

    return () => {
      ws.close();
    };
  }, [token]);
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen flex bg-[#0f1117] text-[#e8eaf6]">
      <Sidebar />
      <div className="flex-1 flex flex-col justify-between overflow-x-hidden">
        <main className="animate-fade-in flex-1">
          <Outlet />
        </main>
        <Footer />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Full screen auth page */}
        <Route path="/login" element={<Login />} />

        {/* Authenticated dashboard paths */}
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/products/:id" element={<ProductPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/about" element={<About />} />
          <Route path="/404" element={<NotFound />} />
        </Route>

        {/* Global unmatched fallback */}
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
