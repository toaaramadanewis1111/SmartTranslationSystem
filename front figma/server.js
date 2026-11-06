const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml'
};
const port = Number(process.env.PORT || 3000);

http.createServer((req, res) => {
  let pathname;
  try {
    pathname = decodeURIComponent(
      new URL(req.url, 'http://localhost').pathname
    );
  } catch {
    res.writeHead(400);
    res.end('Bad request');
    return;
  }

  const relativePath = pathname === '/' ? 'index.html' : pathname.slice(1);
  const file = path.resolve(ROOT, relativePath);
  if (file !== ROOT && !file.startsWith(`${ROOT}${path.sep}`)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(file, (error, data) => {
    if (error) {
      res.writeHead(error.code === 'ENOENT' ? 404 : 500);
      res.end(error.code === 'ENOENT' ? 'Not found' : 'Unable to read file');
      return;
    }

    res.writeHead(200, {
      'content-type': TYPES[path.extname(file)] || 'application/octet-stream'
    });
    res.end(data);
  });
}).listen(port, () => {
  console.log(`LangoLink frontend running at http://localhost:${port}`);
});
