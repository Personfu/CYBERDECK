const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
const API = process.env.API_URL || 'http://localhost:8000';

app.use('/static', express.static(path.join(__dirname, 'public')));
app.use(express.json());

// Helper to proxy API calls
function proxyGet(apiPath) {
    return new Promise((resolve, reject) => {
        const url = new URL(apiPath, API);
        http.get(url.toString(), (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch {
                    resolve(data);
                }
            });
        }).on('error', reject);
    });
}

function proxyPost(apiPath, body) {
    return new Promise((resolve, reject) => {
        const url = new URL(apiPath, API);
        const postData = JSON.stringify(body);
        const options = {
            hostname: url.hostname,
            port: url.port,
            path: url.pathname,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(postData)
            }
        };
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch {
                    resolve(data);
                }
            });
        });
        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

// Pages
app.get('/', (req, res) => res.sendFile(path.join(__dirname, 'public', 'index.html')));
app.get('/projects', (req, res) => res.sendFile(path.join(__dirname, 'public', 'projects.html')));
app.get('/projects/:id', (req, res) => res.sendFile(path.join(__dirname, 'public', 'project-detail.html')));
app.get('/sessions', (req, res) => res.sendFile(path.join(__dirname, 'public', 'sessions.html')));
app.get('/sessions/:id', (req, res) => res.sendFile(path.join(__dirname, 'public', 'session-detail.html')));
app.get('/reports', (req, res) => res.sendFile(path.join(__dirname, 'public', 'reports.html')));
app.get('/reports/:id', (req, res) => res.sendFile(path.join(__dirname, 'public', 'report.html')));
app.get('/settings', (req, res) => res.sendFile(path.join(__dirname, 'public', 'settings.html')));
app.get('/safety', (req, res) => res.sendFile(path.join(__dirname, 'public', 'safety.html')));

// API proxies
app.get('/api/healthz', async (req, res) => {
    try {
        const data = await proxyGet('/healthz');
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/projects', async (req, res) => {
    try {
        const data = await proxyGet('/projects');
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/api/projects', async (req, res) => {
    try {
        const data = await proxyPost('/projects', req.body);
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/projects/:id', async (req, res) => {
    try {
        const data = await proxyGet(`/projects/${req.params.id}`);
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/projects/:id/targets', async (req, res) => {
    try {
        const data = await proxyGet(`/projects/${req.params.id}/targets`);
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/projects/:id/sessions', async (req, res) => {
    try {
        const data = await proxyGet(`/projects/${req.params.id}/sessions`);
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/reports', async (req, res) => {
    try {
        const data = await proxyGet('/reports');
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.get('/api/reports/:id/view', async (req, res) => {
    try {
        const url = new URL(`/reports/${req.params.id}/view`, API);
        http.get(url.toString(), (apiRes) => {
            let data = '';
            apiRes.on('data', chunk => data += chunk);
            apiRes.on('end', () => res.send(data));
        }).on('error', e => res.status(500).send(e.message));
    } catch (e) {
        res.status(500).send(e.message);
    }
});

app.get('/api/settings/ai', async (req, res) => {
    try {
        const data = await proxyGet('/settings/ai');
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

app.post('/api/settings/ai', async (req, res) => {
    try {
        const data = await proxyPost('/settings/ai', req.body);
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// Auth proxy
app.post('/api/auth/login', async (req, res) => {
    try {
        const data = await proxyPost('/auth/login', req.body);
        res.json(data);
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

// AI proxies
app.post('/api/ai/summarize', async (req, res) => {
    try { res.json(await proxyPost('/ai/summarize', req.body)); }
    catch (e) { res.status(500).json({ error: e.message }); }
});
app.post('/api/ai/draft-finding', async (req, res) => {
    try { res.json(await proxyPost('/ai/draft-finding', req.body)); }
    catch (e) { res.status(500).json({ error: e.message }); }
});
app.post('/api/ai/suggest-names', async (req, res) => {
    try { res.json(await proxyPost('/ai/suggest-names', req.body)); }
    catch (e) { res.status(500).json({ error: e.message }); }
});

// Targets/Sessions create proxies
app.post('/api/projects/:id/targets', async (req, res) => {
    try { res.json(await proxyPost(`/projects/${req.params.id}/targets`, req.body)); }
    catch (e) { res.status(500).json({ error: e.message }); }
});
app.post('/api/projects/:id/sessions', async (req, res) => {
    try { res.json(await proxyPost(`/projects/${req.params.id}/sessions`, req.body)); }
    catch (e) { res.status(500).json({ error: e.message }); }
});

// Report generate proxy
app.post('/api/reports/generate', async (req, res) => {
    try { res.json(await proxyPost('/reports/generate', req.body)); }
    catch (e) { res.status(500).json({ error: e.message }); }
});

// CSV export proxy (stream through)
app.get('/api/projects/:id/targets/export.csv', async (req, res) => {
    try {
        const url = new URL(`/projects/${req.params.id}/targets/export.csv`, API);
        http.get(url.toString(), (apiRes) => {
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', apiRes.headers['content-disposition'] || 'attachment; filename=targets.csv');
            apiRes.pipe(res);
        }).on('error', e => res.status(500).send(e.message));
    } catch (e) { res.status(500).send(e.message); }
});

// Artifacts proxy
app.get('/api/artifacts', async (req, res) => {
    try {
        const q = req.query.project_id ? `?project_id=${req.query.project_id}` : '';
        res.json(await proxyGet(`/artifacts${q}`));
    } catch (e) { res.status(500).json({ error: e.message }); }
});

// Upload proxy — pass multipart through to API
const multer = require('multer');
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 50 * 1024 * 1024 } });
app.post('/api/upload', upload.single('file'), async (req, res) => {
    try {
        const FormData = (await import('form-data')).default;
        const form = new FormData();
        form.append('file', req.file.buffer, { filename: req.file.originalname, contentType: req.file.mimetype });
        form.append('project_id', req.body.project_id || '');
        form.append('target_id', req.body.target_id || '');
        form.append('session_id', req.body.session_id || '');
        form.append('kind', req.body.kind || 'file');
        form.append('notes', req.body.notes || '');

        const url = new URL('/upload', API);
        const options = {
            hostname: url.hostname,
            port: url.port,
            path: url.pathname,
            method: 'POST',
            headers: form.getHeaders()
        };
        const apiReq = http.request(options, (apiRes) => {
            let data = '';
            apiRes.on('data', chunk => data += chunk);
            apiRes.on('end', () => { try { res.json(JSON.parse(data)); } catch { res.send(data); } });
        });
        apiReq.on('error', e => res.status(500).json({ error: e.message }));
        form.pipe(apiReq);
    } catch (e) { res.status(500).json({ error: e.message }); }
});

app.listen(3000, () => console.log('FLLC CyberDeck Web UI listening on port 3000'));
