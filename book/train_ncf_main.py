import pandas as pd
import torch
from train_ncf import train_ncf_model  # 같은 폴더에 train_ncf.py 있어야 함

# 1. 데이터 로딩
df = pd.read_csv("sarak_reviews_100users.csv")

# 2. 컬럼 매핑
df['user_id'] = df['작성자']
df['item_id'] = df['책 제목']
df['rating'] = pd.to_numeric(df['별점'], errors='coerce')  # <-- 이 줄 수정!

# 결측치 제거 (변환 실패한 값 제거)
df = df.dropna(subset=['rating'])


# 3. ID 매핑 딕셔너리 생성
user2id = {u: i for i, u in enumerate(df['user_id'].unique())}
item2id = {i: j for j, i in enumerate(df['item_id'].unique())}

# 4. 모델 학습
model = train_ncf_model(df, user2id, item2id, epochs=10, batch_size=256, lr=0.001)

# 5. 저장
torch.save(model.state_dict(), "ncf_model.pt")
torch.save(user2id, "user2id.pt")
torch.save(item2id, "item2id.pt")

print("✅ 모델 및 매핑 정보 저장 완료!")
