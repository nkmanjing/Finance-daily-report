import os
import json
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin

TARGET_CATEGORIES = {
    '金融人事': ['人事变动', '高管变动', '任命', '履新', '离职', '换届', '调任', '聘任', '总经理', '董事长'],
    '重大政策': ['政策', '新规', '监管', '央行', '银保监会', '证监会', '外管局', '发改委', '财政部', '发布', '宣布'],
    '资产管理': ['资管', '资产管理', '财富管理', '理财', '信托', '券商资管', '基金管理'],
    '家族办公室': ['家族办公室', '家办', '家族信托', '家族财富', '高净值'],
    '私募基金': ['私募', '私募基金', 'PE', 'VC', '创投', '股权投资', '私募股权'],
    '资产配置': ['资产配置', '投资策略', '资产组合', '大类资产', '配置策略']
}

def fetch_finance_news():
    news_items = []
    
    sites = [
        {
            'name': '新浪财经-基金',
            'url': 'https://finance.sina.com.cn/fund/',
            'links_selector': 'a[href*=".shtml"], a[href*="/doc-"], a[href*="/zt_d/"]'
        },
        {
            'name': '新浪财经-股票',
            'url': 'https://finance.sina.com.cn/stock/',
            'links_selector': 'a[href*=".shtml"], a[href*="/doc-"], a[href*="/zt_d/"]'
        },
        {
            'name': '新浪财经-银行',
            'url': 'https://finance.sina.com.cn/bank/',
            'links_selector': 'a[href*=".shtml"], a[href*="/doc-"], a[href*="/zt_d/"]'
        },
        {
            'name': '新浪财经-保险',
            'url': 'https://finance.sina.com.cn/insurance/',
            'links_selector': 'a[href*=".shtml"], a[href*="/doc-"], a[href*="/zt_d/"]'
        },
        {
            'name': '新浪财经-理财',
            'url': 'https://finance.sina.com.cn/money/',
            'links_selector': 'a[href*=".shtml"], a[href*="/doc-"]'
        },
        {
            'name': '东方财富网-基金',
            'url': 'http://fund.eastmoney.com/',
            'links_selector': 'a[href*=".html"]'
        },
        {
            'name': '东方财富网-股票',
            'url': 'http://stock.eastmoney.com/',
            'links_selector': 'a[href*=".html"]'
        },
        {
            'name': '证券时报',
            'url': 'https://www.stcn.com/',
            'links_selector': 'a[href*=".html"]'
        },
        {
            'name': '金融界',
            'url': 'https://www.jrj.com.cn/',
            'links_selector': 'a[href*=".shtml"]'
        },
        {
            'name': '上海证券报',
            'url': 'https://www.cnstock.com/',
            'links_selector': 'a[href*=".html"]'
        }
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    for site in sites:
        try:
            response = requests.get(site['url'], headers=headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.select(site['links_selector']) if site['links_selector'] else soup.find_all('a', href=True)
            
            for article in articles[:25]:
                try:
                    title = article.get_text(strip=True)
                    link = article.get('href', '')
                    
                    if not title or len(title) < 8:
                        continue
                    
                    if not link.startswith('http'):
                        link = urljoin(site['url'], link)
                    
                    if 'javascript' in link.lower() or '#' in link:
                        continue
                    
                    category = categorize_news(title)
                    
                    if category == '其他' and len(news_items) > 30:
                        continue
                    
                    summary = fetch_summary(link, headers)
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
                    
            print(f"  {site['name']}: 完成")
                    
        except Exception as e:
            print(f"  {site['name']}: 失败 - {str(e)[:30]}")
            continue
    
    return news_items

def fetch_summary(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
        score += 15
    
    for cat_keywords in TARGET_CATEGORIES.values():
        for keyword in cat_keywords:
            if keyword in title:
                score += 3
    
    important_words = ['重磅', '紧急', '突发', '正式', '宣布', '发布', '决定', '新规', '落地', '实施']
    for word in important_words:
        if word in title:
            score += 8
    
    if len(title) > 15:
        score += 2
    
    return score

def deduplicate_news(news_items):
    seen = set()
    unique_news = []
    
    for news in news_items:
        title_key = news['title'][:35]
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
        title_key = news['title'][:35]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        
        category = news['category']
        
        if category != '其他':
            if category_counts.get(category, 0) >= 3:
                continue
            category_counts[category] = category_counts.get(category, 0) + 1
        else:
            other_count = sum(1 for n in final_news if categorize_news(n['title']) == '其他')
            if other_count >= 4:
                continue
        
        final_news.append({
            'title': news['title'],
            'summary': news['summary'],
            'link': news['link']
        })
        
        if len(final_news) >= top_n:
            break
    
    return final_news[:top_n]

def generate_daily_json():
    today = datetime.now().strftime('%Y-%m-%d')
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    file_path = os.path.join(data_dir, f'{today}.json')
    
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"删除已存在的文件: {file_path}")
    
    print(f"开始生成 {today} 的日报...")
    print("正在抓取新闻源...")
    
    all_news = fetch_finance_news()
    print(f"共获取 {len(all_news)} 条原始新闻")
    
    print("去重中...")
    unique_news = deduplicate_news(all_news)
    print(f"去重后: {len(unique_news)} 条")
    
    print("筛选核心新闻...")
    top_news = filter_top_news(unique_news, 10)
    
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
    
    print("=" * 60)
    print(f"日报生成完成")
    print(f"日期: {today}")
    print(f"文件路径: {file_path}")
    print(f"新闻条数: {len(top_news)}")
    if len(top_news) < 10:
        print(f"警告: 仅获取到 {len(top_news)} 条新闻")
    print("=" * 60)
    
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
    
    print(f"已更新日期索引，共 {len(dates)} 条记录")

if __name__ == '__main__':
    generate_daily_json()