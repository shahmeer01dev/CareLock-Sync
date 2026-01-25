import React from "react";
import Chatbot from "./Chatbot";
import { Container, CssBaseline, Typography, Box } from "@mui/material";

function App() {
  return (
    <React.Fragment>
      <CssBaseline />
      <Container maxWidth="md">
        <Box sx={{ textAlign: "center", mt: 5, mb: 2 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            🏥 CareLock Sync
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Secure Hospital Integration & AI Analytics
          </Typography>
        </Box>
        
        {/* Render the Chat Interface */}
        <Chatbot />
        
      </Container>
    </React.Fragment>
  );
}

export default App;