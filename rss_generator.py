import requests
from bs4 import BeautifulSoup
import csv
import datetime
import re
import xml.dom.minidom as md
from xml.etree.ElementTree import Element, SubElement, tostring
import html

def scrape_ytu_announcements():
    """
    YTÜ duyurular sayfasından başlık ve linkleri çeker.
    Tarih ve başlık ayrı ayrı geliyorsa, birleştirerek tek bir duyuru olarak döndürür.
    Ayrıca, tarih bilgisini 2025 yılı ile birlikte döndürür.
    """
    url = 'https://www.yildiz.edu.tr/universite/haberler/ytu-duyurular'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    month_map = {
        'Oca': '01', 'Şub': '02', 'Mar': '03', 'Nis': '04', 'May': '05', 'Haz': '06',
        'Tem': '07', 'Ağu': '08', 'Eyl': '09', 'Eki': '10', 'Kas': '11', 'Ara': '12'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = [a for a in soup.find_all('a', href=True) if a['href'].startswith('/universite/ytu-duyurular/') and a.get_text(strip=True)]
        announcements = []
        date_regex = r'^(\d{2})([A-Za-zÇŞĞÜÖİçşğüöı]{3})$'  # 15Nis, 07Nis gibi
        i = 0
        while i < len(links):
            title = links[i].get_text(strip=True)
            url_full = f"https://www.yildiz.edu.tr{links[i]['href']}"
            date_str = None
            # Eğer başlık tarih formatındaysa ve bir sonraki başlık aynı linke sahipse birleştir
            m = re.match(date_regex, title)
            if m and i+1 < len(links):
                day = m.group(1)
                mon_abbr = m.group(2).capitalize()
                month = month_map.get(mon_abbr, '01')
                date_str = f"2025-{month}-{day}"
                next_title = links[i+1].get_text(strip=True)
                next_url_full = f"https://www.yildiz.edu.tr{links[i+1]['href']}"
                if next_url_full == url_full:
                    announcements.append({
                        'title': f"{next_title}",
                        'url': url_full,
                        'date': date_str
                    })
                    i += 2
                    continue
            # Eğer başlık tarih değilse ya da birleştirme yapılamıyorsa olduğu gibi ekle
            announcements.append({'title': title, 'url': url_full, 'date': None})
            i += 1
        return announcements
    except Exception as e:
        print(f"Duyurular çekilemedi: {e}")
        return []

def generate_rss(announcements, filename):
    # RSS kökünü oluştur
    rss = Element('rss', {'version': '2.0'})
    channel = SubElement(rss, 'channel')
    title = SubElement(channel, 'title')
    title.text = 'YTÜ Duyurular'
    link = SubElement(channel, 'link')
    link.text = 'https://www.yildiz.edu.tr/universite/haberler/ytu-duyurular'
    description = SubElement(channel, 'description')
    description.text = 'Yıldız Teknik Üniversitesi Resmi Duyurular'
    for ann in announcements:
        item = SubElement(channel, 'item')
        item_title = SubElement(item, 'title')
        # Tarihi başlığa ekle
        if ann.get('date'):
            item_title.text = f"{ann['title']} ({ann['date']})"
        else:
            item_title.text = ann['title']
        item_link = SubElement(item, 'link')
        item_link.text = ann['url']
        # pubDate alanı ekle
        if ann.get('date'):
            try:
                pubdate = datetime.datetime.strptime(ann['date'], "%Y-%m-%d")
                pubdate_str = pubdate.strftime("%a, %d %b %Y 12:00:00 +0300")
                pubDate = SubElement(item, 'pubDate')
                pubDate.text = pubdate_str
            except Exception:
                pass
    rough_string = tostring(rss, 'utf-8')
    reparsed = md.parseString(rough_string)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(reparsed.toprettyxml(indent="  "))
    print(f"RSS beslemesi başarıyla oluşturuldu: {filename}")

if __name__ == "__main__":
    print("YTÜ duyuruları çekiliyor...")
    announcements = scrape_ytu_announcements()
    if announcements:
        print(f"{len(announcements)} duyuru bulundu.")
        # generate_rss fonksiyonunu duyurular için kullan
        generate_rss(announcements, "ytu_duyurular.xml")
        for i, ann in enumerate(announcements[:5], 1):
            print(f"Duyuru {i}:")
            print(f"Başlık: {ann['title']}")
            print(f"URL: {ann['url']}")
            print("-"*50)
    else:
        print("Hiç duyuru bulunamadı. RSS oluşturulamadı.")