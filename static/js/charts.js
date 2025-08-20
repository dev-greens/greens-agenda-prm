(function(){
  if (!window.Chart) return;
  function css(v){ return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
  function apply(){
    Chart.defaults.color = css('--text') || '#0f172a';
    Chart.defaults.borderColor = css('--border') || '#e5e7eb';
  }
  apply();
  document.addEventListener('theme:changed', apply);
  window.chartConfig = function(type, labels, data, label){
    return { type, data: { labels: labels||[], datasets:[{ label:label||'', data:data||[], tension:0.35, fill:false, borderWidth:2, pointRadius:0 }]},
      options:{ responsive:true, plugins:{legend:{display:false}}, scales:{x:{grid:{color:Chart.defaults.borderColor,drawBorder:false}}, y:{grid:{color:Chart.defaults.borderColor,drawBorder:false}} } } };
  };
})();
