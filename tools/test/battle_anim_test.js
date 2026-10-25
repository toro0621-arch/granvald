// 戦闘アニメの総当たりテスト
// 使い方: node battledbg.js <出力フォルダ> <周回 1-5>
// ゲームの時計（performance.now と requestAnimationFrame）を早送りにして、全ユニット×全武装×全パターンを流す。
// 自動チェック：例外、描画関数への NaN/Infinity、アニメが終わらない、終わったあと画面が閉じない、
//   一度も何も描かれない、HP表示の値が範囲外、表示した顔・名前が攻撃側と違う
// 目で見る用：各パターンのコマ（構え・当たる瞬間・その後）を画像に保存
const {chromium}=require('playwright');const fs=require('fs');
const OUT=process.argv[2],ROUND=+process.argv[3]||1;
const VP={1:[400,800],2:[320,568],3:[844,390],4:[390,844],5:[400,800]}[ROUND];
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:VP[0],height:VP[1]}});
const errs=[];p.on('pageerror',e=>errs.push('JS: '+e.message));
await p.addInitScript(()=>{
  // 仮想時計：rAF は 16ms ずつ進める。描画関数に NaN が来たら記録
  window.VT=0;window.BAD=[];const realNow=performance.now.bind(performance);
  window.FAST=false;
  performance.now=()=>window.FAST?window.VT:realNow();
  const rq=window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame=cb=>window.FAST?setTimeout(()=>{window.VT+=16;cb(window.VT)},0):rq(cb);
  const P=CanvasRenderingContext2D.prototype;
  for(const m of ['drawImage','fillRect','strokeRect','arc','ellipse','moveTo','lineTo','translate','scale','rotate','fillText','strokeText','createLinearGradient']){
    const o=P[m];P[m]=function(...a){for(const v of a)if(typeof v==='number'&&!isFinite(v)){window.BAD.push(m+'('+a.map(x=>typeof x==='number'?Math.round(x*100)/100:typeof x).join(',')+')');break}return o.apply(this,a)}}
});
await p.goto('http://localhost:8765/index.html');await p.waitForTimeout(1500);
const res=await p.evaluate(async({ROUND})=>{
  document.getElementById('title').hidden=true;settings.sound=false;
  const PAT=['hit','miss','crit','kill','counter','counterKill'];
  const TERR=['P','F','M','W','C','B','E'];
  const jobs=[];
  for(const st of ['e1','s1']){loadStage(st);setup();
    const seen=new Set();
    for(const u of units){if(seen.has(u.key))continue;seen.add(u.key);
      u.weapons.forEach((w,wi)=>{for(const pat of PAT)jobs.push({st,key:u.key,wi,wname:w.name,pat})})}}
  const log=[],shots=[];let n=0;
  for(const j of jobs){
    loadStage(j.st);setup();over=false;
    const A=units.find(u=>u.key===j.key),foes=units.filter(u=>u.team!==A.team);
    // 相手：周回ごとに変える（空中・地上・ボスなどいろいろ当たるように）
    const D=foes[(n+ROUND)%foes.length];
    const w=A.weapons[j.wi];
    // 届く距離に置く（反撃パターンは相手の武器も届く距離）
    const dist_=Math.max(w.min,1);
    // 地形：周回4は地形を順番に変える
    if(ROUND===4){const T=TERR[n%TERR.length];for(let y=0;y<ROWS;y++)for(let x=0;x<COLS;x++)if(MAP[y][x]===T){D.x=x;D.y=y}}
    A.will=150;A.en=A.maxEn;w.ammo=w.maxAmmo;
    const mk=(att,def,wp,hit,crit,kill)=>{const dmg=!hit?0:kill?def.hp:Math.max(10,Math.round(def.maxHp*(crit?.4:.25)));
      const r={att,def,w:wp,hit,dmg,crit,hpFrom:def.hp,hpTo:def.hp-dmg,kill:!!kill,line:att.lines[0]};def.hp-=dmg;return r};
    const hp0={a:A.hp,d:D.hp};
    let strikes=[];
    if(j.pat==='hit')strikes=[mk(A,D,w,1,0,0)];
    if(j.pat==='miss')strikes=[mk(A,D,w,0,0,0)];
    if(j.pat==='crit')strikes=[mk(A,D,w,1,1,0)];
    if(j.pat==='kill')strikes=[mk(A,D,w,1,0,1)];
    if(j.pat==='counter'){const cw=D.weapons[0];strikes=[mk(A,D,w,1,0,0),mk(D,A,cw,1,0,0)]}
    if(j.pat==='counterKill'){const cw=D.weapons[D.weapons.length-1];strikes=[mk(A,D,w,0,0,0),mk(D,A,cw,1,1,1)]}
    A.hp=hp0.a;D.hp=hp0.d;
    window.BAD=[];FAST=true;VT=0;
    const total=strikes.reduce((s,x)=>s+(isSpecial(x.w)?950:0)+1900,0)+500;
    const want=[];for(const [si,sx] of strikes.entries()){const base=strikes.slice(0,si).reduce((s,x)=>s+(isSpecial(x.w)?950:0)+1900,0),cut=isSpecial(sx.w)?950:0;
      if(cut)want.push(base+cut*.5);want.push(base+cut+1900*.35,base+cut+1900*(sx.w.type==='格'?.53:.6),base+cut+1900*.85)}
    const frames=[];let drawn=false,faceBad=null;
    const skipAt=ROUND===5?Math.floor(Math.random()*total):null;
    const pr=playBattle(A,D,strikes);
    let finished=false;pr.then(()=>finished=true);
    const ctx=document.getElementById('bcv').getContext('2d');
    while(!finished&&VT<total+3000){
      await new Promise(r=>setTimeout(r,0));
      if(want.length&&VT>=want[0]){want.shift();frames.push(document.getElementById('bcv').toDataURL('image/jpeg',.6))}
      if(!drawn){const px=ctx.getImageData(Math.floor(bcv.width/2),Math.floor(bcv.height*.8),1,1).data;if(px[3]>0)drawn=true}
      const who=document.getElementById('bWho').textContent;if(who&&!strikes.some(s=>s.att.pilot.name===who))faceBad=who;
      if(skipAt!==null&&VT>=skipAt&&!finished){document.getElementById('battle').click()}
    }
    FAST=false;
    const hidden=document.getElementById('battle').hidden;
    const prob=[];
    if(!finished)prob.push('終わらない');
    if(!hidden)prob.push('画面が閉じない');
    if(!drawn)prob.push('何も描かれない');
    if(BAD.length)prob.push('NaN: '+[...new Set(BAD)].slice(0,3).join(' / '));
    if(faceBad)prob.push('違う名前: '+faceBad);
    log.push({n,unit:A.name,key:j.key,w:j.wname,fx:w.fx,pat:j.pat,vs:D.name,ter:TER[MAP[D.y][D.x]]?.n,dur:VT,prob});
    if(ROUND!==5||n%3===0)shots.push({n,label:`${A.name}／${j.wname}／${j.pat}／vs ${D.name}`,frames});
    n++;
  }
  return {log,shots};
},{ROUND});
fs.writeFileSync(`${OUT}/bd_r${ROUND}.json`,JSON.stringify(res.log));
// コマを保存
fs.mkdirSync(`${OUT}/bd_r${ROUND}`,{recursive:true});
for(const s of res.shots)s.frames.forEach((d,i)=>fs.writeFileSync(`${OUT}/bd_r${ROUND}/${String(s.n).padStart(3,'0')}_${i}.jpg`,Buffer.from(d.split(',')[1],'base64')));
fs.writeFileSync(`${OUT}/bd_r${ROUND}/labels.json`,JSON.stringify(res.shots.map(s=>[s.n,s.label])));
const bad=res.log.filter(l=>l.prob.length);
console.log(`周回${ROUND}（画面 ${VP[0]}×${VP[1]}）：${res.log.length}パターン、問題 ${bad.length}件`);
for(const l of bad.slice(0,30))console.log(' ',l.unit,l.w,l.pat,'vs',l.vs,'→',l.prob.join('、'));
console.log(errs.join('\n')||'例外なし');await b.close()})();
