import * as d3 from "d3-geo"; import fs from "fs";
const ring=[]; for(let lon=-12;lon<=140;lon+=1) ring.push([lon,20]); for(let lat=20;lat<=76;lat+=1) ring.push([140,lat]); for(let lon=140;lon>=-12;lon-=1) ring.push([lon,76]); for(let lat=76;lat>=20;lat-=1) ring.push([-12,lat]);
ring.reverse(); const win={type:"Polygon",coordinates:[ring]};
const proj0=d3.geoConicConformal().parallels([35,65]).rotate([-50,0]).center([0,52]).fitExtent([[20,20],[1580,880]],win);
const geo=JSON.parse(fs.readFileSync(new URL("./loon-geo.json", import.meta.url)));  // the corridor map the explainers were drawn from
const k=proj0([30.5234,50.4501]); const dx=geo.cities.Kyiv[0]-k[0], dy=geo.cities.Kyiv[1]-k[1];
const P=(lat,lon)=>{const p=proj0([lon,lat]); return [+(p[0]+dx).toFixed(1), +(p[1]+dy).toFixed(1)];};
// verify translation-only on two more stored cities
for(const [n,ll] of [["Warsaw",[52.2297,21.0122]],["Moscow",[55.7558,37.6173]],["Odesa",[46.4825,30.7233]]]){const p=P(ll[0],ll[1]); const s=geo.cities[n]; const e=Math.hypot(p[0]-s[0],p[1]-s[1]); console.log(n,'err px',e.toFixed(2)); if(e>1.5) throw new Error('projection mismatch '+n);}
const csv=f=>{const [h,...r]=fs.readFileSync(f,'utf8').trim().split('\n'); const H=h.split(','); return r.map(l=>{const v=l.split(','); return Object.fromEntries(H.map((k,i)=>[k,v[i]]));});};
const R=new URL("../../results/", import.meta.url).pathname;
// hourly tracks of the 120 slow-controller flights
const tr={}; for(const r of csv(R+"slow_tracks.csv")){ (tr[r.flight] ||= {flight:r.flight, site:r.site, start:r.start, month:+r.start.slice(5,7), pts:[]}).pts.push([...P(+r.lat,+r.lon), +r.hours]); }
const tracks=Object.values(tr).map(t=>({...t, pts:t.pts.sort((a,b)=>a[2]-b[2]).map(p=>[p[0],p[1]])}));
// all 360 drift flights: dwell, release, recovery, envelope landing
const sites=JSON.parse(fs.readFileSync("sites.json"));
const LAUNCH={Lisbon:[38.7,-9.1],Brest:[48.4,-4.5],Dublin:[53.3,-6.3],Vienna:[48.2,16.4],Bucharest:[44.4,26.1]};
const drift=csv(R+"drift_2025.csv").map(r=>({site:r.site, start:r.start, month:+r.month, ctl:r.controller, dwell_d:+(+r.dwell_h/24).toFixed(2), end:r.end,
  rel: r.release_lat? P(+r.release_lat,+r.release_lon):null, rec:r.recovery||null, recovered:r.recovered==='True', env: r.env_a_lat? P(+r.env_a_lat,+r.env_a_lon):null}));
const monthDwell={}; for(const r of drift){ (monthDwell[r.ctl] ||= Array.from({length:12},()=>[])) [r.month-1].push(r.dwell_d); }
for(const c in monthDwell) monthDwell[c]=monthDwell[c].map(a=>+(a.reduce((x,y)=>x+y,0)/a.length).toFixed(2));
// region outline 32.5–65N, 15W–50E
const reg=[]; for(let lon=-15;lon<=50;lon+=1) reg.push(P(32.5,lon)); for(let lat=32.5;lat<=65;lat+=0.5) reg.push(P(lat,50)); for(let lon=50;lon>=-15;lon-=1) reg.push(P(65,lon)); for(let lat=65;lat>=32.5;lat-=0.5) reg.push(P(lat,-15));
const out={W:1600,H:900, land:geo.land, russia:geo.russia, ukraine:geo.ukraine, borders:geo.borders,
  launch:Object.fromEntries(Object.entries(LAUNCH).map(([n,[la,lo]])=>[n,P(la,lo)])),
  sites:Object.fromEntries(Object.entries(sites).map(([n,[la,lo]])=>[n,P(la,lo)])),
  region:reg, tracks, drift, monthDwell};
fs.writeFileSync("data.json", JSON.stringify(out));
console.log('tracks',tracks.length,'drift',drift.length,'sites',Object.keys(out.sites).length,'bytes',fs.statSync('data.json').size, 'monthDwell slow', monthDwell.slow);
const bb=tracks.flatMap(t=>t.pts); console.log('track bbox x',Math.min(...bb.map(p=>p[0])).toFixed(0),Math.max(...bb.map(p=>p[0])).toFixed(0),'y',Math.min(...bb.map(p=>p[1])).toFixed(0),Math.max(...bb.map(p=>p[1])).toFixed(0));
