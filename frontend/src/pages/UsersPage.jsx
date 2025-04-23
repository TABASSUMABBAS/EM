import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";

function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editUser, setEditUser] = useState(null);
  const [editEmail, setEditEmail] = useState("");
  const [editRoles, setEditRoles] = useState("");
  const [snackbar, setSnackbar] = useState({ open: false, message: "", severity: "success" });
  const [deleteId, setDeleteId] = useState(null);
  const navigate = useNavigate();

  // Get token from localStorage (should be set on login)
  const token = localStorage.getItem("access_token");

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }
    fetchUsers();
    // eslint-disable-next-line
  }, [token]);

  const fetchUsers = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/users/", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
      } else {
        if (res.status === 403) {
          setError("You do not have permission to view users.");
        } else {
          setError("Failed to fetch users.");
        }
      }
    } catch (err) {
      setError("Network error");
    }
    setLoading(false);
  };

  const handleEdit = (user) => {
    setEditUser(user);
    setEditEmail(user.email);
    setEditRoles(user.roles.join(", "));
  };

  const handleEditSave = async () => {
    try {
      const res = await fetch(`/api/users/${editUser.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ email: editEmail, roles: editRoles.split(",").map(r => r.trim()) })
      });
      if (res.ok) {
        setSnackbar({ open: true, message: "User updated successfully", severity: "success" });
        setEditUser(null);
        fetchUsers();
      } else {
        const data = await res.json();
        setSnackbar({ open: true, message: data.detail || "Update failed", severity: "error" });
      }
    } catch (err) {
      setSnackbar({ open: true, message: "Network error", severity: "error" });
    }
  };

  const handleDelete = async (id) => {
    try {
      const res = await fetch(`/api/users/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.status === 204) {
        setSnackbar({ open: true, message: "User deleted", severity: "success" });
        fetchUsers();
      } else {
        const data = await res.json();
        setSnackbar({ open: true, message: data.detail || "Delete failed", severity: "error" });
      }
    } catch (err) {
      setSnackbar({ open: true, message: "Network error", severity: "error" });
    }
    setDeleteId(null);
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" fontWeight={700} gutterBottom>
        User Management
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <TableContainer component={Paper} sx={{ maxWidth: 900, mx: "auto" }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Roles</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow><TableCell colSpan={4}>Loading...</TableCell></TableRow>
            ) : users.length === 0 ? (
              <TableRow><TableCell colSpan={4}>No users found.</TableCell></TableRow>
            ) : (
              users.map(user => (
                <TableRow key={user.id}>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{user.roles.join(", ")}</TableCell>
                  <TableCell align="right">
                    <IconButton onClick={() => handleEdit(user)}><EditIcon /></IconButton>
                    <IconButton color="error" onClick={() => setDeleteId(user.id)}><DeleteIcon /></IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
      {/* Edit Dialog */}
      <Dialog open={!!editUser} onClose={() => setEditUser(null)}>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <TextField
            margin="normal"
            label="Email"
            fullWidth
            value={editEmail}
            onChange={e => setEditEmail(e.target.value)}
          />
          <TextField
            margin="normal"
            label="Roles (comma separated)"
            fullWidth
            value={editRoles}
            onChange={e => setEditRoles(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditUser(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleEditSave}>Save</Button>
        </DialogActions>
      </Dialog>
      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteId} onClose={() => setDeleteId(null)}>
        <DialogTitle>Delete User</DialogTitle>
        <DialogContent>
          Are you sure you want to delete this user?
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteId(null)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={() => handleDelete(deleteId)}>Delete</Button>
        </DialogActions>
      </Dialog>
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert severity={snackbar.severity} sx={{ width: "100%" }}>{snackbar.message}</Alert>
      </Snackbar>
    </Box>
  );
}

export default UsersPage;