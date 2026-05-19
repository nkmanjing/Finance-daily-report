import os
import json
from datetime import datetime

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
    
    news_template = []
    for i in range(1, 11):
        news_item = {
            "title": f"新闻标题 {i}",
            "summary": "在此处输入新闻简报内容（1-2句话）",
            "link": ""
        }
        news_template.append(news_item)
    
    daily_data = {
        "date": today,
        "title": "金融资管日报",
        "news": news_template
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(daily_data, f, ensure_ascii=False, indent=2)
    
    update_dates_index(data_dir)
    
    print("=" * 50)
    print(f"生成日期: {today}")
    print(f"文件路径: {file_path}")
    print("=" * 50)
    print("提示: 您可以手动编辑生成的JSON文件，添加新闻内容和链接")

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