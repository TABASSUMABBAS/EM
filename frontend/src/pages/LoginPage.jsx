import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import InputAdornment from "@mui/material/InputAdornment";
import IconButton from "@mui/material/IconButton";
import Visibility from "@mui/icons-material/Visibility";
import VisibilityOff from "@mui/icons-material/VisibilityOff";
import GoogleIcon from "@mui/icons-material/Google";
import LinkedInIcon from "@mui/icons-material/LinkedIn";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const validate = () => {
    const errors = {};
    if (!email) {
      errors.email = "Email is required";
    } else if (!/^\S+@\S+\.\S+$/.test(email)) {
      errors.email = "Enter a valid email address";
    }
    if (!password) {
      errors.password = "Password is required";
    } else if (password.length < 6) {
      errors.password = "Password must be at least 6 characters";
    }
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;
    setLoading(true);
    try {
      // Mock login: simulate API call
      await new Promise((res) => setTimeout(res, 1000));
      // Simulate successful login and token
      const mockToken = "mock_token_123";
      if (rememberMe) {
        localStorage.setItem("access_token", mockToken);
      } else {
        sessionStorage.setItem("access_token", mockToken);
      }
      setEmail("");
      setPassword("");
      setFieldErrors({});
      navigate("/");
    } catch (err) {
      setError("Network error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {/* Left Side - Illustration */}
      <Box sx={{ flex: 1, display: { xs: "none", md: "flex" }, flexDirection: "column", justifyContent: "center", alignItems: "center", bgcolor: "#181C2A", color: "#fff", p: 4 }}>
        <Box sx={{ mb: 4 }}>
          <img src="https://images.unsplash.com/photo-1464983953574-0892a716854b?auto=format&fit=crop&w=600&q=80" alt="Rocket Arrow" style={{ width: 320, borderRadius: 16, boxShadow: "0 8px 32px rgba(0,0,0,0.2)" }} />
        </Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Let’s empower your employees today.
        </Typography>
        <Typography variant="body1" sx={{ opacity: 0.8 }}>
          We help to complete all your conveyancing needs easily
        </Typography>
        <Box sx={{ mt: 6, fontWeight: 700, fontSize: 22, display: "flex", alignItems: "center" }}>
          <Avatar sx={{ bgcolor: "#fff", color: "#181C2A", mr: 1, width: 32, height: 32, fontWeight: 700 }}>T</Avatar> TaxOn
        </Box>
      </Box>
      {/* Right Side - Login Form */}
      <Box sx={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "#f9fafd" }}>
        <Paper elevation={0} sx={{ p: { xs: 2, md: 6 }, width: "100%", maxWidth: 420, borderRadius: 4, boxShadow: { xs: 0, md: 3 } }}>
          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
            <Box sx={{ mb: 2, mt: -2, alignSelf: "flex-end" }}>
              <span style={{ fontSize: 32, color: "#bdbdbd" }}>↗</span>
            </Box>
            <Typography component="h1" variant="h5" fontWeight={700} sx={{ mb: 1 }}>
              Login first to your account
            </Typography>
            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: "100%" }} noValidate>
              <TextField
                margin="normal"
                required
                fullWidth
                label="Email Address"
                type="email"
                name="email"
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="Input your registered email"
                sx={{ mb: 2 }}
                error={Boolean(fieldErrors.email)}
                helperText={fieldErrors.email}
                inputProps={{ "aria-label": "Email Address" }}
              />
              <TextField
                margin="normal"
                required
                fullWidth
                label="Password"
                type={showPassword ? "text" : "password"}
                name="password"
                autoComplete="current-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Input your password"
                sx={{ mb: 1 }}
                error={Boolean(fieldErrors.password)}
                helperText={fieldErrors.password}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label={showPassword ? "Hide password" : "Show password"}
                        onClick={() => setShowPassword(v => !v)}
                        onMouseDown={e => e.preventDefault()}
                        edge="end"
                        tabIndex={0}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                inputProps={{ "aria-label": "Password" }}
              />
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Box sx={{ display: "flex", alignItems: "center" }}>
                  <input type="checkbox" id="rememberMe" style={{ marginRight: 6 }} />
                  <label htmlFor="rememberMe" style={{ fontSize: 14, color: "#757575" }}>Remember Me</label>
                </Box>
                <Button variant="text" size="small" sx={{ textTransform: "none", color: "#1976d2" }} onClick={() => navigate("/reset-password")}>Forgot Password</Button>
              </Box>
              {error && <Typography color="error" variant="body2" sx={{ mb: 1 }}>{error}</Typography>}
              <Button type="submit" fullWidth variant="contained" sx={{ mt: 1, mb: 2, py: 1.3, fontWeight: 700, fontSize: 16, borderRadius: 2 }} disabled={!email || !password}>
                Login
              </Button>
              <Typography align="center" sx={{ color: "#bdbdbd", fontSize: 14, mb: 1 }}>Or login with</Typography>
              <Box sx={{ display: "flex", gap: 2, justifyContent: "center", mb: 2 }}>
                <Button variant="outlined" startIcon={<GoogleIcon />} sx={{ textTransform: "none", bgcolor: "#fff", borderColor: "#e0e0e0", color: "#444", fontWeight: 600, width: 160 }} disabled>
                  Google
                </Button>
                <Button variant="outlined" startIcon={<LinkedInIcon />} sx={{ textTransform: "none", bgcolor: "#fff", borderColor: "#e0e0e0", color: "#0077b5", fontWeight: 600, width: 160 }} disabled>
                  LinkedIn
                </Button>
              </Box>
              <Typography align="center" sx={{ fontSize: 14 }}>
                You’re new in here? <Button variant="text" size="small" sx={{ textTransform: "none", color: "#1976d2", fontWeight: 700, p: 0 }} onClick={() => navigate("/register")}>Create Account</Button>
              </Typography>
            </Box>
            <Box sx={{ mt: 4, color: "#bdbdbd", fontSize: 13, textAlign: "center" }}>
              © 2023 Humanline. Alrights reserved. <Button variant="text" size="small" sx={{ color: "#1976d2", textTransform: "none", p: 0 }}>Terms & Conditions</Button> <Button variant="text" size="small" sx={{ color: "#1976d2", textTransform: "none", p: 0 }}>Privacy Policy</Button>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}

export default LoginPage;