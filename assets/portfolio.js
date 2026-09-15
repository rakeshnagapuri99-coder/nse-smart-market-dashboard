let portfolioData=null, builtPortfolio=[];
function initializePortfolioBuilder(data){
 portfolioData=data;
 const root=document.getElementById("portfolioBuilder");
 root.innerHTML=`<div class="portfolio-controls">
 <label>Portfolio Amount<input id="pfAmount" type="number" value="100000" min="1000"></label>
 <label>Number of Stocks<input id="pfCount" type="number" value="10" min="1" max="30"></label>
 <label>Minimum Score<input id="pfScore" type="number" value="55" min="0" max="100"></label>
 <button class="btn" onclick="buildPortfolio()">Build Portfolio</button>
 <button class="btn" onclick="exportPortfolio()">Export CSV</button></div>
 <div id="pfOutput"></div>`;
}
function buildPortfolio(){
 const amount=Number(document.getElementById("pfAmount").value)||100000;
 const count=Number(document.getElementById("pfCount").value)||10;
 const minScore=Number(document.getElementById("pfScore").value)||55;
 let rows=(portfolioData.stocks||[]).filter(x=>Number(x.Overall_Score)>=minScore&&Number(x.Close)>0&&Number(x.Stop_Loss)>0&&Number(x.Target_1)>Number(x.Entry_Price)&&x.Trade_Status==="Actionable Watch");
 rows.sort((a,b)=>Number(b.Overall_Score)-Number(a.Overall_Score));
 const used={}; rows=rows.filter(x=>{const s=x.Primary_Sector||"Unknown";if((used[s]||0)>=2)return false;used[s]=(used[s]||0)+1;return true}).slice(0,count);
 const allocation=rows.length?amount/rows.length:0;
 builtPortfolio=rows.map(x=>{
   const qty=Math.floor(allocation/Number(x.Close));
   const invested=qty*Number(x.Close);
   const risk=qty*(Number(x.Close)-Number(x.Stop_Loss));
   const t1=qty*(Number(x.Target_1)-Number(x.Close));
   return {...x,Quantity:qty,Allocation:invested,Risk_Amount:risk,Target_1_Profit:t1};
 });
 const totalRisk=builtPortfolio.reduce((a,x)=>a+x.Risk_Amount,0);
 const totalT1=builtPortfolio.reduce((a,x)=>a+x.Target_1_Profit,0);
 document.getElementById("pfOutput").innerHTML=`<div class="portfolio-summary">
 <div class="summary"><b>Stocks</b><br>${builtPortfolio.length}</div>
 <div class="summary"><b>Invested</b><br>₹${totalInvested().toLocaleString("en-IN")}</div>
 <div class="summary"><b>Max Planned Risk</b><br>₹${totalRisk.toLocaleString("en-IN")}</div>
 <div class="summary"><b>T1 Scenario Profit</b><br>₹${totalT1.toLocaleString("en-IN")}</div></div>
 <div class="table-wrap"><table><thead><tr><th>Stock</th><th>Score</th><th>Qty</th><th>Entry</th><th>SL</th><th>T1</th><th>Allocation</th><th>Risk</th></tr></thead><tbody>
 ${builtPortfolio.map((x,i)=>`<tr class="stock-row" onclick="openPortfolioStock(${i})"><td>${x.Symbol}</td><td>${Number(x.Overall_Score).toFixed(1)}</td><td>${x.Quantity}</td><td>${Number(x.Entry_Price).toFixed(2)}</td><td>${Number(x.Stop_Loss).toFixed(2)}</td><td>${Number(x.Target_1).toFixed(2)}</td><td>₹${x.Allocation.toLocaleString("en-IN")}</td><td>₹${x.Risk_Amount.toFixed(0)}</td></tr>`).join("")}</tbody></table></div>`;
}
function totalInvested(){return builtPortfolio.reduce((a,x)=>a+x.Allocation,0)}
function openPortfolioStock(i){if(window.openStock){const x=builtPortfolio[i];const list=window.currentRows;window.currentRows=[x];window.openStock(0);window.currentRows=list}}
function exportPortfolio(){
 if(!builtPortfolio.length){buildPortfolio();if(!builtPortfolio.length)return}
 const headers=["Symbol","Overall_Score","Setup","Quantity","Close","Entry_Price","Stop_Loss","Target_1","Target_2","Risk_Reward","Allocation","Risk_Amount","Target_1_Profit"];
 const csv=[headers.join(","),...builtPortfolio.map(x=>headers.map(h=>JSON.stringify(x[h]??"")).join(","))].join("\n");
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));a.download="portfolio_builder.csv";a.click();
}
window.initializePortfolioBuilder=initializePortfolioBuilder;window.buildPortfolio=buildPortfolio;window.exportPortfolio=exportPortfolio;window.openPortfolioStock=openPortfolioStock;
