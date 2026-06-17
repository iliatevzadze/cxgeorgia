FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

RUN chown -R node:node /app

USER node

EXPOSE 3000

CMD ["npx", "next", "dev", "--hostname", "0.0.0.0", "--port", "3000"]
