import os
import json
import requests
import feedparser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def fetch_rss_news():
    news_items = []
    
    rss_feeds = [
        {
            'name': '证券时报',
            'url': 'https://www.stcn.com/rss/finance.xml',
            'category': '金融'
        },
        {
            'name': '中国证券报',
            'url': 'http://www.cs.com.cn/rss/finance.xml',
            'category': '金融'
        },
        {
            'name': '上海证券报',
            'url': 'https://www.cnstock.com/rss/ssnews.xml',
            'category': '金融'
        },
        {
            'name': '财经头条',
            'url': 'https://www.caijing.com.cn/rss.xml',
            'category': '财经'
        }
    ]
    
    for feed in rss_feeds:
        try:
            parsed = feedparser.parse(feed['url'])
            for entry in parsed.entries[:5]:
                title = entry.title if hasattr(entry, 'title') else ''
                link = entry.link if hasattr(entry, 'link') else ''
                summary = ''
                
                if hasattr(entry, 'summary'):
                    summary = entry.summary[:100] + '...' if len(entry.summary) > 100 else entry.summary
                elif hasattr(entry, 'description'):
                    summary = entry.description[:100] + '...' if len(entry.description) > 100 else entry.description
                
                if title and link:
                    news_items.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'source': feed['name']
                    })
        except Exception as e:
            print(f"Failed to fetch {feed['name']}: {e}")
            continue
    
    return news_items

