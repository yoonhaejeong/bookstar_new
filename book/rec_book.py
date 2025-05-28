import os
import torch
import pandas as pd
import pickle
import gc
from sentence_transformers import SentenceTransformer
from model import NCF  # 직접 만든 NCF 모델 클래스
from train_ncf import train_ncf_model  # NCF 학습 함수
from recommender import HybridRecommender  # 우리가 만든 추천 클래스

# CUDA 가용성 확인
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"사용 중인 디바이스: {device}")

# 1. 데이터 로드
review_path = 'sarak_reviews_100users.csv'
desc_path = 'book_descriptions.csv'

if not os.path.exists(review_path):
    raise FileNotFoundError(f"{review_path} 파일이 존재하지 않습니다.")
if not os.path.exists(desc_path):
    raise FileNotFoundError(f"{desc_path} 파일이 존재하지 않습니다.")

book_df = pd.read_csv(review_path)
desc_df = pd.read_csv(desc_path)
print(book_df.columns)  # book_df 열 확인
print(desc_df.columns)  # desc_df 열 확인

# 사용자 ID 확인 및 출력 - 디버깅용
print("데이터셋의 사용자 ID 샘플(최대 10개):", book_df['user_id'].unique()[:10].tolist())
total_users = len(book_df['user_id'].unique())
print(f"총 사용자 수: {total_users}")

# 2. 책 설명 병합 (item_id 기준)
book_df = book_df.merge(desc_df, on='item_id', how='left')
print(book_df.columns)

# 3. 사용자/아이템 ID 매핑
if os.path.exists('user2id.pt') and os.path.exists('item2id.pt'):
    user2id = torch.load('user2id.pt')
    item2id = torch.load('item2id.pt')
    id2item = {v: k for k, v in item2id.items()}
else:
    user2id = {uid: idx for idx, uid in enumerate(book_df['user_id'].unique())}
    item2id = {iid: idx for idx, iid in enumerate(book_df['item_id'].unique())}
    id2item = {v: k for k, v in item2id.items()}
    torch.save(user2id, 'user2id.pt')
    torch.save(item2id, 'item2id.pt')

# 4. NCF 모델 로딩 또는 학습 (state_dict 방식)
num_users = len(user2id)
num_items = len(item2id)
ncf_model = NCF(num_users=num_users, num_items=num_items)
ncf_model.to(device)

if os.path.exists('ncf_model.pt'):
    print("저장된 NCF 모델 불러오는 중...")
    state_dict = torch.load('ncf_model.pt', map_location=device)  # 적절한 디바이스에 로드
    ncf_model.load_state_dict(state_dict)
    ncf_model.eval()
    print("NCF 모델 로드 완료.")
else:
    print("NCF 모델 학습 중...")
    book_df['rating'] = pd.to_numeric(book_df['rating'], errors='coerce').fillna(0).astype(float)
    ncf_model = train_ncf_model(book_df, user2id, item2id)
    torch.save(ncf_model.state_dict(), 'ncf_model.pt')  # state_dict 저장
    print("NCF 모델 저장 완료.")

# 5. 임베딩 생성 - 캐싱 활용해 속도 향상
embeddings_cache_path = 'book_embeddings.pkl'

# KoBERT 모델 로드
print("KoBERT 모델 로드 중...")
kobert_model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-augSTS', device='cpu')

# 캐시된 임베딩이 있는지 확인
if os.path.exists(embeddings_cache_path):
    print("저장된 임베딩 불러오는 중...")
    with open(embeddings_cache_path, 'rb') as f:
        book_embeddings = pickle.load(f)
    print(f"임베딩 로드 완료: {book_embeddings.shape}")
