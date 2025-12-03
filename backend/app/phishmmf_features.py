"""
PhishMMF 228 维多模态特征提取模块。

基于 json_schema.py 定义的特征结构，从原始邮件文本中尽可能提取特征。
对于需要外部数据源的特征（如图像、URL OSINT、网站HTML），使用合理的默认值占位。

特征结构（228维）：
- text_features: 文本相关特征（主题、发件人、内容）
- url_intelligence_features: URL情报特征
- image_features: 图像特征（占位）
- website_features: 网站特征（占位）
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from app.analysis import (
    URL_PATTERN,
    EMAIL_PATTERN,
    ANCHOR_PATTERN,
    SUSPICIOUS_KEYWORDS,
    BRAND_KEYWORDS,
    _extract_subject,
    _extract_sender_domain,
    _extract_auth_results,
    _has_html,
)


# 紧急词汇列表
URGENCY_WORDS = [
    "urgent", "immediate", "asap", "now", "today", "expire", "expired",
    "expiring", "limited", "act now", "click now", "verify now",
    "紧急", "立即", "马上", "过期", "限时", "立即处理"
]

# 威胁性语言关键词
THREATENING_LANGUAGE = [
    "suspend", "close", "terminate", "lock", "block", "freeze",
    "suspend", "cancel", "deactivate", "restrict",
    "冻结", "锁定", "关闭", "暂停", "取消"
]

# 诱惑性语言关键词
SEDUCTIVE_LANGUAGE = [
    "free", "bonus", "reward", "prize", "win", "congratulations",
    "exclusive", "special offer", "discount", "save",
    "免费", "奖励", "奖品", "恭喜", "特价", "优惠"
]

# 个人信息请求关键词
PERSONAL_INFO_KEYWORDS = [
    "ssn", "social security", "credit card", "card number", "cvv", "pin",
    "password", "account number", "routing number", "date of birth",
    "身份证", "银行卡", "密码", "账号", "身份证号"
]

# 金融请求关键词
FINANCIAL_REQUEST_KEYWORDS = [
    "wire transfer", "bitcoin", "cryptocurrency", "payment", "refund",
    "invoice", "transaction", "account balance",
    "转账", "支付", "退款", "交易", "余额"
]


def _count_keywords(text: str, keywords: List[str]) -> int:
    """统计文本中关键词出现次数"""
    lower_text = text.lower()
    count = 0
    for kw in keywords:
        if kw.lower() in lower_text:
            count += 1
    return count


def _extract_urgency_level(subject: str) -> str:
    """提取主题紧急程度"""
    if not subject:
        return "unknown"
    lower_subj = subject.lower()
    urgency_count = _count_keywords(lower_subj, URGENCY_WORDS)
    if urgency_count >= 2:
        return "High"
    elif urgency_count == 1:
        return "Moderate"
    else:
        return "Low"


def _extract_sentiment_score(text: str) -> float:
    """
    简单情感得分：基于正面/负面词汇比例
    返回 [-1, 1]，1 为最正面，-1 为最负面
    """
    positive_words = ["good", "great", "excellent", "thank", "welcome", "恭喜", "感谢"]
    negative_words = ["urgent", "suspend", "close", "error", "warning", "紧急", "错误", "警告"]
    
    lower_text = text.lower()
    pos_count = sum(1 for w in positive_words if w in lower_text)
    neg_count = sum(1 for w in negative_words if w in lower_text)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    return (pos_count - neg_count) / max(total, 1)


def _extract_sentiment_label(text: str) -> str:
    """提取情感标签"""
    score = _extract_sentiment_score(text)
    if score > 0.2:
        return "Positive"
    elif score < -0.2:
        return "Negative"
    else:
        return "Neutral"


def _extract_impersonation_type(content: str, sender_domain: Optional[str]) -> str:
    """检测冒充类型"""
    lower_content = content.lower()
    brand_hits = {kw: kw.lower() in lower_content for kw in BRAND_KEYWORDS}
    
    if any(brand_hits.values()):
        # 检查是否与发件人域名匹配
        if sender_domain:
            for brand in BRAND_KEYWORDS:
                if brand.lower() in lower_content and brand.lower() not in sender_domain.lower():
                    return "brand_impersonation"
        return "potential_brand_impersonation"
    
    # 检查其他类型
    if any(kw in lower_content for kw in ["government", "irs", "tax", "政府", "税务"]):
        return "government_entity"
    if any(kw in lower_content for kw in ["bank", "financial", "银行", "金融"]):
        return "financial_institution"
    if any(kw in lower_content for kw in ["cloud", "microsoft", "google", "amazon"]):
        return "cloud_service"
    
    return "unknown"


def _extract_email_anomalies(sender_email: str, sender_domain: Optional[str]) -> str:
    """检测发件人邮箱异常"""
    if not sender_email:
        return "unknown"
    
    # 检查随机字符
    if re.search(r'[a-z]{10,}', sender_email.lower()):
        if len(re.findall(r'[a-z]', sender_email)) > 15:
            return "randomized_characters"
    
    # 检查域名不匹配（需要与已知品牌对比，这里简化处理）
    if sender_domain and any(brand in sender_email.lower() for brand in BRAND_KEYWORDS):
        brand_in_email = [b for b in BRAND_KEYWORDS if b.lower() in sender_email.lower()]
        if brand_in_email and not any(b.lower() in sender_domain.lower() for b in brand_in_email):
            return "domain_mismatch_with_known_brand"
    
    # 检查可疑子域名
    if sender_domain and sender_domain.count('.') > 2:
        return "complex_subdomain"
    
    return "none"


def _extract_url_features(url: str) -> Dict[str, Any]:
    """从单个URL提取特征"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        # 基本特征
        domain_length = len(domain)
        dot_count = domain.count('.')
        contains_ip = bool(re.match(r'^\d+\.\d+\.\d+\.\d+', domain))
        contains_at = '@' in url
        contains_hyphen = '-' in domain
        path_length = len(parsed.path)
        subdomains_count = domain.count('.') - 1 if '.' in domain else 0
        tld = domain.split('.')[-1] if '.' in domain else "unknown"
        
        # 查询参数
        query_params = parse_qs(parsed.query)
        query_params_count = len(query_params)
        suspicious_params = [k for k in query_params.keys() if len(k) < 3 or 'id' in k.lower() or 'token' in k.lower()]
        has_suspicious_params = len(suspicious_params) > 0
        
        return {
            "domain_length": domain_length,
            "dot_count": dot_count,
            "contains_ip_address": contains_ip,
            "contains_at_symbol": contains_at,
            "contains_hyphen": contains_hyphen,
            "path_length": path_length,
            "subdomains_count": max(0, subdomains_count),
            "tld": tld,
            "query_params_count": query_params_count,
            "has_suspicious_query_params": has_suspicious_params,
            "suspicious_query_params": suspicious_params,
        }
    except Exception:
        return {
            "domain_length": 0,
            "dot_count": 0,
            "contains_ip_address": False,
            "contains_at_symbol": False,
            "contains_hyphen": False,
            "path_length": 0,
            "subdomains_count": 0,
            "tld": "unknown",
            "query_params_count": 0,
            "has_suspicious_query_params": False,
            "suspicious_query_params": [],
        }


