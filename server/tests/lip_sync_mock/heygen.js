// Official HeyGen v3 direct uploads + standalone lipsync contract; no real model.
const http=require('http');
const state={mode:'success',media:'',assets:{},polls:0,submitted:0};
http.createServer(async(req,res)=>{
  const chunks=[];for await(const chunk of req)chunks.push(chunk);
  const raw=Buffer.concat(chunks),path=req.url.split('?')[0];
  const origin=`http://${req.headers.host}/heygen`;
  const send=(code,value)=>{res.writeHead(code,{'Content-Type':'application/json'});res.end(JSON.stringify(value));};
  let body={};
  try{if((req.headers['content-type']||'').includes('json')&&raw.length)body=JSON.parse(raw);}
  catch{return send(400,{message:'invalid JSON'});}
  if(path==='/control'){
    state.mode=body.mode||'success';state.media=body.media||state.media;
    state.assets={};state.polls=0;state.submitted=0;delete state.arguments;
    return send(200,{data:{ok:true}});
  }
  if(path==='/state')return send(200,state);
  if(path.startsWith('/storage/')||path==='/output.mp4'){
    if(req.headers['x-api-key'])return send(400,{message:'credential leak'});
    if(path==='/output.mp4'){
      res.writeHead(200,{'Content-Type':'video/mp4'});
      return res.end(Buffer.from(state.mode==='empty'?'':state.media,'base64'));
    }
    const id=path.split('/').pop(),asset=state.assets[id];
    if(!asset||req.method!=='PUT'||raw.length!==asset.size_bytes||
       req.headers['content-type']!==asset.content_type||req.headers['x-signed-test']!=='verbatim')
      return send(400,{message:'signed upload headers or size mismatch'});
    asset.uploaded=true;return send(200,{});
  }
  if(req.headers['x-api-key']!=='test-only'||state.mode==='unauthorized')return send(401,{error:{code:'unauthorized',message:'invalid key'}});
  if(path==='/v3/assets/direct-uploads'){
    if(!body.filename||!body.content_type||!body.size_bytes)return send(422,{message:'invalid asset'});
    const id=String(Object.keys(state.assets).length+1);state.assets[id]=body;
    return send(200,{data:{asset_id:id,upload_url:`${origin}/storage/${id}`,
      upload_headers:state.mode==='missing_headers'?null:{'Content-Type':body.content_type,'X-Signed-Test':'verbatim'},
      max_bytes:state.mode==='size_limit'?1:200*1024*1024,expires_in_seconds:3600}});
  }
  const match=path.match(/^\/v3\/assets\/([^/]+)\/complete$/);
  if(match){
    const asset=state.assets[match[1]];
    if(!asset?.uploaded)return send(422,{message:'upload not finished'});
    if(state.mode==='complete_error')return send(422,{message:'invalid uploaded media'});
    asset.completed=true;return send(200,{data:{asset_id:match[1],status:'processing'}});
  }
  if(path==='/v3/lipsyncs'&&req.method==='POST'){
    if(body.video?.type!=='asset_id'||body.audio?.type!=='asset_id'||
       !state.assets[body.video.asset_id]?.completed||!state.assets[body.audio.asset_id]?.completed||
       body.enable_dynamic_duration!==false||body.enable_caption!==false||body.disable_music_track!==true||
       body.enable_speech_enhancement!==false||body.fps_mode!=='passthrough'||
       !['precision','speed'].includes(body.mode))return send(422,{message:'invalid lipsync arguments'});
    state.arguments=body;state.submitted++;
    return send(200,{data:state.mode==='missing_id'?{}:{lipsync_id:'ls-1'}});
  }
  if(path==='/v3/lipsyncs/ls-1'){
    state.polls++;
    if(state.mode==='failed')return send(200,{data:{status:'failed',failure_message:'face not found'}});
    if(state.mode==='unknown')return send(200,{data:{status:'unexpected'}});
    if(state.mode==='pending'||state.polls===1)return send(200,{data:{status:'pending'}});
    if(state.polls===2)return send(200,{data:{status:'running'}});
    return send(200,{data:{status:'completed',video_url:state.mode==='missing_url'?null:`${origin}/output.mp4`}});
  }
  return send(501,{message:'endpoint not modeled'});
}).listen(process.env.PORT);
