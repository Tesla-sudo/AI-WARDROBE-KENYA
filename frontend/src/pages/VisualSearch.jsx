// src/pages/VisualSearch.js
import { useState } from 'react';
import { useMutation } from 'react-query';
import api from '../api/axios';
import Dropzone from 'react-dropzone';
import { Grid, Card, CardMedia, Typography, LinearProgress } from '@mui/material';

export default function VisualSearch() {
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const search = useMutation(
    (file) => {
      const formData = new FormData();
      formData.append('image', file);
      return api.post('/wardrobe/visual-search', formData);
    },
    {
      onSuccess: (res) => {
        setResults(res.data.matches || []);
        setSearching(false);
      },
    }
  );

  return (
    <div style={{ padding: '20px 40px' }}>
      <h1>Visual Search</h1>
      <p>Upload any clothing photo — we’ll find similar items in your closet!</p>

      <Dropzone
        onDrop={(files) => {
          setSearching(true);
          setResults([]);
          search.mutate(files[0]);
        }}
        accept={{ 'image/*': [] }}
        multiple={false}
      >
        {({ getRootProps, getInputProps }) => (
          <div
            {...getRootProps()}
            style={{
              border: '5px dashed #ff5722',
              borderRadius: 20,
              padding: 80,
              textAlign: 'center',
              background: '#fff3e0',
              cursor: 'pointer',
            }}
          >
            <input {...getInputProps()} />
            <p style={{ fontSize: 22 }}>Drop image here or click</p>
            {searching && <LinearProgress style={{ marginTop: 20 }} />}
          </div>
        )}
      </Dropzone>

      {results.length > 0 && (
        <>
          <h2>Found {results.length} similar items</h2>
          <Grid container spacing={3}>
            {results.map((item) => (
              <Grid item xs={6} sm={4} md={3} key={item._id}>
                <Card>
                  <CardMedia component="img" height="300" image={item.imageUrl} />
                </Card>
              </Grid>
            ))}
          </Grid>
        </>
      )}
    </div>
  );
}