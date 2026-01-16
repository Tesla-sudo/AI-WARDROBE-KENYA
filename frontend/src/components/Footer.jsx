// src/components/Footer.jsx
import { Box, Typography, Container, Link, Stack } from '@mui/material';

export default function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        bgcolor: '#1b5e20', // deep forest green
        color: 'white',
        py: 8,
        mt: 'auto',
      }}
    >
      <Container maxWidth="lg">
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={4}
          justifyContent="space-between"
          alignItems={{ xs: 'center', md: 'flex-start' }}
        >
          <Box>
            <Typography variant="h6" fontWeight={700} gutterBottom>
              AI Wardrobe Kenya
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8, maxWidth: 400 }}>
              Smart AI-powered wardrobe management built for Kenyan style, sustainability, and affordability.
            </Typography>
          </Box>

          <Stack direction="row" spacing={5}>
            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Quick Links
              </Typography>
              <Stack spacing={1}>
                <Link href="/wardrobe" color="inherit" underline="hover">Wardrobe</Link>
                <Link href="/visual-search" color="inherit" underline="hover">Visual Search</Link>
                <Link href="/trends" color="inherit" underline="hover">Trends</Link>
              </Stack>
            </Box>

            <Box>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Legal
              </Typography>
              <Stack spacing={1}>
                <Link href="#" color="inherit" underline="hover">Privacy Policy</Link>
                <Link href="#" color="inherit" underline="hover">Terms of Service</Link>
              </Stack>
            </Box>
          </Stack>
        </Stack>

        <Typography variant="body2" align="center" sx={{ mt: 6, opacity: 0.7 }}>
          © {new Date().getFullYear()} AI Wardrobe Kenya. Built with ❤️ for a greener fashion future.
        </Typography>
      </Container>
    </Box>
  );
}