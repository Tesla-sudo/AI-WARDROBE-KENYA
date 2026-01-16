// src/pages/Home.jsx
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import {
  Container,
  Typography,
  Box,
  Grid,
  Button,
  useTheme,
} from '@mui/material';
import HeroSection from '../components/HeroSection';
import FeatureCard from '../components/FeatureCard';
import Footer from '../components/Footer';
import WardrobeIcon from '@mui/icons-material/Checkroom';
import SearchIcon from '@mui/icons-material/Search';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import RecyclingIcon from '@mui/icons-material/Recycling';

const features = [
  {
    icon: <WardrobeIcon fontSize="large" />,
    title: "Intelligent Wardrobe",
    description: "Upload your clothes — AI instantly classifies category, color, style, material & seasonality"
  },
  {
    icon: <SearchIcon fontSize="large" />,
    title: "Visual Search",
    description: "Upload any outfit photo and find perfect matches in your own closet in seconds"
  },
  {
    icon: <TrendingUpIcon fontSize="large" />,
    title: "Trend Matching",
    description: "Discover what's trending in Kenyan fashion and how it pairs with your wardrobe"
  },
  {
    icon: <RecyclingIcon fontSize="large" />,
    title: "Mitumba & Sustainability",
    description: "Celebrate second-hand fashion — get upcycling ideas and track your carbon footprint"
  },
];

export default function Home() {
  // eslint-disable-next-line no-unused-vars
  const theme = useTheme();

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Hero */}
      <HeroSection />

      {/* Features Section */}
      <Box
        sx={{
          bgcolor: '#e8f5e9', // light green background
          py: { xs: 8, md: 12 },
          flexGrow: 1,
        }}
      >
        <Container maxWidth="lg">
          <Typography
            variant="h4"
            align="center"
            fontWeight={800}
            gutterBottom
            sx={{ color: 'primary.dark' }}
          >
            Everything You Need for a Smarter, Greener Wardrobe
          </Typography>

          <Typography
            variant="subtitle1"
            align="center"
            color="text.secondary"
            sx={{ mb: 8, maxWidth: 800, mx: 'auto' }}
          >
            From AI-powered organization to trend matching and sustainable mitumba ideas — designed for Kenya
          </Typography>

          <Grid container spacing={4}>
            {features.map((feature, index) => (
              <Grid item xs={12} sm={6} md={3} key={index}>
                <FeatureCard {...feature} />
              </Grid>
            ))}
          </Grid>

          {/* Final CTA in this section */}
          <Box sx={{ textAlign: 'center', mt: 10 }}>
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <Button
                variant="contained"
                size="large"
                color="primary"
                sx={{
                  px: 8,
                  py: 2,
                  fontSize: '1.3rem',
                  boxShadow: 6,
                  '&:hover': { boxShadow: 12 },
                }}
                onClick={() => window.location.href = '/register'}
              >
                Start Building Your Wardrobe Now
              </Button>
            </motion.div>
          </Box>
        </Container>
      </Box>

      <Footer />
    </Box>
  );
}