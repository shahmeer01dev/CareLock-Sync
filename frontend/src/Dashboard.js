import React, { useEffect, useState } from "react";
import axios from "axios";
import { 
  Box, 
  Typography, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  Chip,
  Grid
} from "@mui/material";
import PersonIcon from '@mui/icons-material/Person';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';

// Configuration
const CENTRAL_API = "http://localhost:8001";
const TENANT_ID = "hospital_01";

function Dashboard() {
  const [patients, setPatients] = useState([]);
  const [encounters, setEncounters] = useState([]);
  const [observations, setObservations] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const pRes = await axios.get(`${CENTRAL_API}/data/patients/${TENANT_ID}`);
      const eRes = await axios.get(`${CENTRAL_API}/data/encounters/${TENANT_ID}`);
      const oRes = await axios.get(`${CENTRAL_API}/data/observations/${TENANT_ID}`);
      
      setPatients(pRes.data);
      setEncounters(eRes.data);
      setObservations(oRes.data);
    } catch (error) {
      console.error("Error fetching dashboard data", error);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>
            <LocalHospitalIcon color="error" sx={{ mr: 1, verticalAlign: "bottom" }} />
            Live Hospital Sync Data
        </Typography>

        <Grid container spacing={3}>
            {/* Patients Table */}
            <Grid item xs={12} md={6}>
                <TableContainer component={Paper} elevation={3}>
                    <Box p={2} bgcolor="#e3f2fd">
                        <Typography variant="h6">Patients Synced ({patients.length})</Typography>
                    </Box>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell><b>Name</b></TableCell>
                                <TableCell><b>Gender</b></TableCell>
                                <TableCell><b>DOB</b></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {patients.map((p) => (
                                <TableRow key={p.id}>
                                    <TableCell>
                                        <Box display="flex" alignItems="center">
                                            <PersonIcon color="action" fontSize="small" sx={{ mr: 1 }} />
                                            {p.name[0].text}
                                        </Box>
                                    </TableCell>
                                    <TableCell>{p.gender}</TableCell>
                                    <TableCell>{p.birthDate}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Grid>

            {/* Lab Results Table */}
            <Grid item xs={12} md={6}>
                <TableContainer component={Paper} elevation={3}>
                    <Box p={2} bgcolor="#fff3e0">
                        <Typography variant="h6">Recent Lab Results ({observations.length})</Typography>
                    </Box>
                    <Table size="small">
                        <TableHead>
                            <TableRow>
                                <TableCell><b>Test</b></TableCell>
                                <TableCell><b>Result</b></TableCell>
                                <TableCell><b>Date</b></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {observations.map((o) => (
                                <TableRow key={o.id}>
                                    <TableCell>{o.code.text}</TableCell>
                                    <TableCell>
                                        <Chip 
                                            label={o.valueString} 
                                            color={o.valueString === "Normal" ? "success" : "error"} 
                                            size="small" 
                                        />
                                    </TableCell>
                                    <TableCell>{o.effectiveDateTime}</TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            </Grid>
        </Grid>
    </Box>
  );
}

export default Dashboard;