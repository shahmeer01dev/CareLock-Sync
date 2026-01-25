import React, { useState } from "react";
import axios from "axios";
import { 
  Box, 
  TextField, 
  Button, 
  Paper, 
  Typography, 
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider
} from "@mui/material";
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';

// Configuration
const CHAT_API = "http://localhost:8002/chat";

function Chatbot() {
  const [question, setQuestion] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!question.trim()) return;

    // 1. Add user question to history immediately
    const newHistory = [...history, { sender: "user", text: question }];
    setHistory(newHistory);
    setLoading(true);

    try {
      // 2. Call your Python Backend
      const res = await axios.post(CHAT_API, { question: question });
      
      // 3. Add AI response to history
      setHistory([...newHistory, { sender: "bot", text: res.data.answer }]);
    } catch (error) {
      setHistory([...newHistory, { sender: "bot", text: "Error: Could not reach the AI brain." }]);
    }

    setLoading(false);
    setQuestion("");
  };

  return (
    <Paper elevation={3} sx={{ padding: 4, maxWidth: 600, margin: "auto", mt: 4 }}>
      <Box display="flex" alignItems="center" mb={2}>
        <SmartToyIcon color="primary" sx={{ fontSize: 40, mr: 2 }} />
        <Typography variant="h5">CareLock Clinical Assistant</Typography>
      </Box>
      <Divider />

      {/* Chat History Area */}
      <Box sx={{ height: 300, overflowY: "auto", my: 2, border: "1px solid #eee", padding: 2, borderRadius: 2 }}>
        <List>
          {history.map((msg, index) => (
            <ListItem key={index} sx={{ justifyContent: msg.sender === "user" ? "flex-end" : "flex-start" }}>
              <Paper 
                sx={{ 
                  p: 2, 
                  bgcolor: msg.sender === "user" ? "#e3f2fd" : "#f5f5f5",
                  maxWidth: "80%"
                }}
              >
                <ListItemText primary={msg.text} />
              </Paper>
            </ListItem>
          ))}
          {loading && <CircularProgress size={20} sx={{ ml: 2 }} />}
        </List>
      </Box>

      {/* Input Area */}
      <Box display="flex" gap={1}>
        <TextField 
          fullWidth 
          label="Ask a clinical question..." 
          variant="outlined" 
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
        />
        <Button variant="contained" endIcon={<SendIcon />} onClick={handleSend} disabled={loading}>
          Send
        </Button>
      </Box>
    </Paper>
  );
}

export default Chatbot;