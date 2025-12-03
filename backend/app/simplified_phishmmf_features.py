"""
简化的 PhishMMF 特征提取（只使用可提取特征）

使用 35 个可以从邮件中直接提取的特征：
- 文本特征：主题 (6) + 发件人 (2) + 正文 (16) = 24 维
- URL 基础特征：11 维

总计：35 维特征
"""

from __future__ import annotations

import re
from typing import List, Dict, Any
from urllib.parse import urlparse
import email
from email import policy
from email.parser import BytesParser


# 可疑关键词列表
SUSPICIOUS_KEYWORDS = [
    # 英文
    "urgent", "verify", "suspended", "locked", "confirm", "update", "click here",
    "act now", "limited time", "expire", "account", "password", "security",
    "winner", "prize", "congratulations", "claim", "refund", "tax",
    # 中文
    "紧急", "验证", "暂停", "锁定", "确认", "更新", "点击这里",
    "立即行动", "限时", "过期", "账户", "密码", "安全",
    "中奖", "奖品", "恭喜", "领取", "退款", "税务",
]

URGENCY_WORDS = [
    "urgent", "immediately", "now", "asap", "hurry", "quick", "fast",
    "紧急", "立即", "马上", "尽快", "赶快",
]

PERSONAL_INFO_KEYWORDS = [
    "social security", "ssn", "credit card", "bank account", "password",
    "pin", "cvv", "date of birth", "driver license",
    "社保", "信用卡", "银行账户", "密码", "身份证",
]

FINANCIAL_KEYWORDS = [
    "wire transfer", "bitcoin", "cryptocurrency", "gift card", "payment",
    "invoice", "refund", "tax", "irs",
    "转账", "比特币", "加密货币", "礼品卡", "付款", "发票", "退款", "税务",
]


def extract_simplified_phishmmf_features(email_content: str) -> List[float]:
    """
    从邮件内容中提取 35 维简化特征
    
    Args:
        email_content: 邮件原始内容（EML格式）
    
    Returns:
        35维特征向量
    """
    # 解析邮件
    msg = BytesParser(policy=policy.default).parsebytes(email_content.encode('utf-8', errors='ignore'))
    
    # 提取基本信息
    subject = msg.get('subject', '')
    from_addr = msg.get('from', '')
    body = _extract_body(msg)
    urls = _extract_urls(body)
    
    features = []
    
    # 1. 文本特征 - 主题 (6维)
    features.extend(_extract_subject_features(subject))
    
    # 2. 文本特征 - 发件人 (2维)
    features.extend(_extract_sender_features(from_addr))
    
    # 3. 文本特征 - 正文 (16维)
    features.extend(_extract_content_features(body, urls))
    
    # 4. URL 基础特征 (11维)
    features.extend(_extract_url_features(urls))
    
    return features


