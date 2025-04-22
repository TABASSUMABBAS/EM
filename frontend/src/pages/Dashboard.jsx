import React from "react";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";

function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome to the Employee Management System
      </Typography>
      <Typography variant="body1">
        Select a module from the sidebar to get started.
      </Typography>
    </Box>
  );
}

export default Dashboard;