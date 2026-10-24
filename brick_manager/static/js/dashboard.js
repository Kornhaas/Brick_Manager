document.addEventListener('DOMContentLoaded', () => {
  const readJson = id => JSON.parse(document.getElementById(id)?.textContent || '[]');
  const history = readJson('historyData');
  const statuses = readJson('statusData');
  const statusContainer = document.getElementById('statusBars');
  const statusMax = Math.max(...statuses.map(item => item.value), 1);
  statuses.forEach(item => {
    const row = document.createElement('div'); row.className = 'status-row';
    const label = document.createElement('span'); label.textContent = item.label;
    const track = document.createElement('span'); track.className = 'status-track';
    const bar = document.createElement('i'); bar.style.width = `${item.value / statusMax * 100}%`; track.appendChild(bar);
    const count = document.createElement('span'); count.className = 'status-count'; count.textContent = item.value.toLocaleString();
    row.append(label, track, count); statusContainer?.appendChild(row);
  });
  const svg = document.getElementById('collectionTrend');
  if (!svg || !history.length) return;
  const ns = 'http://www.w3.org/2000/svg', width = 900, height = 300, padding = 34;
  const create = (name, attrs) => { const node = document.createElementNS(ns, name); Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value)); svg.appendChild(node); return node; };
  for (let line = 0; line < 5; line += 1) { const y = padding + (height - padding * 2) / 4 * line; create('line', {x1: padding, y1: y, x2: width - padding, y2: y, stroke: '#e8ecf4', 'stroke-width': 1}); }
  [{key:'owned',color:'#3478f6'},{key:'missing',color:'#f06462'},{key:'sets',color:'#7657e8'}].forEach(({key,color}) => {
    const values = history.map(item => Number(item[key]) || 0), min = Math.min(...values), max = Math.max(...values), range = max - min || 1;
    const points = values.map((value,index) => `${history.length === 1 ? width / 2 : padding + index / (history.length - 1) * (width - padding * 2)},${height - padding - (value - min) / range * (height - padding * 2)}`).join(' ');
    create('polyline', {points, fill:'none', stroke:color, 'stroke-width':4, 'stroke-linecap':'round', 'stroke-linejoin':'round'});
    const [lastX,lastY] = points.split(' ').at(-1).split(','); create('circle', {cx:lastX,cy:lastY,r:6,fill:color,stroke:'#fff','stroke-width':3});
  });
});