def _extract_body(msg) -> str:
    """提取邮件正文"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    pass
            elif part.get_content_type() == "text/html":
                try:
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    # 简单去除HTML标签
                    body += re.sub(r'<[^>]+>', ' ', html)
                except:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = str(msg.get_payload())
    
    return body


def _extract_urls(text: str) -> List[str]:
    """提取文本中的URL"""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    return urls


def _extract_subject_features(subject: str) -> List[float]:
    """
    提取主题特征 (6维)
    
    Returns:
        [urgency_level, threatening, seductive, emergency, sentiment_score, sentiment_label]
    """
    subject_lower = subject.lower()
    
    # 1. urgency_level (0=Low, 1=Moderate, 2=High)
    urgency_level = 0
    if any(word in subject_lower for word in ["urgent", "immediately", "asap", "紧急", "立即"]):
        urgency_level = 2
    elif any(word in subject_lower for word in ["important", "attention", "notice", "重要", "注意"]):
        urgency_level = 1
    
    # 2. contains_threatening_language
    threatening = any(word in subject_lower for word in [
        "suspend", "lock", "block", "terminate", "legal", "暂停", "锁定", "封禁", "法律"
    ])
    
    # 3. contains_seductive_language
    seductive = any(word in subject_lower for word in [
        "win", "winner", "prize", "free", "gift", "congratulations", "中奖", "奖品", "免费", "礼物"
    ])
    
    # 4. contains_emergency_action_request
    emergency = any(word in subject_lower for word in [
        "verify", "confirm", "update", "act now", "click", "验证", "确认", "更新", "立即行动"
    ])
    
    # 5. sentiment_score (-1 to 1)
    # 简单的情感分析
    positive_words = ["thank", "welcome", "congratulations", "success", "谢谢", "欢迎", "恭喜", "成功"]
    negative_words = ["suspend", "lock", "problem", "issue", "暂停", "锁定", "问题"]
    
    pos_count = sum(1 for word in positive_words if word in subject_lower)
    neg_count = sum(1 for word in negative_words if word in subject_lower)
    
    if pos_count + neg_count > 0:
        sentiment_score = (pos_count - neg_count) / (pos_count + neg_count)
    else:
        sentiment_score = 0.0
    
    # 6. sentiment_label (0=Negative, 1=Neutral, 2=Positive)
    if sentiment_score < -0.3:
        sentiment_label = 0
    elif sentiment_score > 0.3:
        sentiment_label = 2
    else:
        sentiment_label = 1
    
    return [
        float(urgency_level),
        float(threatening),
        float(seductive),
        float(emergency),
        float(sentiment_score),
        float(sentiment_label),
    ]


def _extract_sender_features(from_addr: str) -> List[float]:
    """
    提取发件人特征 (2维)
    
    Returns:
        [impersonation_type, email_address_anomalies]
    """
    from_lower = from_addr.lower()
    
    # 1. impersonation_type (0=None, 1=Bank, 2=Government, 3=E-commerce, 4=Social Media)
    impersonation = 0
    if any(word in from_lower for word in ["bank", "paypal", "visa", "mastercard", "银行"]):
        impersonation = 1
    elif any(word in from_lower for word in ["gov", "irs", "tax", "政府", "税务"]):
        impersonation = 2
    elif any(word in from_lower for word in ["amazon", "ebay", "alibaba", "淘宝", "京东"]):
        impersonation = 3
    elif any(word in from_lower for word in ["facebook", "twitter", "instagram", "微信", "微博"]):
        impersonation = 4
    
    # 2. email_address_anomalies (0=None, 1=Non-official, 2=Spelling error)
    anomaly = 0
    
    # 检查是否使用免费邮箱冒充官方
    free_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "163.com", "qq.com"]
    if impersonation > 0 and any(domain in from_lower for domain in free_domains):
        anomaly = 1
    
    # 检查拼写错误（简单检测）
    if any(pattern in from_lower for pattern in ["paypa1", "amaz0n", "g00gle", "micr0soft"]):
        anomaly = 2
    
    return [float(impersonation), float(anomaly)]


def _extract_content_features(body: str, urls: List[str]) -> List[float]:
    """
    提取正文特征 (16维)
    
    Returns:
        [word_count, url_count, spelling_errors, grammar_errors, suspicious_keywords,
         urgency_words, personal_info_request, financial_request, text_complexity,
         similarity_to_legit, language, obfuscated, otp_request, phishing_cta,
         text_sentiment, text_sentiment_score]
    """
    body_lower = body.lower()
    
    # 1. word_count
    words = re.findall(r'\b\w+\b', body)
    word_count = len(words)
    
    # 2. url_count
    url_count = len(urls)
    
    # 3. spelling_errors (简单检测：重复字母)
    spelling_errors = len(re.findall(r'(\w)\1{2,}', body))
    
    # 4. grammar_errors (简单检测：多个感叹号/问号)
    grammar_errors = len(re.findall(r'[!?]{2,}', body))
    
    # 5. suspicious_keywords
    suspicious_count = sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in body_lower)
    
    # 6. urgency_words_count
    urgency_count = sum(1 for word in URGENCY_WORDS if word in body_lower)
    
    # 7. contains_personal_information_request
    personal_info_request = any(keyword in body_lower for keyword in PERSONAL_INFO_KEYWORDS)
    
    # 8. contains_abnormal_financial_request
    financial_request = any(keyword in body_lower for keyword in FINANCIAL_KEYWORDS)
    
    # 9. text_complexity (0-100, 基于平均词长)
    if words:
        avg_word_length = sum(len(w) for w in words) / len(words)
        text_complexity = min(avg_word_length * 10, 100)
    else:
        text_complexity = 0
    
    # 10. text_similarity_to_legitimate_emails (简单估计)
    # 正常邮件通常有问候语、签名等
    has_greeting = any(word in body_lower for word in ["dear", "hello", "hi", "您好", "你好"])
    has_signature = any(word in body_lower for word in ["regards", "sincerely", "best", "此致", "敬礼"])
    similarity = (int(has_greeting) + int(has_signature)) / 2.0
    
    # 11. language (0=en, 1=zh, 2=mixed)
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', body))
    has_english = bool(re.search(r'[a-zA-Z]', body))
    if has_chinese and has_english:
        language = 2
    elif has_chinese:
        language = 1
    else:
        language = 0
    
    # 12. contains_obfuscated_text (检测字符替换)
    obfuscated = bool(re.search(r'[0O]{2,}|[1lI]{3,}', body))
    
    # 13. requests_otp_or_mfa
    otp_request = any(word in body_lower for word in ["otp", "verification code", "验证码", "动态密码"])
    
    # 14. contains_phishing_call_to_action
    phishing_cta = any(phrase in body_lower for phrase in [
        "click here", "verify now", "update now", "confirm identity",
        "点击这里", "立即验证", "立即更新", "确认身份"
    ])
    
    # 15. text_sentiment (0=Negative, 1=Neutral, 2=Positive)
    positive_words = ["thank", "welcome", "success", "谢谢", "欢迎", "成功"]
    negative_words = ["problem", "issue", "suspend", "问题", "暂停"]
    
    pos_count = sum(1 for word in positive_words if word in body_lower)
    neg_count = sum(1 for word in negative_words if word in body_lower)
    
    if neg_count > pos_count:
        text_sentiment = 0
    elif pos_count > neg_count:
        text_sentiment = 2
    else:
        text_sentiment = 1
    
    # 16. text_sentiment_score
    if pos_count + neg_count > 0:
        text_sentiment_score = (pos_count - neg_count) / (pos_count + neg_count)
    else:
        text_sentiment_score = 0.0
    
    return [
        float(word_count),
        float(url_count),
        float(spelling_errors),
        float(grammar_errors),
        float(suspicious_count),
        float(urgency_count),
        float(personal_info_request),
        float(financial_request),
        float(text_complexity),
        float(similarity),
        float(language),
        float(obfuscated),
        float(otp_request),
        float(phishing_cta),
        float(text_sentiment),
        float(text_sentiment_score),
    ]


def _extract_url_features(urls: List[str]) -> List[float]:
    """
    提取 URL 基础特征 (11维)
    
    Returns:
        [domain_length, dot_count, ip_address, at_symbol, hyphen,
         path_length, subdomains, tld, query_params, suspicious_params, suspicious_params_list]
    """
    if not urls:
        # 没有URL，返回默认值
        return [0.0] * 11
    
    # 使用第一个URL（最可疑的通常是第一个）
    url = urls[0]
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path
        query = parsed.query
    except:
        return [0.0] * 11
    
    # 1. domain_length
    domain_length = len(domain)
    
    # 2. dot_count
    dot_count = domain.count('.')
    
    # 3. contains_ip_address
    ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    contains_ip = bool(re.match(ip_pattern, domain))
    
    # 4. contains_at_symbol
    contains_at = '@' in url
    
    # 5. contains_hyphen
    contains_hyphen = '-' in domain
    
    # 6. path_length
    path_length = len(path)
    
    # 7. subdomains_count
    parts = domain.split('.')
    subdomains_count = max(0, len(parts) - 2)  # 减去域名和TLD
    
    # 8. tld (0=com, 1=org, 2=net, 3=edu, 4=gov, 5=other)
    tld_map = {"com": 0, "org": 1, "net": 2, "edu": 3, "gov": 4}
    if parts:
        tld_str = parts[-1].lower()
        tld = tld_map.get(tld_str, 5)
    else:
        tld = 5
    
    # 9. query_params_count
    query_params = query.split('&') if query else []
    query_params_count = len(query_params)
    
    # 10. has_suspicious_query_params
    suspicious_param_names = ["redirect", "url", "link", "goto", "next"]
    has_suspicious = any(param in query.lower() for param in suspicious_param_names)
    
    # 11. suspicious_query_params (count)
    suspicious_params_count = sum(1 for param in suspicious_param_names if param in query.lower())
    
    return [
        float(domain_length),
        float(dot_count),
        float(contains_ip),
        float(contains_at),
        float(contains_hyphen),
        float(path_length),
        float(subdomains_count),
        float(tld),
        float(query_params_count),
        float(has_suspicious),
        float(suspicious_params_count),
    ]
