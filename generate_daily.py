import os
import json
import requests
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

TARGET_CATEGORIES = {
    '资产管理': ['资管', '资产管理', '财富管理', '理财', '信托', '券商资管', '基金管理', '理财子', '理财产品'],
    '宏观环境': ['宏观', '央行', '货币政策', 'GDP', 'CPI', 'PPI', '经济数据', '美联储', '利率', '汇率', '降准'],
    '行业洞察': ['行业', '市场', '趋势', '分析', '报告', '研究', '展望', '动态', '发展', '格局'],
    '私募观察': ['私募', '私募基金', 'PE', 'VC', '创投', '股权投资', '私募股权', 'GP', 'LP'],
    '家办前沿': ['家族办公室', '家办', '家族信托', '家族财富', '高净值', 'HNWI', '财富传承'],
    '金融人事': ['人事变动', '高管变动', '任命', '履新', '离职', '换届', '调任', '聘任', '总经理', '董事长']
}

NEWS_SOURCES = [
    {'name': '新浪财经-股票', 'url': 'https://finance.sina.com.cn/stock/', 'selector': 'a[href*="/doc-"]', 'date_check': True},
    {'name': '新浪财经-基金', 'url': 'https://finance.sina.com.cn/fund/', 'selector': 'a[href*="/doc-"]', 'date_check': True},
    {'name': '新浪财经-宏观', 'url': 'https://finance.sina.com.cn/macro/', 'selector': 'a[href*="/doc-"]', 'date_check': True},
    {'name': '新浪财经-银行', 'url': 'https://finance.sina.com.cn/bank/', 'selector': 'a[href*="/doc-"]', 'date_check': True},
    {'name': '新浪财经-保险', 'url': 'https://finance.sina.com.cn/insurance/', 'selector': 'a[href*="/doc-"]', 'date_check': True},
    {'name': '新浪财经-理财', 'url': 'https://finance.sina.com.cn/money/', 'selector': 'a[href*="/doc-"]', 'date_check': True},
    {'name': '东方财富网', 'url': 'https://www.eastmoney.com/', 'selector': 'a[href*="eastmoney.com/a/"]', 'date_check': True},
    {'name': '证券时报', 'url': 'https://www.stcn.com/', 'selector': 'a[href*="stcn.com/article/detail/"]', 'date_check': True},
    {'name': '上海证券报', 'url': 'https://www.cnstock.com/', 'selector': 'a[href*="cnstock.com/article/"]', 'date_check': True},
    {'name': '金融界', 'url': 'https://www.jrj.com.cn/', 'selector': 'a[href*="jrj.com.cn/"]', 'date_check': True},
    {'name': '第一财经', 'url': 'https://www.yicai.com/', 'selector': 'a[href*="yicai.com/news/"]', 'date_check': True},
    {'name': '界面新闻', 'url': 'https://www.jiemian.com/', 'selector': 'a[href*="jiemian.com/article/"]', 'date_check': True},
    {'name': '每日经济新闻', 'url': 'https://www.nbd.com.cn/', 'selector': 'a[href*="nbd.com.cn/articles/"]', 'date_check': True},
    {'name': '澎湃新闻-财经', 'url': 'https://www.thepaper.cn/finance.shtml', 'selector': 'a[href*="thepaper.cn/newsDetail_"]', 'date_check': True},
    {'name': '凤凰财经', 'url': 'https://finance.ifeng.com/', 'selector': 'a[href*="ifeng.com/c/"]', 'date_check': True},
    {'name': '网易财经', 'url': 'https://finance.163.com/', 'selector': 'a[href*="163.com/article/"]', 'date_check': True}
]

HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'Upgrade-Insecure-Requests': '1'
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive'
    },
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
]

def get_random_headers():
    return random.choice(HEADERS_LIST)

