// Local contract fixture based on sync.so asset uploads and generation API docs.
// An owner-provided mock was unavailable; nothing is published or called remotely.
const http = require('http');
const state = { uploads: {}, assets: {}, jobs: {}, count: 0, mode: 'success', media: '' };
http.createServer(async (req, res) => {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  const raw = Buffer.concat(chunks);
  const path = req.url.split('?')[0];
  const origin = `http://${req.headers.host}/sync`;
  const send = (code, value) => { res.writeHead(code, {'Content-Type':'application/json'}); res.end(JSON.stringify(value)); };
  let body = {};
  try { if ((req.headers['content-type'] || '').includes('json') && raw.length) body = JSON.parse(raw); }
  catch { return send(400, {errorCode:'invalid_json'}); }
  if (path === '/control') {
    state.mode = body.mode || 'success'; state.media = body.media || state.media;
    state.uploads = {}; state.assets = {}; state.jobs = {}; state.count = 0;
    return send(200, {ok:true});
  }
  if (path === '/state') return send(200, state);
  if (path === '/redirect.mp4') {
    if (req.headers['x-api-key']) return send(400, {errorCode:'credential_leak'});
    const locations = {redirect: './output.mp4', loop: './redirect.mp4', unsafe: 'file:///tmp/output.mp4'};
    res.writeHead(302, state.mode === 'missing_location' ? {} : {Location: locations[state.mode] || './output.mp4'});
    return res.end();
  }
  if (path.startsWith('/storage/') || path === '/output.mp4') {
    if (req.headers['x-api-key']) return send(400, {errorCode:'credential_leak'});
    if (path === '/output.mp4') {
      res.writeHead(200, {'Content-Type':'video/mp4'});
      return res.end(Buffer.from(state.mode === 'empty' ? '' : state.media, 'base64'));
    }
    const id = path.split('/').pop();
    const expected = state.uploads[id];
    if (!expected || req.method !== 'PUT' || expected.size !== raw.length || expected.contentType !== req.headers['content-type'])
      return send(400, {errorCode:'invalid_upload'});
    expected.received = true;
    return send(200, {});
  }
  if (req.headers['x-api-key'] !== 'test-only') return send(401, {errorCode:'unauthorized'});
  if (state.mode === 'unauthorized') return send(401, {errorCode:'invalid_api_key'});
  if (path === '/v2/assets/upload') {
    const id = String(++state.count);
    state.uploads[id] = body;
    return send(201, {uploadUrl:`${origin}/storage/${id}`,url:`${origin}/asset/${id}`,expiresIn:3600});
  }
  if (path === '/v2/assets') {
    const id = body.url.split('/').pop();
    if (!state.uploads[id]?.received) return send(422, {errorCode:'upload_missing'});
    state.assets[id] = body;
    return send(201, {id});
  }
  if (path === '/v2/generate' && req.method === 'POST') {
    if (!req.headers['idempotency-key'] || body.options?.sync_mode !== 'silence' || body.input?.length !== 2 ||
        body.input.some(x => !state.assets[x.assetId] || state.assets[x.assetId].type.toLowerCase() !== x.type))
      return send(422, {errorCode:'invalid_generation'});
    const id = 'job-1'; state.jobs[id] = {polls:0,body};
    return send(201, {id,status:'PENDING'});
  }
  if (path === '/v2/generate/job-1') {
    if (!state.jobs['job-1']) return send(404, {errorCode:'not_found'});
    state.jobs['job-1'].polls++;
    if (state.mode === 'failed' || state.mode === 'rejected')
      return send(200, {id:'job-1',status:state.mode.toUpperCase(),error:'face not found',errorCode:'no_face'});
    if (state.mode === 'pending' || state.jobs['job-1'].polls === 1) return send(200, {id:'job-1',status:'PROCESSING'});
    return send(200, {id:'job-1',status:'COMPLETED',outputUrl:`${origin}/${['redirect', 'loop', 'unsafe', 'missing_location'].includes(state.mode) ? 'redirect.mp4' : 'output.mp4'}`});
  }
  return send(501, {errorCode:'endpoint_not_modeled'});
}).listen(process.env.PORT);
