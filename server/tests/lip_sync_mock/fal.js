// Official fal queue + storage initiation contract, local fixture only.
const http = require('http');
const state = { uploads:{}, polls:0, submitted:0, mode:'success', media:'' };
http.createServer(async (req,res) => {
  const chunks=[]; for await (const chunk of req) chunks.push(chunk);
  const raw=Buffer.concat(chunks), path=req.url.split('?')[0];
  const origin=`http://${req.headers.host}/fal`;
  const send=(code,data)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(data));};
  let body={};
  try { if ((req.headers['content-type']||'').includes('json') && raw.length) body=JSON.parse(raw); }
  catch {return send(400,{detail:'invalid JSON'});}
  if (path==='/control') {
    state.mode=body.mode||'success'; state.media=body.media||state.media;
    state.uploads={}; state.polls=0; state.submitted=0; delete state.arguments;
    return send(200,{ok:true});
  }
  if (path==='/state') return send(200,state);
  if (path.startsWith('/storage-object/') || path==='/output.mp4') {
    if (req.headers.authorization) return send(400,{detail:'credential leak'});
    if (path==='/output.mp4') {
      res.writeHead(200,{'Content-Type':'video/mp4'});
      return res.end(Buffer.from(state.mode==='empty'?'':state.media,'base64'));
    }
    const id=path.split('/').pop(), item=state.uploads[id];
    if (!item || req.method!=='PUT' || req.headers['content-type']!==item.content_type)
      return send(400,{detail:'invalid upload'});
    item.bytes=raw.length; return send(200,{});
  }
  if (req.headers.authorization!=='Key test-only' || state.mode==='unauthorized')
    return send(401,{detail:'invalid API key'});
  if (path==='/storage/upload/initiate') {
    if (!body.file_name || !body.content_type || !req.url.includes('storage_type=gcs'))
      return send(422,{detail:'invalid upload arguments'});
    const id=String(Object.keys(state.uploads).length+1); state.uploads[id]=body;
    return send(200,{upload_url:`${origin}/storage-object/${id}`,file_url:`${origin}/asset/${id}`});
  }
  if (path==='/fal-ai/latentsync' && req.method==='POST') {
    const ready = Object.values(state.uploads).every(x=>x.bytes>0);
    if (!ready || !body.video_url || !body.audio_url || body.loop_mode || body.enable_safety_checker!==true)
      return send(422,{detail:'invalid model arguments'});
    state.submitted++; state.arguments=body;
    return send(200,{request_id:'request-1', status_url:state.mode==='foreign_url' ? 'https://foreign.invalid/steal' :
                     `${origin}/fal-ai/latentsync/requests/request-1/status`,
                     response_url:`${origin}/fal-ai/latentsync/requests/request-1`});
  }
  if (path==='/fal-ai/latentsync/requests/request-1/status') {
    state.polls++;
    if (state.mode==='failed') return send(200,{status:'COMPLETED',error:'no face',error_type:'validation'});
    if (state.mode==='unknown') return send(200,{status:'unexpected'});
    if (state.mode==='pending' || state.polls===1) return send(200,{status:'IN_QUEUE'});
    if (state.polls===2) return send(200,{status:'IN_PROGRESS'});
    return send(200,{status:'COMPLETED'});
  }
  if (path==='/fal-ai/latentsync/requests/request-1') {
    if (state.mode==='result_error') return send(422,{detail:'model validation failed'});
    if (state.mode==='missing_video') return send(200,{});
    return send(200,{video:{url:`${origin}/output.mp4`,content_type:'video/mp4'}});
  }
  return send(501,{detail:'endpoint not modeled'});
}).listen(process.env.PORT);
