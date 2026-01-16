// src/components/FeatureCard.jsx
import { Card, CardContent, Typography, Box } from '@mui/material';
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';

export default function FeatureCard({ icon, title, description }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.8, ease: "easeOut" }}
    >
      <Card
        sx={{
          height: '100%',
          borderRadius: 4,
          boxShadow: '0 6px 20px rgba(0,0,0,0.08)',
          transition: 'all 0.3s ease',
          overflow: 'hidden',
          bgcolor: 'white',
          '&:hover': {
            transform: 'translateY(-12px)',
            boxShadow: '0 20px 40px rgba(46,125,50,0.18)',
            border: '1px solid #66bb6a',
          },
        }}
      >
        <Box
          sx={{
            height: 140,
            bgcolor: '#e8f5e9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '4px solid #4caf50',
          }}
        >
          {icon}
        </Box>

        <CardContent sx={{ p: 4 }}>
          <Typography
            variant="h5"
            fontWeight={700}
            gutterBottom
            sx={{ color: 'primary.dark' }}
          >
            {title}
          </Typography>
          <Typography variant="body1" color="text.secondary" lineHeight={1.7}>
            {description}
          </Typography>
        </CardContent>
      </Card>
    </motion.div>
  );
}