def extract_image_features_from_bytes(image_bytes: Optional[bytes]) -> List[float]:
    """
    从图像字节数据提取 PhishMMF 图像特征（约 20 维）。
    
    特征包括：
    - layout: contains_login_form, contains_bank_card_input, form_present, login_form_detected, element_complexity
    - visual_similarity: logo_similarity, favicon_matches_brand, brand_visual_similarity, visual_similarity_score, brand_mismatch, suspicious_ui_layout
    - risk_elements: suspicious_links, contains_suspicious_popup, suspicious_visual_elements, visual_phishing_risk, image_text_keywords
    """
    if not image_bytes or not PIL_AVAILABLE:
        # 无图像数据时返回占位值
        return [0.0] * 20
    
    try:
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        
        # 转换为RGB（如果是RGBA或其他格式）
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 简化特征提取：基于图像尺寸、颜色分布等
        # layout 特征（5维）
        # 简化：基于图像尺寸和颜色复杂度推测是否有表单
        aspect_ratio = width / max(height, 1)
        has_form_like_layout = 1.0 if 0.5 < aspect_ratio < 2.0 and width > 400 else 0.0
        features = [
            has_form_like_layout,  # contains_login_form
            0.0,  # contains_bank_card_input (需要OCR，简化处理)
            has_form_like_layout,  # form_present
            has_form_like_layout,  # login_form_detected
            min(1.0, (width * height) / 1000000.0),  # element_complexity (基于像素数)
        ]
        
        # visual_similarity 特征（6维）
        # 简化：基于颜色分布和图像复杂度
        pixels = list(img.getdata())
        if pixels:
            # 计算颜色多样性（简化指标）
            unique_colors = len(set(pixels[:1000]))  # 采样前1000像素
            color_diversity = min(1.0, unique_colors / 100.0)
        else:
            color_diversity = 0.0
        
        features.extend([
            color_diversity,  # logo_similarity_to_known_brands (占位)
            0.0,  # favicon_matches_brand (需要品牌库对比)
            color_diversity,  # brand_visual_similarity
            color_diversity,  # visual_similarity_score
            0.0,  # brand_mismatch (需要品牌库对比)
            0.0,  # suspicious_ui_layout (需要布局分析)
        ])
        
        # risk_elements 特征（5维）
        # 简化：基于图像尺寸和颜色特征
        is_small_image = 1.0 if width < 300 or height < 300 else 0.0
        features.extend([
            0.0,  # suspicious_links (需要OCR)
            0.0,  # contains_suspicious_popup (需要布局分析)
            float(is_small_image),  # suspicious_visual_elements (简化)
            float(is_small_image * 0.5),  # visual_phishing_risk
            0.0,  # image_text_keywords (需要OCR)
        ])
        
        # 确保正好 20 维
        while len(features) < 20:
            features.append(0.0)
        
        return features[:20]
    except Exception:
        # 图像处理失败时返回占位值
        return [0.0] * 20


