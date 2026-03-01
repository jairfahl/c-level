#!/bin/sh
# Run database migrations then seed
set -e
echo "Running Prisma migrations..."
npx prisma migrate deploy
echo "Seeding database..."
npx ts-node prisma/seed.ts
echo "Done."
