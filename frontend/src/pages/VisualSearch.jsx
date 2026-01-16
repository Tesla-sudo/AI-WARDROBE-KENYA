// src/pages/VisualSearch.jsx
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import api from '../api/axios';
import Dropzone from 'react-dropzone';
import {
  Grid,
  Card,
  CardMedia,
  Typography,
  LinearProgress,
  Alert,
  Box,
  Container,
  Paper,
} from '@mui/material';

export default function VisualSearch() {
  const [results, setResults] = useState([]);
  const [status, setStatus] = useState(null);

  const searchMutation = useMutation({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/wardrobe/visual-search', formData);
      return res.data;
    },
    onSuccess: (data) => {
      setResults(data.similar_items || []);
      setStatus({
        type: 'success',
        message: data.message || `Found ${data.similar_items?.length || 0} similar items!`,
      });
    },
    onError: (err) => {
      setStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Search failed. Try again.',
      });
    },
  });

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Paper sx={{ p: 5, borderRadius: 4, mb: 6 }}>
        <Typography variant="h3" align="center" gutterBottom fontWeight={700}>
          Visual Search
        </Typography>
        <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 4 }}>
          Upload a photo of any outfit or style you like — even from Instagram or TikTok — and see what matches in your wardrobe!
        </Typography>

        {status && (
          <Alert severity={status.type} sx={{ mb: 4 }} onClose={() => setStatus(null)}>
            {status.message}
          </Alert>
        )}

        <Dropzone
          onDrop={(files) => {
            if (files.length > 0) {
              searchMutation.mutate(files[0]);
            }
          }}
          accept={{ 'image/*': [] }}
          multiple={false}
        >
          {({ getRootProps, getInputProps, isDragActive }) => (
            <Box
              {...getRootProps()}
              sx={{
                border: '3px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.400',
                borderRadius: 4,
                p: { xs: 8, md: 12 },
                textAlign: 'center',
                bgcolor: isDragActive ? 'primary.light' : 'grey.50',
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                '&:hover': { bgcolor: 'grey.100' },
              }}
            >
              <input {...getInputProps()} />
              <Typography variant="h5" gutterBottom>
                {isDragActive ? 'Drop the image here...' : 'Drop an image or click to browse'}
              </Typography>
              <Typography color="text.secondary">
                Search your wardrobe for similar styles
              </Typography>
              {searchMutation.isPending && <LinearProgress sx={{ mt: 3 }} />}
            </Box>
          )}
        </Dropzone>
      </Paper>

      {results.length > 0 && (
        <Box>
          <Typography variant="h5" gutterBottom align="center">
            Found {results.length} Similar Items in Your Wardrobe
          </Typography>
          <Grid container spacing={3} justifyContent="center">
            {results.map((item) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={item.item_id}>
                <Card sx={{ borderRadius: 3, overflow: 'hidden' }}>
                  <CardMedia
                    component="img"
                    height="320"
                    image={item.image_url}
                    alt={`${item.category} - ${item.color}`}
                  />
                  <CardContent>
                    <Typography variant="subtitle1" fontWeight={600}>
                      {item.category}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {item.color} • {item.style}
                    </Typography>
                    <Typography variant="caption" color="primary">
                      Similarity: {(item.similarity_score * 100).toFixed(0)}%
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}

      {results.length === 0 && !searchMutation.isPending && (
        <Typography align="center" color="text.secondary" mt={6}>
          No matches yet — upload more items or try a different photo!
        </Typography>
      )}
    </Container>
  );
}