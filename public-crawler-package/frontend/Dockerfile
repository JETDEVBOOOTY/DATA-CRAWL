FROM node:20-alpine
WORKDIR /app
COPY package.json yarn.lock* ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npx","serve","-s","build","-l","3000"]