else:
    print("책 설명 임베딩 생성 중...")

    # 메모리 정리
    torch.cuda.empty_cache()
    gc.collect()

    if 'description' not in book_df.columns:
        raise KeyError("'description' 열이 book_df에 없습니다.")

    # 텍스트 전처리 - 임베딩 속도 개선
    import re


    def clean_text(text):
        if not isinstance(text, str):
            return ""
        text = re.sub(r'\s+', ' ', text)  # 중복 공백 제거
        return text.strip()[:512]  # 길이 제한


    descriptions = [clean_text(desc) for desc in book_df['description'].fillna("")]

    # 진행 상황 표시와 함께 배치 처리
    book_embeddings = []
    batch_size = 32  # 배치 크기 증가

    for i in range(0, len(descriptions), batch_size):
        end_idx = min(i + batch_size, len(descriptions))
        batch = descriptions[i:end_idx]

        # 진행률 표시
        print(f"임베딩 진행률: {i}/{len(descriptions)} ({i / len(descriptions) * 100:.1f}%)")

        # 임베딩 생성
        with torch.no_grad():
            embeddings = kobert_model.encode(batch, convert_to_tensor=True).detach().cpu()

        book_embeddings.append(embeddings)

        # 주기적 메모리 정리
        if i % 320 == 0 and i > 0:
            gc.collect()

    # 모든 임베딩 합치기
    book_embeddings = torch.cat(book_embeddings, dim=0)

    # 임베딩 캐시 저장
    print(f"임베딩 저장 중... 크기={book_embeddings.shape}")
    with open(embeddings_cache_path, 'wb') as f:
        pickle.dump(book_embeddings, f)

    print("임베딩 생성 및 저장 완료!")

# 메모리 정리
torch.cuda.empty_cache()

# 중요: title 열 추가 (KeyError 해결)
if 'title' not in book_df.columns:
    print("'title' 열이 없습니다. 제목 정보를 생성합니다.")

    # 옵션 1: 다른 열의 데이터를 활용하여 더 의미 있는 제목 생성
    if '저자/역자' in book_df.columns:
        # 저자/역자 정보를 포함한 제목 생성
        book_df['title'] = book_df.apply(
            lambda row: f"도서 {row['item_id']} (저자: {row['저자/역자']})"
            if pd.notna(row['저자/역자']) else f"도서 {row['item_id']}",
            axis=1
        )
        print("'저자/역자' 정보를 포함한 'title' 열을 생성했습니다.")
    else:
        # 기본 제목 생성
        book_df['title'] = book_df['item_id'].astype(str).apply(lambda x: f"도서 {x}")
        print("'item_id'를 기반으로 'title' 열을 생성했습니다.")

# 6. 추천 시스템 초기화
recommender = HybridRecommender(
    ncf_model=ncf_model,
    book_df=book_df,
    user2id=user2id,
    item2id=item2id,
    id2item=id2item,
    kobert_model=kobert_model,
    alpha=0.7
)

# 7. 추천 수행
# 원래 코드에서는 'icdatig' 사용자 ID를 사용했지만, 이미 데이터셋에 있음을 확인
user_id = '흙속에저바람속에'  # 추천할 사용자 ID
print(f"추천에 사용할 사용자 ID: {user_id}")

# 사용자 리뷰 가져오기
user_reviews = book_df[book_df['user_id'] == user_id]['리뷰'].tolist()
if not user_reviews:
    print(f"사용자 {user_id}의 리뷰를 찾을 수 없습니다. 빈 문자열을 사용합니다.")
    user_review = ""
else:
    # 모든 사용자 리뷰를 하나의 문자열로 결합
    user_review = " ".join([str(review) for review in user_reviews if review is not None])
    if len(user_review) > 100:
        print(f"사용자 리뷰 샘플: {user_review[:100]}...")
    else:
        print(f"사용자 리뷰: {user_review}")

try:
    # 추천 실행
    recommendations = recommender.recommend(user_id, user_review, top_k=5)

    # 8. 결과 출력
    print(f"\n사용자 {user_id}에게 추천하는 책:")
    for i, (item_id, title) in enumerate(recommendations, 1):
        print(f"{i}. {title} (ID: {item_id})")
except Exception as e:
    import traceback

    print(f"추천 생성 중 오류 발생: {str(e)}")
    print("상세 오류 정보:")
    print(traceback.format_exc())

    # 문제 진단 정보 제공
    print("\n문제 진단 정보:")
    print(f"book_df 열: {book_df.columns.tolist()}")
    print(f"user_id '{user_id}'가 데이터셋에 존재하는지: {user_id in book_df['user_id'].values}")
    print(f"user2id 매핑에 '{user_id}'가 존재하는지: {user_id in user2id}")

    # 다른 사용자 시도 제안
    if user_id not in user2id and len(book_df['user_id'].unique()) > 0:
        alt_user = book_df['user_id'].unique()[0]
        print(f"\n대체 사용자 ID '{alt_user}'로 다시 시도해보세요.")