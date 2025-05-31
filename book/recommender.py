from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
import pandas as pd
import pickle
from .model import NCF  # 모델 정의가 book/model.py에 있다고 가정


class HybridRecommender:
    def __init__(self, ncf_model, book_df, user2id, item2id, id2item, kobert_model, alpha=0.7):
        self.ncf_model = ncf_model
        self.book_df = book_df
        self.user2id = user2id
        self.item2id = item2id
        self.id2item = id2item
        self.kobert_model = kobert_model
        self.alpha = alpha
        self.device = next(ncf_model.parameters()).device
        self.embedder = SentenceTransformer('jhgan/ko-sbert-sts', device=self.device)

        # 책 설명 임베딩
        print("책 설명 임베딩 중...")
        self.book_embeddings = kobert_model.encode(
            book_df['description'].fillna("").tolist(),
            convert_to_tensor=True,
            device=self.device
        )

    #이전 recommend 코드는 따로 뺴둠둠

    #수정 reccomend
    def recommend(self, user_id, user_review, top_k=5):
        self.ncf_model.eval()

        #  사용자 ID가 존재하는지 확인
        if user_id not in self.user2id:
            raise ValueError(f"[오류] user_id '{user_id}' 가 user2id에 존재하지 않습니다.")

        #  item_id가 item2id에 존재하는 데이터만 필터링
        filtered_df = self.book_df[self.book_df['item_id'].isin(self.item2id)].reset_index(drop=True)

        with torch.no_grad():
            user_indices = [self.user2id[user_id]] * len(filtered_df)
            item_indices = [self.item2id[i] for i in filtered_df['item_id']]

            user_tensor = torch.tensor(user_indices, dtype=torch.long).to(self.device)
            item_tensor = torch.tensor(item_indices, dtype=torch.long).to(self.device)

            #  NCF 점수 계산
            ncf_scores = self.ncf_model(user_tensor, item_tensor).cpu().numpy()

        #  사용자 리뷰 임베딩
        review_embedding = self.embedder.encode(user_review, convert_to_tensor=True, device=self.device)

        #  책 설명 필터링에 맞게 임베딩도 맞춤
        filtered_embeddings = self.book_embeddings[self.book_df['item_id'].isin(self.item2id)]

        #  유사도 계산
        sim_scores = util.pytorch_cos_sim(review_embedding, filtered_embeddings)[0].cpu().numpy()

        #  점수 조합
        final_scores = self.alpha * ncf_scores + (1 - self.alpha) * sim_scores

        #  추천 상위 K개
        top_indices = final_scores.argsort()[-top_k:][::-1]
        recommendations = [
            (filtered_df.iloc[i]['item_id'], filtered_df.iloc[i]['title'])
            for i in top_indices
        ]

        return recommendations

# ============================
# 외부에서 사용할 get_recommendations 함수
# ============================

# 디바이스 설정
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 1. 데이터 불러오기
book_df = pd.read_csv("sarak_reviews_100users.csv")
desc_df = pd.read_csv("book_descriptions.csv")
# debugging------------
print("book_df columns:", book_df.columns.tolist())
print("desc_df columns:", desc_df.columns.tolist())
# debug end------------


#기존 오류 코드 이하 한줄
#book_df = book_df.merge(desc_df, on="item_id", how="left")

# 수정 (공통 컬럼 '책 제목' 기준 병합)
book_df = book_df.merge(desc_df, on="책 제목", how="left")

# 병합 후 '책 제목'을 고유 ID로 사용
book_df['item_id'] = book_df['책 제목']
book_df['title'] = book_df['책 제목']
book_df['description'] = book_df['소개글']
book_df['rating'] = book_df['별점']


# 2. 매핑 불러오기
user2id = torch.load("user2id.pt")
item2id = torch.load("item2id.pt")
id2item = {v: k for k, v in item2id.items()}

# 3. 모델 로딩
num_users = len(user2id)
num_items = len(item2id)
ncf_model = NCF(num_users, num_items)
ncf_model.load_state_dict(torch.load("ncf_model.pt", map_location=device))
ncf_model.to(device)
ncf_model.eval()

# 4. 임베딩 모델 로딩
kobert_model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS', device=device)

# 5. 추천기 초기화
recommender = HybridRecommender(ncf_model, book_df, user2id, item2id, id2item, kobert_model)

# 6. 외부 호출용 함수
def get_recommendations(user_id, user_review='', top_k=5):
    return recommender.recommend(user_id, user_review, top_k)
