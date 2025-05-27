# recommender_core.py
def get_recommendations(user_id='흙속에저바람속에', top_k=5):
    import torch
    import pandas as pd
    import pickle
    from sentence_transformers import SentenceTransformer

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # CSV 파일 로딩 (이 경로는 프로젝트 기준으로 조정)
    review_path = 'sarak_reviews_100users.csv'
    desc_path = 'book_descriptions.csv'

    book_df = pd.read_csv(review_path)
    desc_df = pd.read_csv(desc_path)

    book_df['item_id'] = book_df['책 제목']
    desc_df.rename(columns={'책 제목': 'item_id'}, inplace=True)
    book_df = book_df.merge(desc_df, on='item_id', how='left')

    book_df['rating'] = pd.to_numeric(book_df['별점'], errors='coerce').fillna(0).astype(float)
    book_df['review'] = book_df['리뷰']
    book_df['user_id'] = book_df['작성자']

    # 모델 및 ID 매핑 로딩
    user2id = torch.load('user2id.pt')
    item2id = torch.load('item2id.pt')
    id2item = {v: k for k, v in item2id.items()}

    from model import NCF
    ncf_model = NCF(num_users=len(user2id), num_items=len(item2id))
    ncf_model.load_state_dict(torch.load('ncf_model.pt', map_location=device))
    ncf_model.eval()

    kobert_model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS', device='cpu')
    with open('book_embeddings.pkl', 'rb') as f:
        book_embeddings = pickle.load(f)

    from recommender import HybridRecommender
    recommender = HybridRecommender(
        ncf_model=ncf_model,
        book_df=book_df,
        user2id=user2id,
        item2id=item2id,
        id2item=id2item,
        kobert_model=kobert_model,
        alpha=0.7
    )

    user_reviews = book_df[book_df['user_id'] == user_id]['리뷰'].tolist()
    user_review = " ".join([str(r) for r in user_reviews if r]) if user_reviews else ""
    results = recommender.recommend(user_id, user_review, top_k)

    return results  # [(item_id, title), ...]
