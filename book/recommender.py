from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np


class HybridRecommender:
    def __init__(self, ncf_model, book_df, user2id, item2id, id2item, kobert_model, alpha=0.7):
        self.ncf_model = ncf_model
        self.book_df = book_df
        self.user2id = user2id
        self.item2id = item2id
        self.id2item = id2item
        self.kobert_model = kobert_model
        self.alpha = alpha
        self.device = next(ncf_model.parameters()).device  # ncf 모델이 위치한 디바이스 확인
        self.embedder = SentenceTransformer('jhgan/ko-sbert-sts')

        # 책 임베딩 생성 (책 설명에 대한 임베딩)
        print("책 설명 임베딩 중...")
        self.book_embeddings = kobert_model.encode(book_df['description'].fillna("").tolist(), convert_to_tensor=True,
                                                   device=self.device)

    def recommend(self, user_id, user_review, top_k=5):
        self.ncf_model.eval()
        with torch.no_grad():
            # 사용자 및 아이템 인덱스 준비
            user_indices = [self.user2id[user_id]] * len(self.book_df)
            item_indices = list(self.book_df['item_id'].map(self.item2id.get))

            # 사용자 및 아이템 인덱스를 텐서로 변환하고, 디바이스로 이동
            user_tensor = torch.tensor(user_indices).to(self.device)
            item_tensor = torch.tensor(item_indices).to(self.device)

            # NCF 모델을 사용하여 예측 점수 계산
            ncf_scores = self.ncf_model(user_tensor, item_tensor).cpu().numpy()  # CPU로 이동 후 NumPy로 변환

        # 사용자 리뷰 임베딩 계산 (KoBERT 모델 사용)
        review_embedding = self.embedder.encode(user_review, convert_to_tensor=True, device=self.device)

        # 문장 유사도 계산 (Cosine similarity)
        sim_scores = util.pytorch_cos_sim(review_embedding, self.book_embeddings)[0].cpu().numpy()

        # 최종 점수 계산 (NCF 점수와 유사도 점수의 결합)
        final_scores = self.alpha * ncf_scores + (1 - self.alpha) * sim_scores

        # 상위 K개의 추천 아이템 선택
        top_indices = final_scores.argsort()[-top_k:][::-1]
        recommendations = [(self.book_df.iloc[i]['item_id'], self.book_df.iloc[i]['title']) for i in top_indices]

        return recommendations