def extract_phishmmf_features_228d(content: str, image_bytes: Optional[bytes] = None) -> List[float]:
    """
    从邮件文本提取 PhishMMF 228 维特征向量。
    
    返回: 228 维浮点数列表，按 json_schema 定义的顺序排列。
    """
    # 提取基础信息
    subject = _extract_subject(content) or ""
    sender_domain = _extract_sender_domain(content)
    urls = URL_PATTERN.findall(content)
    auth_results = _extract_auth_results(content)
    
    lower_content = content.lower()
    words = content.split()
    word_count = len(words)
    
    # ========== text_features (约 30+ 维) ==========
    features = []
    
    # subject 特征
    urgency_level = _extract_urgency_level(subject)
    urgency_map = {"High": 2, "Moderate": 1, "Low": 0, "unknown": 0}
    features.append(float(urgency_map.get(urgency_level, 0)))
    
    features.append(1.0 if _count_keywords(subject, THREATENING_LANGUAGE) > 0 else 0.0)
    features.append(1.0 if _count_keywords(subject, SEDUCTIVE_LANGUAGE) > 0 else 0.0)
    features.append(1.0 if _count_keywords(subject, URGENCY_WORDS) > 0 else 0.0)
    features.append(_extract_sentiment_score(subject))
    sentiment_label = _extract_sentiment_label(subject)
    sentiment_map = {"Positive": 1, "Neutral": 0, "Negative": -1, "unknown": 0}
    features.append(float(sentiment_map.get(sentiment_label, 0)))
    
    # sender 特征
    impersonation_type = _extract_impersonation_type(content, sender_domain)
    # 简化：将冒充类型映射为数值（0=unknown, 1=potential, 2=confirmed）
    impersonation_score = 2.0 if "impersonation" in impersonation_type else (1.0 if "potential" in impersonation_type else 0.0)
    features.append(impersonation_score)
    
    email_anomalies = _extract_email_anomalies("", sender_domain)  # 简化：不解析完整邮箱
    anomaly_score = 1.0 if email_anomalies != "none" and email_anomalies != "unknown" else 0.0
    features.append(anomaly_score)
    
    # 发件人信誉分（简化：基于域名长度和结构）
    sender_reputation = 1.0 if sender_domain and len(sender_domain.split('.')) == 2 else 0.5
    features.append(sender_reputation)
    
    # 域名与品牌相似度（简化：基于关键词匹配）
    brand_similarity = 1.0 if any(brand.lower() in (sender_domain or "").lower() for brand in BRAND_KEYWORDS) else 0.0
    features.append(brand_similarity)
    
    # content 特征
    features.append(float(word_count))
    features.append(float(len(urls)))
    
    # 拼写/语法错误（简化：基于常见错误模式）
    spelling_errors = len(re.findall(r'\b\w{15,}\b', content))  # 超长单词
    features.append(float(spelling_errors))
    grammar_errors = len(re.findall(r'\s+[a-z]', content))  # 简化：小写字母开头（可能缺少大写）
    features.append(float(min(grammar_errors, 45)))
    
    # 可疑关键词数量
    suspicious_kw_count = _count_keywords(content, SUSPICIOUS_KEYWORDS)
    features.append(float(suspicious_kw_count))
    
    features.append(float(_count_keywords(content, URGENCY_WORDS)))
    features.append(1.0 if _count_keywords(content, PERSONAL_INFO_KEYWORDS) > 0 else 0.0)
    features.append(1.0 if _count_keywords(content, FINANCIAL_REQUEST_KEYWORDS) > 0 else 0.0)
    
    # 文本复杂度（简化：基于平均词长）
    avg_word_len = sum(len(w) for w in words) / max(word_count, 1)
    text_complexity = min(100.0, avg_word_len * 10)
    features.append(text_complexity)
    
    # 与合法邮件相似度（占位：0.5）
    features.append(0.5)
    
    # 语言检测（简化：0=英文, 1=中文, 0.5=混合）
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', content))
    has_english = bool(re.search(r'[a-zA-Z]', content))
    language_code = 0.5 if (has_chinese and has_english) else (1.0 if has_chinese else 0.0)
    features.append(language_code)
    
    features.append(1.0 if re.search(r'[0-9]{4,}', content) else 0.0)  # 模糊化文本（数字替换）
    features.append(1.0 if "otp" in lower_content or "mfa" in lower_content or "验证码" in content else 0.0)
    features.append(1.0 if _count_keywords(content, ["click", "here", "now", "立即", "点击"]) > 0 else 0.0)
    
    content_sentiment = _extract_sentiment_label(content)
    features.append(float(sentiment_map.get(content_sentiment, 0)))
    features.append(_extract_sentiment_score(content))
    
    # ========== url_intelligence_features (约 50+ 维) ==========
    if urls:
        # 取第一个URL的特征（或聚合多个URL）
        url_feat = _extract_url_features(urls[0])
        features.append(float(url_feat["domain_length"]))
        features.append(float(url_feat["dot_count"]))
        features.append(1.0 if url_feat["contains_ip_address"] else 0.0)
        features.append(1.0 if url_feat["contains_at_symbol"] else 0.0)
        features.append(1.0 if url_feat["contains_hyphen"] else 0.0)
        features.append(float(url_feat["path_length"]))
        features.append(float(url_feat["subdomains_count"]))
        # TLD 编码（简化：常见TLD映射）
        tld_map = {"com": 1.0, "org": 0.8, "net": 0.8, "edu": 0.9, "gov": 0.9, "unknown": 0.0}
        features.append(tld_map.get(url_feat["tld"], 0.5))
        features.append(float(url_feat["query_params_count"]))
        features.append(1.0 if url_feat["has_suspicious_query_params"] else 0.0)
    else:
        # 无URL时的默认值
        features.extend([0.0] * 11)
    
    # URL 信誉与风险特征（大部分需要外部API，使用占位值）
    features.append(0.0)  # is_blacklisted
    risk_score = 50.0 if urls else 0.0  # 简化：有URL则中等风险
    features.append(risk_score)
    features.append(0.0)  # redirect_count
    features.append(0.0)  # domain_age_days
    features.append(0.0)  # whois_hidden (占位)
    features.append(0.5)  # domain_similarity_score (占位)
    features.append(1.0 if _count_keywords(" ".join(urls), SUSPICIOUS_KEYWORDS) > 0 else 0.0)
    features.append(brand_similarity)  # brand_similarity_score
    features.append(1.0 if urls and urls[0].startswith("https") else 0.0)  # ssl_https
    # ssl_certificate_status: 0=unknown, 1=valid, 2=invalid
    features.append(1.0 if urls and urls[0].startswith("https") else 0.0)
    features.append(1.0 if urls and urls[0].startswith("https") else 0.0)  # ca_trust_score
    features.append(0.0)  # suspicious_subdomains (占位)
    
    # ========== image_features (约 20+ 维) ==========
    # 如果提供了图像数据，则提取图像特征；否则使用占位值
    image_features = extract_image_features_from_bytes(image_bytes)  # 使用传入的图像数据
    features.extend(image_features)
    
    # ========== website_features (约 30+ 维，大部分占位) ==========
    # structure 特征（可以从HTML内容提取部分）
    html_content = content if _has_html(content) else ""
    features.append(float(html_content.count("<form")))
    features.append(float(len(re.findall(r'href=["\']http', html_content, re.IGNORECASE))))
    features.append(float(html_content.count("<script")))
    features.append(float(html_content.count("<iframe")))
    features.append(float(html_content.count("<input")))
    features.append(float(html_content.count('type="hidden"')))
    features.append(1.0 if "<iframe" in html_content else 0.0)
    features.append(1.0 if 'meta http-equiv="refresh"' in html_content.lower() else 0.0)
    
    # content 特征（占位）
    features.extend([0.5, 0.5, 0.0, 0.0, 0.0, 0.0])  # title_url_relevance, content_similarity, etc.
    
    # security 特征
    features.append(1.0 if any(u.startswith("https") for u in urls) else 0.0)
    features.append(1.0 if any(u.startswith("https") for u in urls) else 0.0)  # ssl_certificate_status
    features.append(1.0 if any(u.startswith("https") for u in urls) else 0.0)  # ca_trust_score
    features.extend([0.0, 0.0, 0.0])  # server_location, domain_registration_country, server_country_match_domain
    
    # 确保正好 228 维
    while len(features) < 228:
        features.append(0.0)
    
    return features[:228]


def extract_phishmmf_features_dict(content: str, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    提取 PhishMMF 特征并返回字典格式（便于调试和查看）。
    主要用于开发和调试，实际使用 extract_phishmmf_features_228d 获取向量。
    """
    vec = extract_phishmmf_features_228d(content, image_bytes)
    return {
        "feature_vector_228d": vec,
        "dimension": len(vec),
        "has_image": image_bytes is not None,
        "note": "部分特征（如URL OSINT、网站HTML）使用占位值，实际部署时建议接入真实提取pipeline"
    }

