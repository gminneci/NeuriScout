# Google Authentication Setup for NeuriScout

## 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API" and enable it
4. Create OAuth credentials:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "NeuriScout"
   - Authorized redirect URIs:
     - For local: `http://localhost:3000/api/auth/callback/google`
     - For production: `https://your-domain.vercel.app/api/auth/callback/google`
   - Click "Create"
   - Copy the Client ID and Client Secret

## 2. Configure Environment Variables

Create `frontend/.env.local`:

```bash
# NextAuth Configuration
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=<generate-with: openssl rand -base64 32>

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 3. For Production (Vercel)

Add these environment variables in Vercel dashboard:

- `NEXTAUTH_URL`: `https://your-app.vercel.app`
- `NEXTAUTH_SECRET`: (same secret or generate a new one)
- `GOOGLE_CLIENT_ID`: (your Google OAuth client ID)
- `GOOGLE_CLIENT_SECRET`: (your Google OAuth client secret)
- `NEXT_PUBLIC_API_URL`: (your Railway backend URL)

Don't forget to add the production callback URL to Google OAuth settings!

## 4. Test Locally

```bash
cd frontend
npm run dev
```

Visit http://localhost:3000 - you should be redirected to sign in with Google.
