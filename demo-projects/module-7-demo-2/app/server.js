const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const APP_NAME = process.env.APP_NAME || 'Dockerized Node App';

app.get('/', (req, res) => res.send(`<h1>Hi from ${APP_NAME}</h1>`));
app.get('/health', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));

app.listen(PORT, () => console.log(`${APP_NAME} listening on port ${PORT}`));
