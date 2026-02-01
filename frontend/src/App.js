import React from "react";
import Chatbot from "./Chatbot";
import Dashboard from "./Dashboard"; // Import the new component
import { Container, CssBaseline, Typography, Box, Divider } from "@mui/material";

function App() {
  return (
    <React.Fragment>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ textAlign: "center", mt: 5, mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom fontWeight="bold" color="primary">
            🏥 CareLock Sync
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Secure Hospital Integration & AI Analytics Platform
          </Typography>
        </Box>
        
        {/* 1. Clinical Assistant */}
        <Chatbot />
        
        <Divider sx={{ my: 6 }} />

        {/* 2. Data Analyst Dashboard */}
        <Dashboard />

        <Box sx={{ pb: 8 }} /> {/* Spacer at bottom */}
      </Container>
    </React.Fragment>
  );
}

export default App;