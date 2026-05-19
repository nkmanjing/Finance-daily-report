const dateListEl = document.getElementById('date-list');
const newsContentEl = document.getElementById('news-content');
let dates = [];

const categoryColors = {
  '资产管理': 'bg-green-600',
  '宏观环境': 'bg-red-600',
  '行业洞察': 'bg-purple-600',
  '私募观察': 'bg-orange-600',
  '家办前沿': 'bg-pink-600',
  '金融人事': 'bg-blue-600',
  '政策动态': 'bg-indigo-600',
  '市场动态': 'bg-cyan-600'
};

function formatDate(dateStr) {
  const date = new Date(dateStr);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
  const weekDay = weekDays[date.getDay()];
  return `${month}月${day}日 周${weekDay}`;
}

function renderDateList() {
  dateListEl.innerHTML = '';
  
  if (dates.length === 0) {
    dateListEl.innerHTML = '<div class="text-center text-slate-500 text-sm py-2">暂无日报数据</div>';
    return;
  }

  dates.forEach(date => {
    const item = document.createElement('div');
    item.className = 'date-item px-3 py-2 rounded cursor-pointer text-sm transition-colors';
    item.innerHTML = `
      <div class="font-medium">${formatDate(date)}</div>
      <div class="text-xs text-slate-400 mt-0.5">${date}</div>
    `;
    item.addEventListener('click', () => loadNews(date));
    dateListEl.appendChild(item);
  });
}

function renderNews(data) {
  if (!data || !data.news || data.news.length === 0) {
    newsContentEl.innerHTML = `
      <div class="flex flex-col items-center justify-center h-full text-slate-500">
        <svg class="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <p class="text-lg">暂无新闻数据</p>
      </div>
    `;
    return;
  }

  const newsByCategory = {};
  data.news.forEach(news => {
    const category = news.category || '其他';
    if (!newsByCategory[category]) {
      newsByCategory[category] = [];
    }
    newsByCategory[category].push(news);
  });

  let newsHtml = '';
  let itemIndex = 1;
  
  Object.keys(newsByCategory).forEach(category => {
    const categoryNews = newsByCategory[category];
    const colorClass = categoryColors[category] || 'bg-gray-600';
    
    newsHtml += `
      <div class="mb-8">
        <div class="flex items-center gap-2 mb-4">
          <div class="${colorClass} w-2 h-6 rounded"></div>
          <h3 class="text-lg font-semibold text-white">${category}</h3>
          <span class="text-sm text-slate-500">(${categoryNews.length}条)</span>
        </div>
        <div class="space-y-3 pl-4 border-l-2 border-slate-700">
    `;
    
    categoryNews.forEach(news => {
      newsHtml += `
        <div class="news-card p-4">
          <div class="flex items-start gap-3">
            <div class="w-6 h-6 ${colorClass} rounded flex items-center justify-center flex-shrink-0 text-xs font-bold text-white">
              ${itemIndex++}
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="font-medium text-white mb-1.5">${news.title}</h4>
              <p class="text-slate-400 text-sm leading-relaxed">${news.summary}</p>
              ${news.link ? `
                <a href="${news.link}" target="_blank" class="inline-flex items-center mt-2 text-blue-400 text-xs hover:text-blue-300 transition-colors">
                  <span>查看原文</span>
                  <svg class="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
                  </svg>
                </a>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    });
    
    newsHtml += `</div></div>`;
  });

  newsContentEl.innerHTML = `
    <div class="max-w-4xl mx-auto">
      <div class="mb-8">
        <h2 class="text-2xl font-bold text-white">${data.title}</h2>
        <p class="text-slate-400 mt-2">${data.date}</p>
        <p class="text-slate-500 text-sm mt-1">共 ${data.news.length} 条新闻</p>
      </div>
      ${newsHtml}
    </div>
  `;
}

async function loadNews(date) {
  const activeItem = dateListEl.querySelector('.active');
  if (activeItem) activeItem.classList.remove('active');
  
  const items = dateListEl.querySelectorAll('.date-item');
  items.forEach(item => {
    if (item.textContent.includes(date)) {
      item.classList.add('active');
    }
  });

  try {
    const response = await fetch(`data/${date}.json`);
    if (!response.ok) {
      throw new Error('File not found');
    }
    const data = await response.json();
    renderNews(data);
  } catch (error) {
    console.error('加载数据失败:', error);
    newsContentEl.innerHTML = `
      <div class="flex flex-col items-center justify-center h-full text-slate-500">
        <svg class="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>
        </svg>
        <p class="text-lg">无法加载 ${date} 的日报数据</p>
      </div>
    `;
  }
}

async function loadDates() {
  try {
    const response = await fetch('data/dates.json');
    if (!response.ok) {
      throw new Error('Index file not found');
    }
    const data = await response.json();
    dates = data.dates || [];
    renderDateList();
    
    if (dates.length > 0) {
      loadNews(dates[0]);
    }
  } catch (error) {
    console.error('加载日期列表失败:', error);
    dates = [];
    renderDateList();
  }
}

loadDates();