import os
import django
import sqlite3
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Django 설정 초기화
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # 이 부분 꼭 맞춰야 함
django.setup()

from book.models import Book

# SQLite에서 직접 데이터 가져오기
conn = sqlite3.connect("db.sqlite3")
cursor = conn.cursor()

cursor.execute("""
    SELECT title, author, publisher, publish_date, description, rating, review_count, genre, link
    FROM book
""")

rows = cursor.fetchall()
success = 0
fail = 0

for row in rows:
    try:
        raw_date = row[3]
        publish_date = None
        if raw_date:
            publish_date = datetime.strptime(raw_date, "%Y.%m.%d").date()

        Book.objects.create(
            title=row[0],
            author=row[1],
            publisher=row[2],
            publish_date=publish_date,
            description=row[4],
            rating=row[5],
            review_count=row[6],
            genre=row[7],
            link=row[8]
        )
        success += 1
    except Exception as e:
        print(f"[❌ 오류] {row[0]} → {e}")
        fail += 1

conn.close()

print(f"\n✅ 완료: {success}개 추가 / ❌ 실패: {fail}개")
