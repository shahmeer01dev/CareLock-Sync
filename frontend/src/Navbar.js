import React from "react";
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link } from "react-router-dom";
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';

function Navbar() {
  return (
    <AppBar position="static">
      <Toolbar>
        {/* Logo Area */}
        <LocalHospitalIcon sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          CareLock Sync
        </Typography>

        {/* Navigation Buttons */}
        <Box>
          <Button color="inherit" component={Link} to="/">
            Clinical Chat
          </Button>
          <Button color="inherit" component={Link} to="/dashboard">
            Analytics Dashboard
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;