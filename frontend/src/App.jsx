import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import CssBaseline from "@mui/material/CssBaseline";
import Box from "@mui/material/Box";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import LoginPage from "./pages/LoginPage";
import DashboardLayout from "./layouts/DashboardLayout";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#007AFF"
    },
    background: {
      default: "#F9F9F9"
    }
  },
  typography: {
    fontFamily: [
      'SF Pro Display',
      'Roboto',
      'Helvetica Neue',
      'Arial',
      'sans-serif'
    ].join(',')
  }
});

function App() {
  // Placeholder for authentication state
  const isAuthenticated = false;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              isAuthenticated ? <DashboardLayout /> : <Navigate to="/login" />
            }
          />
        </Routes>
      </Box>
    </ThemeProvider>
  );
}

export default App;