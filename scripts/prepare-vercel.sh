#!/bin/bash
# Run this script before deploying to Vercel
# It switches the Prisma provider to PostgreSQL and generates the client

set -e

echo "=== Preparing for Vercel deployment ==="

# 1. Switch Prisma to PostgreSQL
echo "Switching Prisma provider to PostgreSQL..."
sed -i 's/provider = "sqlite"/provider = "postgresql"/' prisma/schema.prisma
echo "Done."

# 2. Generate Prisma client
echo "Generating Prisma client..."
npx prisma generate
echo "Done."

# 3. Push schema to database (requires DATABASE_URL to be set)
if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
  echo "Pushing schema to PostgreSQL database..."
  npx prisma db push
  echo "Done."
else
  echo "WARNING: DATABASE_URL is not set to a PostgreSQL URL."
  echo "Set it to your Supabase connection string first:"
  echo '  export DATABASE_URL="postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres"'
  echo "Then run this script again."
  exit 1
fi

echo ""
echo "=== Ready for Vercel deployment ==="
echo "Next steps:"
echo "1. Push to GitHub"
echo "2. Import to Vercel"
echo "3. Set environment variables:"
echo "   - DATABASE_URL (your Supabase URL)"
echo "   - NEXTAUTH_SECRET (openssl rand -base64 32)"
echo "   - NEXTAUTH_URL (your Vercel URL)"
echo "   - AUTH_TRUST_HOST=true"
echo "   - NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1"
echo "   - NVIDIA_API_KEY=nvapi-your-key"
echo "4. Deploy!"