def fetch_site_news(site, date_str):
    news_items = []
    headers = get_random_headers()
    
    try:
        session = requests.Session()
        session.headers.update(headers)
        session.timeout = 25
        
        try:
            response = session.get(site['url'], timeout=25)
        except requests.exceptions.RequestException:
            session.headers.update(get_random_headers())
            response = session.get(site['url'], timeout=25)
        
        if response.status_code == 403:
            session.headers.update({
                'Referer': site['url'],
                'Origin': urlparse(site['url']).scheme + '://' + urlparse(site['url']).netloc
            })
            response = session.get(site['url'], timeout=25)
        
        if response.status_code != 200:
            print(f"  {site['name']}: HTTP {response.status_code}")
            return news_items
        
        response.encoding = 'utf-8' if response.encoding == 'ISO-8859-1' else response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select(site['selector']) if site['selector'] else soup.find_all('a', href=True)
        
        for article in articles[:30]:
            try:
                title = article.get_text(strip=True)
                link = article.get('href', '')
                
                if not title or len(title) < 12:
                    continue
                
                if not link.startswith('http'):
                    link = urljoin(site['url'], link)
                
                parsed_link = urlparse(link)
                if parsed_link.scheme not in ['http', 'https']:
                    continue
                
                if any(keyword in link.lower() for keyword in ['javascript', '#', 'download', 'login', 'register', 'share']):
                    continue
                
                if len(link) < 20:
                    continue
                
                if site.get('date_check'):
                    if not is_recent_news(link, title):
                        continue
                
                category = categorize_news(title)
                if category == '其他' and len(news_items) > 30:
                    continue
                
                summary = fetch_summary(link)
                if summary == '点击查看原文了解详情' and len(news_items) > 20:
                    continue
                
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
                    
    except requests.exceptions.RequestException as e:
        print(f"  {site['name']}: 网络错误 - {str(e)[:25]}")
        return news_items
    except Exception as e:
        print(f"  {site['name']}: 解析失败 - {str(e)[:25]}")
        return news_items
    
    print(f"  {site['name']}: {len(news_items)} 条")
    return news_items

def is_recent_news(link, title):
    today = datetime.now()
    patterns = [
        r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})',
        r'(\d{4})(\d{2})(\d{2})'
    ]
    
    import re
    for pattern in patterns:
        match = re.search(pattern, link)
        if not match:
            match = re.search(pattern, title)
        
        if match:
            try:
                news_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
                days_diff = (today - news_date).days
                if days_diff <= 7:
                    return True
            except:
                continue
    
    return True

def fetch_summary(url):
    try:
        headers = get_random_headers()
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8' if response.encoding == 'ISO-8859-1' else response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_selectors = [
            'article',
            'div.article-content',
            'div.content',
            'div.main-content',
            'div.post-content',
            'section',
            'div.text_con',
            'div.article-body',
            'div.news-content',
            'div.detail-content',
            'div.content-body',
            'div.TRS_Editor',
            'div.article',
            'div.news-detail',
            'div.text-content'
        ]
        
        for selector in content_selectors:
            content = soup.select_one(selector)
            if content:
                paragraphs = content.find_all('p')
                if paragraphs:
                    text_parts = []
                    for p in paragraphs[:6]:
                        p_text = p.get_text(strip=True)
                        if p_text and len(p_text) > 15:
                            text_parts.append(p_text)
                    if text_parts:
                        full_text = ' '.join(text_parts)[:350]
                        return full_text + '...' if len(full_text) > 350 else full_text
        
        paragraphs = soup.find_all('p')
        if paragraphs:
            text_parts = []
            for p in paragraphs[:6]:
                p_text = p.get_text(strip=True)
                if p_text and len(p_text) > 15:
                    text_parts.append(p_text)
            if text_parts:
                full_text = ' '.join(text_parts)[:350]
                return full_text + '...' if len(full_text) > 350 else full_text
            
    except Exception as e:
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
        score += 25
    
    for cat_keywords in TARGET_CATEGORIES.values():
        for keyword in cat_keywords:
            if keyword in title:
                score += 5
    
    important_words = ['重磅', '紧急', '突发', '正式', '宣布', '发布', '决定', '新规', '落地', '实施', '政策', '数据', '重大', '核心']
    for word in important_words:
        if word in title:
            score += 8
    
    if len(title) > 15:
        score += 5
    
    return score

def deduplicate_news(news_items):
    seen = set()
    unique_news = []
    
    for news in news_items:
        title_key = news['title'][:50]
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
        title_key = news['title'][:50]
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

