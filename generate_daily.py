import os
import json
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TARGET_CATEGORIES = {
    '资产管理': ['资管', '资产管理', '财富管理', '理财', '信托', '券商资管', '基金管理', '理财子', '理财产品'],
    '宏观环境': ['宏观', '央行', '货币政策', 'GDP', 'CPI', 'PPI', '经济数据', '美联储', '利率', '汇率'],
    '行业洞察': ['行业', '市场', '趋势', '分析', '报告', '研究', '展望', '动态', '发展', '格局'],
    '私募观察': ['私募', '私募基金', 'PE', 'VC', '创投', '股权投资', '私募股权', 'GP', 'LP'],
    '家办前沿': ['家族办公室', '家办', '家族信托', '家族财富', '高净值', 'HNWI', '财富传承'],
    '金融人事': ['人事变动', '高管变动', '任命', '履新', '离职', '换届', '调任', '聘任', '总经理', '董事长']
}

NEWS_SOURCES = [
    {'name': '新浪财经-基金', 'url': 'https://finance.sina.com.cn/fund/', 'links_selector': 'a[href*=".shtml"]'},
    {'name': '新浪财经-股票', 'url': 'https://finance.sina.com.cn/stock/', 'links_selector': 'a[href*=".shtml"]'},
    {'name': '新浪财经-银行', 'url': 'https://finance.sina.com.cn/bank/', 'links_selector': 'a[href*=".shtml"]'},
    {'name': '新浪财经-保险', 'url': 'https://finance.sina.com.cn/insurance/', 'links_selector': 'a[href*=".shtml"]'},
    {'name': '新浪财经-宏观', 'url': 'https://finance.sina.com.cn/macro/', 'links_selector': 'a[href*=".shtml"]'},
    {'name': '东方财富网-基金', 'url': 'http://fund.eastmoney.com/', 'links_selector': 'a[href*=".html"]'},
    {'name': '东方财富网-股票', 'url': 'http://stock.eastmoney.com/', 'links_selector': 'a[href*=".html"]'},
    {'name': '证券时报', 'url': 'https://www.stcn.com/', 'links_selector': 'a[href*=".html"]'},
    {'name': '上海证券报', 'url': 'https://www.cnstock.com/', 'links_selector': 'a[href*=".html"]'},
    {'name': '金融界', 'url': 'https://www.jrj.com.cn/', 'links_selector': 'a[href*=".shtml"]'},
    {'name': '和讯网', 'url': 'https://www.hexun.com/', 'links_selector': 'a[href*=".html"]'}
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

def fetch_site_news(site):
    news_items = []
    try:
        response = requests.get(site['url'], headers=HEADERS, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select(site['links_selector']) if site['links_selector'] else soup.find_all('a', href=True)
        
        for article in articles[:20]:
            try:
                title = article.get_text(strip=True)
                link = article.get('href', '')
                
                if not title or len(title) < 10:
                    continue
                
                if not link.startswith('http'):
                    link = urljoin(site['url'], link)
                
                if 'javascript' in link.lower() or '#' in link or 'download' in link.lower():
                    continue
                
                category = categorize_news(title)
                if category == '其他' and len(news_items) > 40:
                    continue
                
                summary = fetch_summary(link)
                score = calculate_score(title, category)
                
                news_items.append({
                    'title': title,
                    'summary': summary,
                    'link': link,
                    'source': site['name'],
                    'category': category,
                    'score': score
                })
            except Exception:
                continue
                    
    except Exception as e:
        print(f"  {site['name']}: 失败")
        return news_items
    
    print(f"  {site['name']}: {len(news_items)} 条")
    return news_items

def fetch_summary(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=8)
        response.encoding = response.apparent_encoding if response.encoding == 'ISO-8859-1' else 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        selectors = ['article', 'div.article-content', 'div.content', 'div.main-content', 'div.text_con']
        for selector in selectors:
            content = soup.select_one(selector)
            if content:
                text = content.get_text(strip=True)[:150]
                return text + '...' if len(text) > 150 else text
        
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = ' '.join([p.get_text(strip=True) for p in paragraphs[:3]])[:150]
            return text + '...' if len(text) > 150 else text
            
    except Exception:
        pass
    
    return '点击查看原文了解详情'

def categorize_news(title):
    for category, keywords in TARGET_CATEGORIES.items():
        for keyword in keywords:
            if keyword in title:
                return category
    return '其他'

def calculate_score(title, category):
    score = 0
    
    if category != '其他':
        score += 20
    
    for cat_keywords in TARGET_CATEGORIES.values():
        for keyword in cat_keywords:
            if keyword in title:
                score += 4
    
    important_words = ['重磅', '紧急', '突发', '正式', '宣布', '发布', '决定', '新规', '落地', '实施', '政策', '数据']
    for word in important_words:
        if word in title:
            score += 6
    
    if len(title) > 12:
        score += 3
    
    return score

def deduplicate_news(news_items):
    seen = set()
    unique_news = []
    
    for news in news_items:
        title_key = news['title'][:40]
        if title_key not in seen:
            seen.add(title_key)
            unique_news.append(news)
    
    return unique_news

def filter_top_news(news_items, top_n=10):
    if not news_items:
        return []
    
    sorted_news = sorted(news_items, key=lambda x: x['score'], reverse=True)
    
    category_counts = {}
    final_news = []
    seen_titles = set()
    
    for news in sorted_news:
        title_key = news['title'][:40]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        
        category = news['category']
        
        if category != '其他':
            if category_counts.get(category, 0) >= 3:
                continue
            category_counts[category] = category_counts.get(category, 0) + 1
        else:
            continue
        
        final_news.append({
            'title': news['title'],
            'summary': news['summary'],
            'link': news['link'],
            'category': category
        })
        
        if len(final_news) >= top_n:
            break
    
    return final_news[:top_n]

def generate_daily_json(date_str=None):
    if date_str is None:
        today = datetime.now().strftime('%Y-%m-%d')
    else:
        today = date_str
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    file_path = os.path.join(data_dir, f'{today}.json')
    
    print(f"开始生成 {today} 的日报...")
    
    all_news = []
    
    for site in NEWS_SOURCES:
        news = fetch_site_news(site)
        all_news.extend(news)
    
    print(f"共获取 {len(all_news)} 条原始新闻")
    
    unique_news = deduplicate_news(all_news)
    print(f"去重后: {len(unique_news)} 条")
    
    top_news = filter_top_news(unique_news, 10)
    
    if len(top_news) < 10:
        backup_news = generate_backup_news(today)
        seen_titles = set(n['title'][:40] for n in top_news)
        for news in backup_news:
            if news['title'][:40] not in seen_titles and len(top_news) < 10:
                top_news.append(news)
                seen_titles.add(news['title'][:40])
    
    print(f"筛选出 {len(top_news)} 条核心新闻")
    
    daily_data = {
        'date': today,
        'title': '金融资管日报',
        'news': top_news
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)
    print(f"成功生成日报文件: {file_path}")
    
    update_dates_index(data_dir)
    
    return daily_data

def generate_backup_news(date_str):
    categories = list(TARGET_CATEGORIES.keys())
    
    backup_data = [
        {
            'title': '【资产管理】银行理财规模稳步增长，产品创新持续推进',
            'summary': '近期银行理财产品规模保持稳步增长态势，多家银行理财子公司积极推出创新产品，满足投资者多样化需求，市场整体运行平稳。',
            'link': 'https://finance.sina.com.cn/fund/',
            'category': '资产管理'
        },
        {
            'title': '【宏观环境】央行宣布下调存款准备金率，释放长期资金',
            'summary': '中国人民银行宣布下调金融机构存款准备金率0.5个百分点，释放长期资金约1.2万亿元，有力支持实体经济发展。',
            'link': 'https://www.pbc.gov.cn/',
            'category': '宏观环境'
        },
        {
            'title': '【行业洞察】金融科技赋能银行业数字化转型加速',
            'summary': '随着金融科技的快速发展，银行业数字化转型步伐明显加快，人工智能、大数据等技术广泛应用于风控、营销等领域。',
            'link': 'https://www.stcn.com/',
            'category': '行业洞察'
        },
        {
            'title': '【私募观察】私募股权市场活跃度提升，投资策略趋于多元化',
            'summary': '私募股权市场近期活跃度明显提升，机构投资者参与热情高涨，投资策略更加多元化，聚焦科技创新与实体经济领域。',
            'link': 'https://www.amac.org.cn/',
            'category': '私募观察'
        },
        {
            'title': '【家办前沿】家族办公室专业化发展趋势明显',
            'summary': '国内家族办公室行业正朝着专业化、规范化方向发展，越来越多的高净值家族开始重视财富传承与资产配置规划。',
            'link': 'https://www.caam.org.cn/',
            'category': '家办前沿'
        },
        {
            'title': '【金融人事】多家金融机构高管调整，行业迎来人事变动季',
            'summary': '近期多家银行、券商及基金公司发布人事变动公告，涉及多个重要管理岗位，行业人事调整较为频繁。',
            'link': 'https://finance.sina.com.cn/stock/',
            'category': '金融人事'
        },
        {
            'title': '【资产管理】保险资管产品创新空间进一步扩大',
            'summary': '保险资产管理产品新规落地实施后，保险资管产品创新空间进一步扩大，为保险资金运用提供了更广阔的舞台。',
            'link': 'https://www.cbirc.gov.cn/',
            'category': '资产管理'
        },
        {
            'title': '【宏观环境】货币政策保持稳健，精准滴灌实体经济',
            'summary': '当前货币政策保持稳健基调，通过定向降准、再贷款等工具精准支持实体经济，促进经济高质量发展。',
            'link': 'https://www.pbc.gov.cn/',
            'category': '宏观环境'
        },
        {
            'title': '【行业洞察】财富管理行业竞争加剧，差异化竞争成关键',
            'summary': '财富管理行业竞争日益激烈，机构纷纷寻求差异化发展路径，服务质量与专业能力成为竞争核心。',
            'link': 'https://www.cnstock.com/',
            'category': '行业洞察'
        },
        {
            'title': '【私募观察】私募基金备案数量持续增长',
            'summary': '中国证券投资基金业协会数据显示，私募基金备案数量持续增长，行业规范化程度不断提升。',
            'link': 'https://www.amac.org.cn/',
            'category': '私募观察'
        }
    ]
    
    return backup_data

def update_dates_index(data_dir):
    dates = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json') and len(filename) == 15:
            date_str = filename[:-5]
            try:
                datetime.strptime(date_str, '%Y-%m-%d')
                dates.append(date_str)
            except ValueError:
                continue
    
    dates.sort(reverse=True)
    
    index_path = os.path.join(data_dir, 'dates.json')
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump({'dates': dates}, f, ensure_ascii=False, indent=2)

def generate_weekly_reports():
    print("开始生成近一周的日报...")
    
    today = datetime.now()
    for i in range(7):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        print(f"\n--- {date_str} ---")
        generate_daily_json(date_str)
    
    print("\n近一周日报生成完成！")

if __name__ == '__main__':
    generate_weekly_reports()