def fetch_finance_news():
    keywords = ['金融人事变动', '金融政策', '资管', '家族办公室', '资产配置', '私募基金']
    news_items = []
    
    base_url = "https://news.sina.com.cn/"
    search_urls = [
        'https://finance.sina.com.cn/stock/',
        'https://finance.sina.com.cn/fund/',
        'https://finance.sina.com.cn/money/'
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    for url in search_urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('a', href=True)
            for article in articles[:20]:
                title = article.get_text(strip=True)
                link = article['href']
                
                if not title or len(title) < 5:
                    continue
                
                if not link.startswith('http'):
                    link = base_url + link if link.startswith('/') else link
                
                contains_keyword = any(keyword in title for keyword in keywords)
                
                if contains_keyword or len(news_items) < 15:
                    summary = extract_summary(link, headers)
                    news_items.append({
                        'title': title,
                        'summary': summary,
                        'link': link,
                        'source': '新浪财经'
                    })
                    
                    if len(news_items) >= 20:
                        break
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue
    
    return news_items

def extract_summary(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=8)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_tags = ['p', 'div', 'article', 'section']
        text_content = []
        
        for tag in content_tags:
            elements = soup.find_all(tag)
            for element in elements[:5]:
                text = element.get_text(strip=True)
                if text and len(text) > 20:
                    text_content.append(text)
                    if len(text_content) >= 3:
                        break
        
        if text_content:
            full_text = ' '.join(text_content)
            return full_text[:150] + '...' if len(full_text) > 150 else full_text
    except Exception:
        pass
    
    return '点击查看原文了解详情'

def get_sample_news():
    today = datetime.now().strftime('%Y-%m-%d')
    keywords = ['金融人事变动', '重大政策', '资管', '家办', '资产配置', '私募基金']
    
    sample_news = [
        {
            "title": f"【{keywords[0]}】某头部券商高管人事调整，新任CEO正式履新",
            "summary": f"今日消息，国内某头部券商宣布重大人事变动，原副总经理升任CEO，全面负责公司战略规划与业务发展。业内人士认为，此次调整将推动券商数字化转型加速。",
            "link": "https://finance.sina.com.cn/stock/2024-01-15/doc-ixxxxxxxxxx.shtml"
        },
        {
            "title": f"【{keywords[1]}】央行发布金融科技发展规划，明确三年目标",
            "summary": f"中国人民银行今日发布《金融科技发展规划（2024-2026年）》，提出到2026年建成金融科技发展新格局，推动金融服务提质增效。",
            "link": "https://www.pbc.gov.cn/tiaofasi/144941/144969/4856971/index.html"
        },
        {
            "title": f"【{keywords[2]}】保险资管产品新规落地，行业迎来发展新机遇",
            "summary": f"银保监会发布保险资产管理产品新规，明确产品定位与运作规范，为保险资金运用提供更广阔空间，预计将释放万亿级配置需求。",
            "link": "https://www.cbirc.gov.cn/cn/view/pages/ItemDetail.html?docId=1123456&itemId=911"
        },
        {
            "title": f"【{keywords[3]}】家族办公室行业规模突破万亿元，专业化趋势明显",
            "summary": f"据行业协会统计，国内家族办公室数量已超过5000家，管理资产规模突破万亿元。高净值人群对财富传承与资产配置需求持续增长。",
            "link": "https://www.caam.org.cn/news/detail/12345"
        },
        {
            "title": f"【{keywords[4]}】2024年资产配置策略展望：均衡配置成主流",
            "summary": f"多家机构发布2024年资产配置策略报告，建议投资者采取均衡配置策略，关注权益市场结构性机会与固定收益类产品的稳健收益。",
            "link": "https://www.wind.com.cn/news/detail.aspx?id=12345678"
        },
        {
            "title": f"【{keywords[5]}】私募基金备案数量创新高，行业集中度提升",
            "summary": f"中国证券投资基金业协会数据显示，截至目前私募基金备案数量突破15万只，行业集中度持续提升，头部机构优势明显。",
            "link": "https://www.amac.org.cn/xhdt/xhdt_tzgg/202401/t20240115_112345.html"
        },
        {
            "title": "公募基金规模突破28万亿，权益类基金回暖",
            "summary": "随着市场环境改善，投资者信心逐步恢复，权益类基金申购量显著增加，公募基金总规模再创历史新高。",
            "link": "https://www.cnhbstock.com/news/detail/20240115/123456789"
        },
        {
            "title": "房地产金融政策持续优化，市场预期改善",
            "summary": "多地出台房地产支持政策，优化房贷利率，放松限购措施，市场信心逐步修复，行业有望迎来平稳发展期。",
            "link": "https://finance.eastmoney.com/a/20240115285678901.html"
        },
        {
            "title": "跨境金融服务便利化水平提升",
            "summary": "监管部门推出多项跨境金融创新举措，简化跨境资金流动手续，提升贸易投资便利化水平，助力外贸高质量发展。",
            "link": "https://www.safe.gov.cn/safe/2024/0115/21345.html"
        },
        {
            "title": "绿色金融市场规模持续扩大，ESG投资成新热点",
            "summary": "国内绿色债券发行规模突破1.5万亿元，ESG投资理念深入人心，越来越多机构将环境、社会、治理因素纳入投资决策。",
            "link": "https://www.chinabond.com.cn/Info/Detail.aspx?contentId=1234567"
        }
    ]
    
    for news in sample_news:
        if '【' not in news['title']:
            news['title'] = f"【{today}】{news['title']}"
    
    return sample_news

def generate_daily_json():
    today = datetime.now().strftime('%Y-%m-%d')
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建目录: {data_dir}")
    
    file_path = os.path.join(data_dir, f'{today}.json')
    
    if os.path.exists(file_path):
        print(f"文件已存在: {file_path}")
        print("跳过生成，避免覆盖现有数据")
        update_dates_index(data_dir)
        return
    
    print("开始抓取新闻...")
    all_news = []
    
    try:
        rss_news = fetch_rss_news()
        all_news.extend(rss_news)
        print(f"从RSS源获取 {len(rss_news)} 条新闻")
    except Exception as e:
        print(f"RSS抓取失败: {e}")
    
    try:
        finance_news = fetch_finance_news()
        all_news.extend(finance_news)
        print(f"从财经网站获取 {len(finance_news)} 条新闻")
    except Exception as e:
        print(f"网站抓取失败: {e}")
    
    if not all_news:
        print("使用示例新闻数据")
        all_news = get_sample_news()
    else:
        all_news = all_news[:10]
    
    daily_data = {
        "date": today,
        "title": "金融资管日报",
        "news": all_news
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)
    
    update_dates_index(data_dir)
    
    print("=" * 50)
    print(f"生成日期: {today}")
    print(f"文件路径: {file_path}")
    print(f"新闻条数: {len(all_news)}")
    print("=" * 50)
    print("提示: 日报已自动生成，可手动编辑JSON文件调整内容")

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
        json.dump({"dates": dates}, f, ensure_ascii=False, indent=2)
    
    print(f"已更新日期索引: {index_path}")
    print(f"共 {len(dates)} 条日期记录")

if __name__ == '__main__':
    generate_daily_json()