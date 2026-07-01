FROM node:18-alpine
WORKDIR /usr/src/app
COPY package.json package-lock.json* yarn.lock* ./
RUN npm install || yarn install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
