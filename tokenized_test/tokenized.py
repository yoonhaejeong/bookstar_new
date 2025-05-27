import os
import sqlite3
import csv
import re
from konlpy.tag import Okt

# DB 경로 설정 예시
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db.sqlite3')

# 품사 태그 선택: 필요한 POS(품사)만 남길 때
# - Okt 기준 주요 태그 예시
#   Noun(명사), Verb(동사), Adjective(형용사), Adverb(부사), Josa(조사), Determiner(관형사), Exclamation(감탄사), ...
desired_tags = ['Noun', 'Adjective']  # 원하는 품사 태그만 남긴다고 가정

# 불용어(Stopwords) 목록 예시
# - 자주 등장하지만 의미가 적거나, 제거하고 싶은 단어를 등록
stopwords = {
    '있다', '하다', '되다', '이다', '에서', '저', '거',
    # 필요없는 조사·어미·대명사·접속사 등
    '은', '는', '이', '가', '의', '을', '를', '에', '로', '과', '와', '도'
}

# 텍스트 전처리 & 형태소 분석 함수
def preprocess_text(text, okt):
    # (1) 불필요한 문자 제거(정규식 사용 예시)
    #    - 한글, 영문, 숫자, 공백만 남기고 모두 제거
    text = re.sub('[^가-힣0-9a-zA-Z\\s]', '', text)

    # (2) 형태소 분석 및 POS 태깅
    #     stem=True 옵션을 주면, 어간 추출(기본형/원형 처리)을 수행
    morphs_pos = okt.pos(text, norm=True, stem=True)

    # (3) 품사 필터링 + 불용어 제거
    filtered_tokens = [
        word for word, tag in morphs_pos
        if (tag in desired_tags) and (word not in stopwords)
    ]

    # (선택) 길이가 너무 짧은 단어나 숫자만 있는 토큰 등을 제거하고 싶다면 추가 필터링
    # e.g. 2글자 미만 제거:
    # filtered_tokens = [w for w in filtered_tokens if len(w) >= 2]

    return filtered_tokens


def main():
    # DB 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 예: book 테이블에서 'id', 'description' 열을 가져온다고 가정
    query = "SELECT id, description FROM book"
    cursor.execute(query)
    rows = cursor.fetchall()

    # 형태소 분석기 초기화
    okt = Okt()

    tokenized_data = []
    for row in rows:
        book_id = row[0]
        description = row[1]

        if not description:
            tokens = []
        else:
            # 위에서 정의한 전처리 함수를 통해 원하는 형태의 토큰만 추출
            tokens = preprocess_text(description, okt)

        # CSV나 다른 용도로 저장하기 위해 공백으로 합친 문자열을 만들 수도 있음
        token_str = " ".join(tokens)
        tokenized_data.append([book_id, description, token_str])

    # CSV 저장
    csv_filename = 'refined_tokenized_book_descriptions.csv'
    with open(csv_filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["book_id", "original_description", "refined_tokens"])
        for row_data in tokenized_data:
            writer.writerow(row_data)

    cursor.close()
    conn.close()
    print(f"처리 완료! '{csv_filename}' 파일에 결과가 저장되었습니다.")


if __name__ == '__main__':
    main()
