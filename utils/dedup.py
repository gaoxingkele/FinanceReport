"""
去重工具 - 源自FinRpt的去重逻辑

提供:
1. MinHash LSH 去重 (快速近似)
2. BERT语义去重 (精确)
3. 哈希精确去重
"""
import hashlib
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


def hash_dedup(items: List[Dict[str, Any]], key: str = "title") -> List[Dict[str, Any]]:
    """基于MD5哈希的精确去重"""
    seen = set()
    result = []
    for item in items:
        text = item.get(key, "").strip()
        if not text:
            continue
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        if h not in seen:
            seen.add(h)
            result.append(item)
    return result


def jaccard_dedup(
    items: List[Dict[str, Any]],
    key: str = "title",
    threshold: float = 0.85,
) -> List[Dict[str, Any]]:
    """基于Jaccard相似度的模糊去重"""
    result = []
    for item in items:
        text = item.get(key, "").strip()
        is_dup = False
        for existing in result:
            existing_text = existing.get(key, "")
            sim = _jaccard_char(text, existing_text)
            if sim > threshold:
                is_dup = True
                break
        if not is_dup:
            result.append(item)
    return result


def minhash_dedup(
    items: List[Dict[str, Any]],
    key: str = "content",
    threshold: float = 0.3,
    num_perm: int = 128,
) -> List[Dict[str, Any]]:
    """
    基于MinHash LSH的近似去重 (源自FinRpt)

    使用datasketch库进行高效近似去重
    """
    try:
        from datasketch import MinHash, MinHashLSH

        lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        result = []
        minhashes = {}

        for i, item in enumerate(items):
            text = item.get(key, "").strip()
            if not text:
                continue

            # 创建MinHash
            m = MinHash(num_perm=num_perm)
            for word in _tokenize(text):
                m.update(word.encode("utf-8"))

            # 查询是否有近似重复
            try:
                matches = lsh.query(m)
                if not matches:
                    lsh.insert(str(i), m)
                    result.append(item)
                    minhashes[str(i)] = m
            except Exception:
                result.append(item)

        return result

    except ImportError:
        logger.warning("datasketch未安装，回退到Jaccard去重")
        return jaccard_dedup(items, key, threshold=0.7)


def bert_dedup(
    items: List[Dict[str, Any]],
    key: str = "title",
    threshold: float = 0.85,
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
) -> List[Dict[str, Any]]:
    """
    基于BERT语义相似度的去重 (源自FinRpt)

    使用sentence-transformers计算语义相似度
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        texts = [item.get(key, "") for item in items]
        if not texts:
            return items

        model = SentenceTransformer(model_name)
        embeddings = model.encode(texts, show_progress_bar=False)

        result = []
        result_embeddings = []

        for i, (item, emb) in enumerate(zip(items, embeddings)):
            is_dup = False
            for existing_emb in result_embeddings:
                sim = np.dot(emb, existing_emb) / (
                    np.linalg.norm(emb) * np.linalg.norm(existing_emb)
                )
                if sim > threshold:
                    is_dup = True
                    break
            if not is_dup:
                result.append(item)
                result_embeddings.append(emb)

        return result

    except ImportError:
        logger.warning("sentence-transformers未安装，回退到Jaccard去重")
        return jaccard_dedup(items, key, threshold=threshold)


def _jaccard_char(s1: str, s2: str) -> float:
    """字符级Jaccard相似度"""
    set1 = set(s1)
    set2 = set(s2)
    if not set1 and not set2:
        return 1.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def _tokenize(text: str) -> List[str]:
    """简单分词 (用于MinHash)"""
    # 对中文按字符，对英文按空格分词
    tokens = []
    current = []
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append(ch)
        elif ch.isalnum():
            current.append(ch)
        else:
            if current:
                tokens.append("".join(current))
                current = []
    if current:
        tokens.append("".join(current))
    return tokens
