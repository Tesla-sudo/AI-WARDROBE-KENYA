// src/pages/Register.jsx
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  Link,
  Container,
  Paper,
  CircularProgress,
  InputAdornment,
  IconButton,
} from '@mui/material';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';

export default function Register() {
  const { register, error: authError, loading: authLoading } = useAuth();
  // eslint-disable-next-line no-unused-vars
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError('');

    // Client-side validation
    if (!fullName.trim()) {
      setFormError('Full name is required');
      return;
    }
    if (!email.includes('@') || !email.includes('.')) {
      setFormError('Please enter a valid email address');
      return;
    }
    if (password.length < 6) {
      setFormError('Password must be at least 6 characters');
      return;
    }
    if (password !== confirmPassword) {
      setFormError('Passwords do not match');
      return;
    }

    setSubmitting(true);

    try {
      await register(email, password, fullName.trim());
      // Auto-redirect happens inside register function
    // eslint-disable-next-line no-unused-vars
    } catch (err) {
      // Error already set in context — just show it
    } finally {
      setSubmitting(false);
    }
  };

  const isLoading = authLoading || submitting;

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Paper
        elevation={6}
        sx={{
          p: { xs: 4, md: 6 },
          borderRadius: 4,
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h4" align="center" fontWeight={700} gutterBottom>
          Create Your Account
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 5 }}>
          Join AI Wardrobe Kenya and start building your smart, sustainable wardrobe today
        </Typography>

        {(authError || formError) && (
          <Alert severity="error" sx={{ mb: 4 }} onClose={() => {
            setFormError('');
            // authError cleared via context
          }}>
            {formError || authError}
          </Alert>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <TextField
            label="Full Name"
            fullWidth
            margin="normal"
            variant="outlined"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            disabled={isLoading}
            autoFocus
          />

          <TextField
            label="Email Address"
            type="email"
            fullWidth
            margin="normal"
            variant="outlined"
            value={email}
            onChange={(e) => setEmail(e.target.value.trim())}
            required
            disabled={isLoading}
          />

          <TextField
            label="Password"
            type={showPassword ? 'text' : 'password'}
            fullWidth
            margin="normal"
            variant="outlined"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={isLoading}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                    disabled={isLoading}
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />

          <TextField
            label="Confirm Password"
            type={showPassword ? 'text' : 'password'}
            fullWidth
            margin="normal"
            variant="outlined"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            disabled={isLoading}
          />

          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            disabled={isLoading}
            sx={{
              mt: 4,
              py: 1.8,
              fontSize: '1.1rem',
              fontWeight: 600,
              boxShadow: 3,
            }}
          >
            {isLoading ? (
              <>
                <CircularProgress size={24} sx={{ mr: 2 }} />
                Creating account...
              </>
            ) : (
              'Sign Up'
            )}
          </Button>
        </form>

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Already have an account?{' '}
            <Link
              href="/login"
              underline="hover"
              sx={{ fontWeight: 600, cursor: 'pointer' }}
            >
              Log in here
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
}