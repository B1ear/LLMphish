import os
from pathlib import Path
from typing import List

import joblib
from sklearn.ensemble import IsolationForest

from app.analysis import extract_traditional_features, build_feature_vector


def load_emails_from_dir(data_dir: str) -> List[str]:
    base = Path(data_dir)
    contents: List[str] = []
    for p in base.glob("*.eml"):
        try:
            raw = p.read_bytes()
            text = raw.decode("utf-8", errors="ignore")
            contents.append(text)
        except Exception:
            continue
    return contents


def main():
    # 训练数据目录：只包含垃圾/钓鱼邮件，视为“异常类”
    data_dir = os.environ.get(
        "LLMPHISH_TRAIN_DIR",
        r"C:\Users\Zeus\Desktop\LLMPhish\datacon2023-spoof-email-main",
    )

    emails = load_emails_from_dir(data_dir)
    if not emails:
        print(f"未在目录中加载到有效邮件：{data_dir}")
        return

    print(f"共加载邮件 {len(emails)} 封，开始提取特征...")
    X = []
    for content in emails:
        feats = extract_traditional_features(content)
        vec = build_feature_vector(feats)
        X.append(vec)

    print("训练 IsolationForest 一类模型（仅基于钓鱼/垃圾邮件）...")
    clf = IsolationForest(
        n_estimators=200,
        contamination=0.1,
        random_state=42,
    )
    clf.fit(X)

    # 在 backend 目录下运行时，模型目录应为 backend/models
    model_dir = Path("models")
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "phish_iforest.joblib"
    joblib.dump(clf, model_path)
    print(f"模型已保存到: {model_path}")


if __name__ == "__main__":
    main()


