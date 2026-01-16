// src/pages/Wardrobe.jsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../api/axios';
import Dropzone from 'react-dropzone';
import {
  Grid,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Chip,
  CircularProgress,
  Alert,
  LinearProgress,
  Box,
  Stack,
  Container,
  Button,
  Skeleton,
} from '@mui/material';
import CloudUploadOutlinedIcon from '@mui/icons-material/CloudUploadOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';

const fetchWardrobeItems = async () => {
  const res = await api.get('/wardrobe/my-items'); // ← adjust endpoint if different
  return res.data?.items || res.data || [];
};

export default function Wardrobe() {
  const queryClient = useQueryClient();
  const [uploadStatus, setUploadStatus] = useState(null);

  // Fetch user's wardrobe items
  const {
    data: items = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['wardrobe'],
    queryFn: fetchWardrobeItems,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      // Optional: add mitumba flags etc.
      // formData.append('is_mitumba', true);
      return api.post('/wardrobe/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wardrobe'] });
      setUploadStatus({ type: 'success', message: 'Item uploaded and classified successfully!' });
    },
    onError: (err) => {
      setUploadStatus({
        type: 'error',
        message: err.response?.data?.detail || 'Upload failed. Please try again.',
      });
    },
  });

  return (
    <Container maxWidth="xl" sx={{ py: 6, minHeight: '100vh' }}>
      {/* Header */}
      <Stack spacing={1} alignItems="center" mb={6} textAlign="center">
        <Typography variant="h4" fontWeight={800} color="primary.dark">
          My AI Wardrobe
        </Typography>
        <Typography variant="body1" color="text.secondary" maxWidth={600}>
          Upload your clothes — AI automatically classifies category, color, style, material, seasonality
          and even suggests upcycling ideas for your mitumba finds.
        </Typography>
      </Stack>

      {/* Upload Status */}
      {uploadStatus && (
        <Alert
          severity={uploadStatus.type}
          sx={{ mb: 4, maxWidth: 600, mx: 'auto' }}
          onClose={() => setUploadStatus(null)}
        >
          {uploadStatus.message}
        </Alert>
      )}

      {/* Upload Dropzone */}
      <Dropzone
        onDrop={(acceptedFiles) => {
          if (acceptedFiles.length > 0) {
            uploadMutation.mutate(acceptedFiles[0]);
          }
        }}
        accept={{ 'image/*': ['.jpg', '.jpeg', '.png'] }}
        multiple={false}
        disabled={uploadMutation.isPending}
      >
        {({ getRootProps, getInputProps, isDragActive }) => (
          <Box
            {...getRootProps()}
            sx={{
              border: '3px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.400',
              borderRadius: 4,
              p: { xs: 6, md: 10 },
              mb: 6,
              textAlign: 'center',
              bgcolor: isDragActive ? 'primary.light' : 'grey.50',
              transition: 'all 0.3s ease',
              cursor: uploadMutation.isPending ? 'not-allowed' : 'pointer',
              opacity: uploadMutation.isPending ? 0.6 : 1,
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadOutlinedIcon
              sx={{ fontSize: 60, color: isDragActive ? 'primary.main' : 'grey.500', mb: 2 }}
            />
            <Typography variant="h6" fontWeight={600} gutterBottom>
              {isDragActive
                ? 'Drop your clothing image here...'
                : 'Drag & drop or click to upload clothing photo'}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Supported: JPG, PNG • Best results with clear, well-lit photos
            </Typography>

            {uploadMutation.isPending && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Classifying with AI...
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </Dropzone>

      {/* Wardrobe Content */}
      {isLoading ? (
        <Grid container spacing={3}>
          {[...Array(8)].map((_, i) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={i}>
              <Card sx={{ borderRadius: 3 }}>
                <Skeleton variant="rectangular" height={280} />
                <CardContent>
                  <Skeleton variant="text" height={32} width="60%" />
                  <Stack direction="row" spacing={1} mt={1}>
                    <Skeleton variant="rounded" width={60} height={24} />
                    <Skeleton variant="rounded" width={80} height={24} />
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : isError ? (
        <Box textAlign="center" py={8}>
          <Alert severity="error" sx={{ maxWidth: 500, mx: 'auto', mb: 3 }}>
            Failed to load your wardrobe. Please try again.
          </Alert>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={refetch}
          >
            Retry
          </Button>
        </Box>
      ) : items.length === 0 ? (
        <Box textAlign="center" py={10}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Your wardrobe is empty
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 4 }}>
            Start building your smart wardrobe by uploading your first clothing item above
          </Typography>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={() => document.querySelector('.dropzone-area')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Upload Your First Item
          </Button>
        </Box>
      ) : (
        <Grid container spacing={3}>
          {items.map((item) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={item.id || item._id}>
              <Card
                sx={{
                  height: '100%',
                  borderRadius: 3,
                  overflow: 'hidden',
                  transition: 'transform 0.3s ease, box-shadow 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 12,
                  },
                }}
              >
                <CardMedia
                  component="img"
                  height="280"
                  image={item.image_url || item.imageUrl || 'https://via.placeholder.com/300x280?text=No+Image'}
                  alt={`${item.category} - ${item.color}`}
                  sx={{ objectFit: 'cover' }}
                />
                <CardContent sx={{ pb: 3 }}>
                  <Typography variant="subtitle1" fontWeight={700} gutterBottom>
                    {item.category || 'Unknown Category'}
                  </Typography>

                  <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 1.5 }}>
                    <Chip
                      label={item.color || 'N/A'}
                      size="small"
                      sx={{ bgcolor: item.color || '#ccc', color: 'white' }}
                    />
                    <Chip label={item.style || 'casual'} size="small" color="default" />
                    {item.is_mitumba && (
                      <Chip label="Mitumba" size="small" color="success" />
                    )}
                    {item.confidence && (
                      <Chip
                        label={`${Math.round(item.confidence * 100)}% AI match`}
                        size="small"
                        color={item.confidence > 0.8 ? 'success' : item.confidence > 0.6 ? 'warning' : 'error'}
                      />
                    )}
                  </Stack>

                  {item.upcycle_suggestions?.length > 0 && (
                    <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                      Upcycle ideas available
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Container>
  );
}