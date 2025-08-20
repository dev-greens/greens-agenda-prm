(function(){
  function paintIcons(theme){
    var sun = document.getElementById('iconSun');
    var moon = document.getElementById('iconMoon');
    if(sun)  sun.style.opacity  = (theme==='light') ? '1' : '.35';
    if(moon) moon.style.opacity = (theme==='light') ? '.35' : '1';
  }
  function applyTheme(theme){
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-bs-theme', theme);
    localStorage.setItem('greens-theme', theme);
    var sw=document.getElementById('themeSwitch');
    if(sw) sw.checked = (theme==='light');
    paintIcons(theme);
    document.dispatchEvent(new CustomEvent('theme:changed', {detail:{theme}}));
  }
  document.addEventListener('DOMContentLoaded', function(){
    var saved=localStorage.getItem('greens-theme') || 'dark';
    applyTheme(saved);
    var sw=document.getElementById('themeSwitch');
    if(sw) sw.addEventListener('change', function(){ applyTheme(this.checked ? 'light' : 'dark'); });
  });
})();