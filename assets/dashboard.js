let dashboardData=null, currentList="next_day", currentRows=[];

const $=id=>document.getElementById(id);
const num=(v,d="—")=>{let n=Number(v);return Number.isFinite(n)?n.toFixed(2):d};
const esc=s=>String(s??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));

async function loadDashboard(){
 try{
  const r=await fetch("output/dashboard_data.json?v="+Date.now(),{cache:"no-store"});
  if(!r.ok) throw new Error("dashboard_data.json unavailable");
  dashboardData=await r.json();
  renderMarket(); renderBreadth(); renderSectors(); renderTabs(); renderSetups(); renderWatchlist();
  if(window.initializePortfolioBuilder) window.initializePortfolioBuilder(dashboardData);
 }catch(e){
  $("marketRegime").innerHTML=`<div class="card"><b>Dashboard data unavailable</b><div class="muted">${esc(e.message)}</div></div>`;
 }
}
function renderMarket(){
 const m=dashboardData.market_regime||dashboardData.market||{};
 const n=m.nifty||{}, b=m.bank_nifty||{};
 $("lastUpdated").textContent="Updated: "+(dashboardData.generated_at||"");
 $("marketRegime").innerHTML=[
  ["Regime",m.market_regime],["Market Score",num(m.market_score)],
  ["NIFTY 50",num(n.price)],["NIFTY Day",num(n.daily_return_pct)+"%"],
  ["BANK NIFTY",num(b.price)],["VIX",num(m.vix)]
 ].map(x=>`<div class="card"><div class="label">${x[0]}</div><div class="value">${x[1]??"—"}</div></div>`).join("");
 $("marketEnvironmentGrid").innerHTML=[
  ["Equity",m.equity_environment],["Swing",m.swing_environment],
  ["Breakout",m.breakout_environment],["Intraday",m.intraday_environment],["Options",m.options_environment]
 ].map(x=>`<div class="pill"><b>${x[0]}</b><br>${x[1]||"—"}</div>`).join("");
 $("marketAnalysisGrid").innerHTML=[
  ["Support",num(m.support)],["Resistance",num(m.resistance)],["Pivot",num(m.pivot)],
  ["Bullish Trigger",num(m.bullish_trigger)],["Bearish Trigger",num(m.bearish_trigger)]
 ].map(x=>`<div class="analysis-item"><b>${x[0]}</b><br>${x[1]}</div>`).join("");
 $("marketScenario").textContent="Scenario: "+(m.market_scenario||"Confirmation required");
}
function renderBreadth(){
 const b=dashboardData.market_breadth||dashboardData.breadth||{};
 $("breadthCards").innerHTML=[
  ["Stocks",b.stocks_analyzed],["Above 20 DMA",b.above_20_dma],["Above 50 DMA",b.above_50_dma],
  ["Above 200 DMA",b.above_200_dma],["52W Highs",b["52w_highs"]],["52W Lows",b["52w_lows"]],
  ["Breadth Score",b.breadth_score],["Regime",b.breadth_regime]
 ].map(x=>`<div class="card"><div class="label">${x[0]}</div><div class="value">${x[1]??"—"}</div></div>`).join("");
}
function renderSectors(){
 const s=dashboardData.sector_analysis||dashboardData.sectors||[];
 $("sectorTable").innerHTML=s.slice(0,20).map(x=>`<tr><td>${esc(x.Sector)}</td><td>${num(x.Sector_Score)}</td><td>${num(x.Return_20D_Pct)}%</td><td>${num(x.Return_60D_Pct)}%</td></tr>`).join("");
}
function renderTabs(){
 const names=Object.keys(dashboardData.watchlists||{});
 $("watchTabs").innerHTML=names.map((n,i)=>`<button class="tab ${i===0?"active":""}" data-list="${n}">${n.replaceAll("_"," ")} (${dashboardData.watchlist_counts?.[n]??0})</button>`).join("");
 document.querySelectorAll(".tab").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));b.classList.add("active");currentList=b.dataset.list;renderWatchlist()});
}
function renderSetups(){
 const all=dashboardData.stocks||[], opts=[...new Set(all.map(x=>x.Setup).filter(Boolean))];
 $("setupFilter").innerHTML='<option value="">All setups</option>'+opts.map(x=>`<option>${esc(x)}</option>`).join("");
 $("stockSearch").oninput=renderWatchlist;$("setupFilter").onchange=renderWatchlist;
}
function renderWatchlist(){
 let rows=(dashboardData.watchlists?.[currentList]||[]).slice();
 const q=($("stockSearch")?.value||"").toLowerCase(), setup=$("setupFilter")?.value||"";
 rows=rows.filter(x=>(!q||String(x.Symbol).toLowerCase().includes(q)||String(x.Company_Name||"").toLowerCase().includes(q))&&(!setup||x.Setup===setup));
 currentRows=rows;$("watchlistTitle").textContent=currentList.replaceAll("_"," ").toUpperCase();
 $("watchlistCount").textContent=`${rows.length} shown`;
 $("stockTable").innerHTML=rows.slice(0,100).map((x,i)=>`<tr class="stock-row" onclick="openStock(${i})"><td><b>${esc(x.Symbol)}</b><br><small>${esc(x.Company_Name||"")}</small></td><td>${num(x.Overall_Score)}</td><td>${esc(x.Setup)}</td><td>${num(x.Close)}</td><td>${num(x.Entry_Price)}</td><td>${num(x.Stop_Loss)}</td><td>${num(x.Target_1)}</td><td>${num(x.Target_2)}</td><td>${num(x.Risk_Reward)}</td></tr>`).join("");
}
window.openStock=i=>{
 const x=currentRows[i]; if(!x)return;
 $("stockDetail").innerHTML=`<h2>${esc(x.Symbol)} — ${esc(x.Company_Name||"")}</h2>
 <p><b>Setup:</b> ${esc(x.Setup)} &nbsp; <b>Score:</b> ${num(x.Overall_Score)} &nbsp; <b>Status:</b> ${esc(x.Trade_Status)}</p>
 <div class="trade">${[
 ["Last Close",x.Close],["SMA 200",x.SMA200],["RSI",x.RSI14],["ATR",x.ATR14],
 ["Support",x.Support],["Resistance",x.Resistance],["52W High",x["52W_High"]],["Volume Ratio",x.Volume_Ratio],
 ["Entry",x.Entry_Price],["Stop Loss",x.Stop_Loss],["Target 1",x.Target_1],["Target 2",x.Target_2],["Risk/Reward",x.Risk_Reward]
 ].map(a=>`<div><small>${a[0]}</small><br><b>${num(a[1])}</b></div>`).join("")}</div>
 <h3>Decision Context</h3><p>${esc(x.Setup)}. Technical score ${num(x.Technical_Score)}, fundamental score ${num(x.Fundamental_Score)}. Verify current market price, liquidity and confirmation in your broker before acting.</p>`;
 $("stockModal").classList.add("open");
};
$("stockModalClose").onclick=()=>$("stockModal").classList.remove("open");
$("stockModal").onclick=e=>{if(e.target.id==="stockModal")$("stockModal").classList.remove("open")};
loadDashboard();
