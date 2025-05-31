import torch 
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
from model import NCF

class RatingDataset(Dataset):
    def __init__(self, df, user2id, item2id):
        self.user_tensor = torch.tensor([user2id[u] for u in df['user_id']], dtype=torch.long)
        self.item_tensor = torch.tensor([item2id[i] for i in df['item_id']], dtype=torch.long)
        self.rating_tensor = torch.tensor(df['rating'].values, dtype=torch.float)

    def __len__(self):
        return len(self.user_tensor)

    def __getitem__(self, idx):
        return self.user_tensor[idx], self.item_tensor[idx], self.rating_tensor[idx]

def train_ncf_model(df, user2id, item2id, epochs=5, batch_size=256, lr=0.001):
    dataset = RatingDataset(df, user2id, item2id)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = NCF(num_users=len(user2id), num_items=len(item2id))
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for user, item, rating in dataloader:
            optimizer.zero_grad()
            pred = model(user, item)
            loss = criterion(pred, rating)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}/{epochs} | Loss: {total_loss:.4f}")

    return model

# 🚀 실행 진입점
if __name__ == "__main__":
    # 🗂️ 데이터 로드 (파일명에 맞게 조정)
    df = pd.read_csv("sarak_reviews_100users.csv")

    # 🧠 매핑 준비
    user2id = {u: i for i, u in enumerate(df['user_id'].unique())}
    item2id = {i: j for j, i in enumerate(df['item_id'].unique())}

    # 💪 학습
    model = train_ncf_model(df, user2id, item2id)

    # 💾 저장
    torch.save(user2id, "user2id.pt")
    torch.save(item2id, "item2id.pt")
    torch.save(model.state_dict(), "ncf_model.pt")
    print("✅ 모델 및 매핑 저장 완료: ncf_model.pt, user2id.pt, item2id.pt")
