// src/components/HeroSection.jsx
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import { Typography, Button, Box, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';

export default function HeroSection() {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        bgcolor: 'primary.dark', // deep green
        color: 'white',
        pt: { xs: 12, md: 18 },
        pb: { xs: 12, md: 18 },
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)',
      }}
    >
      {/* Subtle animated background circles */}
      <Box
        sx={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          opacity: 0.15,
          pointerEvents: 'none',
        }}
      >
        <motion.div
          animate={{
            scale: [1, 1.3, 1],
            x: [0, 100, 0],
            y: [0, -50, 0],
          }}
          transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
          style={{
            position: 'absolute',
            width: 400,
            height: 400,
            borderRadius: '50%',
            background: 'radial-gradient(circle, #81c784, transparent)',
            top: '10%',
            left: '15%',
          }}
        />
        <motion.div
          animate={{
            scale: [1, 1.4, 1],
            x: [0, -80, 0],
            y: [0, 60, 0],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "easeInOut", delay: 3 }}
          style={{
            position: 'absolute',
            width: 500,
            height: 500,
            borderRadius: '50%',
            background: 'radial-gradient(circle, #a5d6a7, transparent)',
            bottom: '15%',
            right: '10%',
          }}
        />
      </Box>

      <Container maxWidth="lg" sx={{ position: 'relative', zIndex: 1 }}>
        <motion.div
          initial={{ opacity: 0, y: 80 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, ease: 'easeOut' }}
        >
          <Typography
            variant="h1"
            sx={{
              fontSize: { xs: '3rem', sm: '4.5rem', md: '6rem' },
              fontWeight: 900,
              lineHeight: 1.05,
              mb: 4,
              letterSpacing: '-0.02em',
              textShadow: '0 4px 20px rgba(0,0,0,0.3)',
            }}
          >
            AI Wardrobe Kenya
          </Typography>

          <Typography
            variant="h5"
            sx={{
              maxWidth: 800,
              mx: 'auto',
              mb: 6,
              fontWeight: 400,
              opacity: 0.95,
            }}
          >
            Your personal AI fashion assistant — upload, organize, discover trends, 
            match outfits, embrace mitumba, and dress sustainably — all made for Kenya.
          </Typography>

          <Box sx={{ display: 'flex', gap: 4, justifyContent: 'center', flexWrap: 'wrap' }}>
            <motion.div whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.96 }}>
              <Button
                variant="contained"
                size="large"
                sx={{
                  px: 8,
                  py: 2.5,
                  fontSize: '1.4rem',
                  fontWeight: 700,
                  borderRadius: 50,
                  boxShadow: '0 8px 30px rgba(0,0,0,0.25)',
                  background: 'linear-gradient(45deg, #43a047, #66bb6a)',
                  '&:hover': {
                    background: 'linear-gradient(45deg, #388e3c, #5cb85c)',
                    boxShadow: '0 12px 40px rgba(0,0,0,0.35)',
                  }
                }}
                onClick={() => navigate('/register')}
              >
                Get Started Free
              </Button>
            </motion.div>

            <motion.div whileHover={{ scale: 1.08 }} whileTap={{ scale: 0.96 }}>
              <Button
                variant="outlined"
                size="large"
                sx={{
                  px: 8,
                  py: 2.5,
                  fontSize: '1.4rem',
                  fontWeight: 600,
                  borderRadius: 50,
                  borderWidth: 2,
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': {
                    borderColor: 'white',
                    bgcolor: 'rgba(255,255,255,0.15)',
                  }
                }}
                onClick={() => navigate('/login')}
              >
                Login
              </Button>
            </motion.div>
          </Box>
        </motion.div>
      </Container>
    </Box>
  );
}