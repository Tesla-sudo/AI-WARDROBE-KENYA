// src/pages/Wardrobe.js
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import api from '../api/axios';
import Dropzone from 'react-dropzone';
import { Grid, Card, CardMedia, CardContent, Typography, Chip, CircularProgress } from '@mui/material';

const fetchItems = async () => {
  const res = await api.get('/wardrobe/my-items'); // We'll add this route soon
  return res.data || [];
};

export default function Wardrobe() {
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);

  const { data: items = [], isLoading } = useQuery('wardrobe', fetchItems);

  const uploadMutation = useMutation(
    (file) => {
      const formData = new FormData();
      formData.append('image', file);
      return api.post('/wardrobe/upload', formData);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('wardrobe');
        setUploading(false);
      },
    }
  );

  return (
    <div style={{ padding: '20px 40px' }}>
      <h1>My Wardrobe</h1>

      <Dropzone
        onDrop={(files) => {
          setUploading(true);
          uploadMutation.mutate(files[0]);
        }}
        accept={{ 'image/*': [] }}
        multiple={false}
      >
        {({ getRootProps, getInputProps }) => (
          <div
            {...getRootProps()}
            style={{
              border: '4px dashed #1976d2',
              borderRadius: 16,
              padding: 60,
              textAlign: 'center',
              background: '#f0f8ff',
              cursor: 'pointer',
              marginBottom: 40,
            }}
          >
            <input {...getInputProps()} />
            <p style={{ fontSize: 20 }}>Drop your clothing photo here or click to upload</p>
            {uploading && <CircularProgress size={60} />}
          </div>
        )}
      </Dropzone>

      {isLoading ? (
        <CircularProgress />
      ) : (
        <Grid container spacing={4}>
          {items.map((item) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={item._id}>
              <Card elevation={3}>
                <CardMedia component="img" height="340" image={item.imageUrl} alt={item.category} />
                <CardContent>
                  <Typography variant="h6" style={{ textTransform: 'capitalize' }}>
                    {item.category || 'Unknown'}
                  </Typography>
                  <div style={{ marginTop: 8 }}>
                    <Chip label={item.color || 'N/A'} color="primary" size="small" style={{ marginRight: 8 }} />
                    <Chip label={item.style || 'casual'} size="small" />
                  </div>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </div>
  );
}