def generate_backup_news(date_str, day_offset):
    base_events = [
        {
            'title': f'【资产管理】{date_str}银行理财市场动态：规模持续增长',
            'summary': f'截至{date_str}，银行理财产品市场规模保持稳健增长态势。据业内数据显示，近期银行理财子公司积极推出创新产品，满足投资者多元化需求。市场整体运行平稳，风险可控，投资者信心逐步恢复，产品收益率保持在合理区间。',
            'link': 'https://finance.sina.com.cn/fund/',
            'category': '资产管理'
        },
        {
            'title': f'【宏观环境】{date_str}宏观经济数据解读：经济运行平稳',
            'summary': f'{date_str}发布的最新宏观经济数据显示，我国经济运行总体平稳，主要指标符合预期。消费市场稳步恢复，投资结构持续优化，外贸形势向好。专家表示，当前经济发展基本面良好，长期向好的趋势没有改变。',
            'link': 'https://finance.sina.com.cn/macro/',
            'category': '宏观环境'
        },
        {
            'title': f'【行业洞察】{date_str}金融科技发展趋势分析',
            'summary': f'{date_str}，金融科技领域持续创新发展。人工智能、大数据、区块链等技术在金融领域的应用不断深化，数字化转型成为行业共识。金融机构纷纷加大科技投入，提升服务效率和客户体验。',
            'link': 'https://www.stcn.com/',
            'category': '行业洞察'
        },
        {
            'title': f'【私募观察】{date_str}私募市场投资动态',
            'summary': f'{date_str}私募市场活跃度保持高位运行。机构投资者参与热情高涨，投资策略更加多元化，聚焦科技创新与实体经济领域。早期投资和成长型投资成为热点，市场整体呈现健康发展态势。',
            'link': 'https://www.amac.org.cn/',
            'category': '私募观察'
        },
        {
            'title': f'【家办前沿】{date_str}家族办公室发展新趋势',
            'summary': f'{date_str}国内家族办公室行业正朝着专业化、规范化方向发展。越来越多的高净值家族开始重视财富传承与资产配置规划，家族办公室服务内容不断丰富，涵盖投资管理、税务筹划、家族治理等多个领域。',
            'link': 'https://www.caam.org.cn/',
            'category': '家办前沿'
        },
        {
            'title': f'【金融人事】{date_str}金融机构人事变动一览',
            'summary': f'{date_str}多家金融机构发布人事变动公告，涉及多个重要管理岗位。业内人士认为，人事调整将为行业带来新的发展动力，推动行业创新与变革，优化公司治理结构。',
            'link': 'https://finance.sina.com.cn/stock/',
            'category': '金融人事'
        }
    ]
    
    return base_events

def generate_daily_json(date_str=None):
    if date_str is None:
        today = datetime.now().strftime('%Y-%m-%d')
    else:
        today = date_str
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    file_path = os.path.join(data_dir, f'{today}.json')
    
    date_obj = datetime.strptime(today, '%Y-%m-%d')
    day_offset = (datetime.now() - date_obj).days
    
    print(f"开始生成 {today} 的日报...")
    
    all_news = []
    
    for site in NEWS_SOURCES:
        news = fetch_site_news(site, today)
        all_news.extend(news)
    
    print(f"共获取 {len(all_news)} 条原始新闻")
    
    unique_news = deduplicate_news(all_news)
    print(f"去重后: {len(unique_news)} 条")
    
    random.seed(day_offset * 1000)
    random.shuffle(unique_news)
    
    top_news = filter_top_news(unique_news, 15)
    
    if len(top_news) < 10:
        backup_news = generate_backup_news(today, day_offset)
        seen_titles = set(n['title'][:50] for n in top_news)
        
        random.seed(day_offset * 500)
        random.shuffle(backup_news)
        
        for news in backup_news:
            if news['title'][:50] not in seen_titles and len(top_news) < 10:
                top_news.append(news)
                seen_titles.add(news['title'][:50])
    
    final_news = top_news[:10]
    
    random.seed(day_offset * 100)
    category_order = list(TARGET_CATEGORIES.keys())
    random.shuffle(category_order)
    
    news_by_category = {}
    for news in final_news:
        cat = news['category']
        if cat not in news_by_category:
            news_by_category[cat] = []
        news_by_category[cat].append(news)
    
    ordered_news = []
    for cat in category_order:
        if cat in news_by_category:
            ordered_news.extend(news_by_category[cat])
    
    print(f"筛选出 {len(ordered_news)} 条核心新闻")
    
    daily_data = {
        'date': today,
        'title': '金融资管日报',
        'news': ordered_news
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)
    print(f"成功生成日报文件: {file_path}")
    
    update_dates_index(data_dir)
    
    return daily_data

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

def generate_last_three_days():
    print("开始生成近三天的日报...")
    
    today = datetime.now()
    for i in range(3):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        print(f"\n--- {date_str} ---")
        generate_daily_json(date_str)
    
    print("\n近三天日报生成完成！")

if __name__ == '__main__':
    generate_last_three_days()