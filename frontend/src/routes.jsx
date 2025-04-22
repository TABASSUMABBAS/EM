import React from "react";
import { Routes, Route } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import RegisterPage from "./pages/RegisterPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      {/* Add more routes for modules like Tasks, Payroll, Documents, etc. */}
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
    </Routes>
  );
}

export default AppRoutes;