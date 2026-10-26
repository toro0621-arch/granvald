// ステージを自動で最後まで遊ぶテスト（味方も簡単なAIで動かす）。
// 使い方：python3 -m http.server 8765 を立ててから node tools/test/autoplay.js <ステージ> <回数>
// 会話はすぐ閉じて行を記録し、時計を早送りする。勝敗・ターン数・流れた会話・撃墜された味方・例外を出す
const {chromium}=require('playwright');
const [stage='e2',runs='5']=process.argv.slice(2);
(async()=>{
  const b=await chromium.launch();
  const sum={win:0,lose:0,turns:[],errs:0};
  for(let r=0;r<+runs;r++){
    const p=await b.newPage({viewport:{width:400,height:800}});
    const errs=[];p.on('pageerror',e=>errs.push(e.message));
    await p.addInitScript(()=>{const st=window.setTimeout;window.setTimeout=(f,d,...a)=>st(f,Math.min(5,(d||0)/40),...a);
      try{localStorage.setItem('granvald-settings',JSON.stringify({anim:false,sound:false,bgmVol:0,manualDef:false}))}catch(e){}});
    await p.goto('http://localhost:8765/index.html');await p.waitForTimeout(500);
    const res=await p.evaluate(async(stage)=>{
      const log=[];window.dialog=async(lines)=>{for(const l of lines)log.push(l.who+'「'+l.text.slice(0,18)+'」');};
      window.result=(win)=>{window.__res=win};
      $('title').hidden=true;
      await startGame(stage);
      const foes=()=>alive('foe');
      // 味方のAI：攻撃できるなら一番よい攻撃（撃墜・ボス優先）、できなければボスへ近づく。HPの減ったレオは整備車両へ下がる。整備車両は隣の傷んだ味方を修理
      async function allyAct(u){
        if(over)return;
        const r=computeReach(u);let best=null;
        if(u.repair){for(const t of r.tiles){for(const a of alive('ally'))if(a!==u&&a.hp<a.maxHp*.6&&Math.abs(t.x-a.x)+Math.abs(t.y-a.y)===1){const sc=a.maxHp-a.hp+(a.key===ST.leader||(ST.protect||[]).includes(a.key)?3000:0);if(!best||sc>best.sc)best={sc,t,a,rep:1}}}}
        const weak=(ST.protect||[]).includes(u.key)&&(u.hp<u.maxHp*.7||dist(u,alive('ally').find(a=>a.key===ST.leader))>2);
        if(!best&&!weak)for(const t of r.tiles){const ox=u.x,oy=u.y;u.x=t.x;u.y=t.y;
          for(const e of foes()){const d=dist(u,e);for(const w of u.weapons){if(usable(u,w)||!inRange(w,d))continue;
            const hr=hitRate(u,e,w),dm=baseDmg(u,e,w);let sc=dm*hr/100;if(dm>=e.hp)sc+=3000*hr/100;if(e.boss)sc*=1.3;
            const cw=bestWeapon(e,u,d);if(cw)sc-=baseDmg(e,u,cw)*hitRate(e,u,cw)/100*.5;sc+=terOf(t.x,t.y).e*5;
            if(!best||sc>best.sc)best={sc,t,e,w}}}
          u.x=ox;u.y=oy}
        if(best){await animateMove(u,r.path(best.t.x,best.t.y));
          if(best.rep){doRepair(u,best.a);return}
          await combat(u,best.e,best.w,{mode:'counter'})}
        else{const goal=weak?(alive('ally').find(a=>a.repair)||alive('ally').find(a=>a.key===ST.leader)):(foes().find(e=>e.boss)||foes()[0]);
          if(goal){let bt=null,bd=1e9;for(const t of r.tiles){const d=Math.abs(t.x-goal.x)+Math.abs(t.y-goal.y);if(d<bd&&!(t.x===u.x&&t.y===u.y&&weak)){bd=d;bt=t}}if(bt)await animateMove(u,r.path(bt.x,bt.y))}}
        if(!over&&!u.acted)finishUnit(u);
      }
      let guard=0;
      while(!over&&guard++<40){
        while(busy)await new Promise(r=>setTimeout(r,5));
        for(const u of alive('ally')){if(over)break;if(u.acted)continue;sel=u;await allyAct(u);while(busy&&!over)await new Promise(r=>setTimeout(r,5))}
        if(over)break;
        if(phase==='player')await endPlayerPhase();
      }
      while(window.__res===undefined&&guard++<400)await new Promise(r=>setTimeout(r,20));
      return{win:window.__res,turn,flags:Object.keys(flags),lostAllies:units.filter(u=>u.team==='ally'&&u.dead).map(u=>u.pilot.name),
        bossHp:units.find(u=>u.boss).hp,log:log.length,arrived:units.filter(u=>u.arrive).map(u=>u.off?'未着':'着')};
    },stage);
    if(res.win)sum.win++;else sum.lose++;sum.turns.push(res.turn);sum.errs+=errs.length;
    console.log(`#${r+1}`,res.win?'勝ち':'負け','TURN',res.turn,'会話',res.flags.join(','),'撃墜された味方',res.lostAllies.join('・')||'なし','増援',res.arrived.join(','),errs.slice(0,3));
    await p.close();
  }
  console.log('合計',JSON.stringify(sum));
  await b.close();
})();
