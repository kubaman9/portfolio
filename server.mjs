import http from 'node:http';
const srv = http.createServer((req,res)=>{ res.end('ok'); });
srv.listen(9090, '127.0.0.1', () => console.log('listening on 127.0.0.1:9090'));
