"""
基础特征工程与规则检测逻辑。
这里侧重传统钓鱼特征，并预留 LLM 语义特征与判别的入口。
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse

URL_PATTERN = re.compile(r"https?://[^\s>]+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
HTML_TAG_PATTERN = re.compile(r"<\s*(script|form|input|button)[^>]*>", re.IGNORECASE)
ATTACHMENT_HINT_PATTERN = re.compile(
    r"attachment;|filename=|\.zip|\.rar|\.exe|\.scr|\.js", re.IGNORECASE
)
ANCHOR_PATTERN = re.compile(
    r'<a[^>]*href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<text>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
DOMAIN_IN_TEXT_PATTERN = re.compile(r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")

SUSPICIOUS_KEYWORDS = [
    "verify your account",
    "update your password",
    "urgent action required",
    "limited time",
    "click below",
    "登录异常",
    "账号异常",
    "密码重置",
    "点击链接",
]

BRAND_KEYWORDS = [
    "paypal",
    "apple",
    "microsoft",
    "office 365",
    "bank of america",
    "hsbc",
    "中国银行",
    "工商银行",
    "建设银行",
    "招商银行",
    "支付宝",
    "微信支付",
]

HIGH_RISK_TLDS = [
    ".top",
    ".xyz",
    ".club",
    ".work",
    ".click",
    ".link",
]


def _extract_sender_domain(content: str) -> Optional[str]:
    for line in content.splitlines():
        if line.lower().startswith("from:"):
            match = EMAIL_PATTERN.search(line)
            if match:
                return match.group(1).lower()
    return None


def _extract_subject(content: str) -> Optional[str]:
    for line in content.splitlines():
        if line.lower().startswith("subject:"):
            return line.split(":", 1)[1].strip()
    return None


def _has_html(content: str) -> bool:
    return "<html" in content.lower() or "<body" in content.lower()


def _base_domain(domain: str) -> str:
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def _extract_anchor_mismatch_stats(content: str) -> Tuple[int, int]:
    """
    统计 <a> 标签中“显示文本域名”与 href 域名不一致的次数。
    典型场景：文本显示 paypal.com，实际跳转到可疑域名。
    """
    total = 0
    mismatch = 0
    for m in ANCHOR_PATTERN.finditer(content):
        href = m.group("href")
        text = m.group("text")

        total += 1

        # 提取 href 域名
        href_domain = urlparse(href).netloc.lower()
        href_domain = _base_domain(href_domain) if href_domain else ""

        # 提取文本中的域名（如果有）
        # 去掉内部标签
        clean_text = re.sub(r"<.*?>", "", text).strip()
        tm = DOMAIN_IN_TEXT_PATTERN.search(clean_text)
        text_domain = _base_domain(tm.group(1).lower()) if tm else ""

        if href_domain and text_domain and href_domain != text_domain:
            mismatch += 1

    return total, mismatch


def _extract_auth_results(content: str) -> Dict[str, str]:
    """
    非严格解析 SPF/DKIM/DMARC 结果，基于常见头部中的关键字。
    """
    spf = "none"
    dkim = "none"
    dmarc = "none"

    for line in content.splitlines():
        low = line.lower()
        if "received-spf:" in low or low.startswith("received-spf:"):
            if "pass" in low:
                spf = "pass"
            elif "fail" in low or "softfail" in low:
                spf = "fail"
        if "authentication-results:" in low:
            if "dkim=" in low:
                if "dkim=pass" in low:
                    dkim = "pass"
                elif "dkim=fail" in low or "dkim=temperror" in low:
                    dkim = "fail"
            if "dmarc=" in low:
                if "dmarc=pass" in low:
                    dmarc = "pass"
                elif "dmarc=fail" in low:
                    dmarc = "fail"

    return {
        "spf_result": spf,
        "dkim_result": dkim,
        "dmarc_result": dmarc,
    }


def extract_traditional_features(content: str) -> Dict[str, Any]:
    """
    扩展后的传统特征：结构、URL、头部字段、可疑关键词、附件等。
    针对钓鱼邮件数据集优化。
    """
    lines = content.splitlines()
    num_lines = len(lines)
    num_chars = len(content)

    urls = URL_PATTERN.findall(content)
    num_urls = len(urls)

    lower_content = content.lower()
    keyword_hits = {kw: (kw.lower() in lower_content) for kw in SUSPICIOUS_KEYWORDS}
    keyword_hit_count = sum(1 for v in keyword_hits.values() if v)

    brand_hits = {kw: (kw.lower() in lower_content) for kw in BRAND_KEYWORDS}
    brand_hit_count = sum(1 for v in brand_hits.values() if v)

    sender_domain = _extract_sender_domain(content)
    subject = _extract_subject(content) or ""
    subject_len = len(subject)

    has_html = _has_html(content)
    has_script_or_form = bool(HTML_TAG_PATTERN.search(content))
    has_attachment_hint = bool(ATTACHMENT_HINT_PATTERN.search(content))

    anchor_total, anchor_mismatch_count = _extract_anchor_mismatch_stats(content)

    auth_results = _extract_auth_results(content)

    high_risk_url_count = 0
    for u in urls:
        lu = u.lower()
        for tld in HIGH_RISK_TLDS:
            if lu.endswith(tld) or (tld + "/") in lu:
                high_risk_url_count += 1
                break

    # 提取钓鱼模式特征
    phishing_patterns = _extract_phishing_patterns(content)

    return {
        "num_lines": num_lines,
        "num_chars": num_chars,
        "num_urls": num_urls,
        "urls": urls[:50],
        "keyword_hits": keyword_hits,
        "keyword_hit_count": keyword_hit_count,
        "brand_hits": brand_hits,
        "brand_hit_count": brand_hit_count,
        "sender_domain": sender_domain,
        "subject": subject,
        "subject_len": subject_len,
        "has_html": has_html,
        "has_script_or_form": has_script_or_form,
        "has_attachment_hint": has_attachment_hint,
        "high_risk_url_count": high_risk_url_count,
        "anchor_total": anchor_total,
        "anchor_mismatch_count": anchor_mismatch_count,
        "phishing_patterns": phishing_patterns,
        **auth_results,
    }


def dummy_llm_semantic_features(content: str) -> Dict[str, Any]:
    """
    LLM 语义特征占位实现（同步版本，保持兼容性）。
    实际使用请调用 app.llm_service.llm_service.analyze_email_semantics()（异步版本）。
    """
    return {
        "llm_supported": False,
        "phishing_intent_score": 0.0,
        "urgency_score": 0.0,
        "confidence_level": 0.0,
        "note": "请使用异步版本 analyze_email_semantics_async() 获取真实LLM特征",
    }


async def analyze_email_semantics_async(content: str) -> Dict[str, Any]:
    """
    使用 LLM 分析邮件语义特征（异步版本）。
    优先使用 DashScope (Qwen3)，失败时回退到 DeepSeek (DeepSeek-V3)。
    """
    from app.llm_service import llm_service, LLMProvider
    
    return await llm_service.analyze_email_semantics(
        content,
        provider=LLMProvider.DASHSCOPE,
        fallback_provider=LLMProvider.DEEPSEEK
    )


def simple_rule_based_detection(
    email_id: str,
    traditional_features: Dict[str, Any],
    llm_features: Dict[str, Any],
) -> Dict[str, Any]:
    """
    简单规则：基于 URL 数量、可疑关键词命中等，输出风险评分。
    """
    score = 0.0
    reasons = []

    num_urls = traditional_features.get("num_urls", 0)
    if num_urls >= 3:
        score += 0.3
        reasons.append("包含多条 URL 链接")
    elif num_urls > 0:
        score += 0.15
        reasons.append("包含 URL 链接")

    hit_count = traditional_features.get("keyword_hit_count", 0)
    if hit_count >= 2:
        score += 0.4
        reasons.append("多处可疑钓鱼关键词")
    elif hit_count == 1:
        score += 0.2
        reasons.append("存在可疑钓鱼关键词")

    num_chars = traditional_features.get("num_chars", 0)
    if num_chars > 3000:
        score += 0.1
        reasons.append("正文较长，疑似精心编写内容")

    if traditional_features.get("has_html") and traditional_features.get(
        "has_script_or_form"
    ):
        score += 0.15
        reasons.append("HTML 内容中包含脚本或表单标签")

    if traditional_features.get("has_attachment_hint"):
        score += 0.15
        reasons.append("包含疑似可执行或压缩附件提示")

    high_risk_url_count = traditional_features.get("high_risk_url_count", 0)
    if high_risk_url_count > 0:
        score += 0.15
        reasons.append("指向高风险顶级域名的链接")

    # 文本展示域名与 href 域名不一致
    anchor_mismatch = traditional_features.get("anchor_mismatch_count", 0)
    if anchor_mismatch > 0:
        score += 0.2
        reasons.append("显示链接与真实跳转域名不一致")

    # SPF/DKIM/DMARC 失败信号
    if traditional_features.get("spf_result") == "fail":
        score += 0.1
        reasons.append("SPF 检查失败")
    if traditional_features.get("dkim_result") == "fail":
        score += 0.1
        reasons.append("DKIM 检查失败")
    if traditional_features.get("dmarc_result") == "fail":
        score += 0.1
        reasons.append("DMARC 检查失败")

    score = min(score, 1.0)

    if score >= 0.7:
        attack_type = "hybrid"  # 假设存在复杂钓鱼链路
    elif score >= 0.4:
        attack_type = "traditional"
    elif score >= 0.25:
        attack_type = "llm_generated"
    else:
        attack_type = "benign"

    return {
        "email_id": email_id,
        "is_phishing": attack_type != "benign",
        "attack_type": attack_type,
        "risk_score": round(score, 3),
        "reasons": reasons,
        "traditional_features": traditional_features,
        "llm_semantic_features": llm_features,
    }


def _extract_phishing_patterns(content: str) -> Dict[str, Any]:
    """
    提取钓鱼邮件特有的模式特征
    """
    lower_content = content.lower()
    
    # 1. 检测伪造发件人域名（常见钓鱼手法）
    suspicious_sender_patterns = [
        r"from:.*@.*\.(top|xyz|club|work|click|link|cn)",  # 高风险TLD
        r"reply-to:.*@(gmail|qq|163|hotmail|outlook)\.com",  # Reply-To使用免费邮箱
    ]
    fake_sender_score = sum(1 for p in suspicious_sender_patterns if re.search(p, lower_content, re.IGNORECASE))
    
    # 2. 检测base64编码内容（常用于隐藏恶意内容）
    has_base64 = bool(re.search(r"content-transfer-encoding:\s*base64", lower_content))
    base64_blocks = len(re.findall(r"^[A-Za-z0-9+/]{40,}={0,2}$", content, re.MULTILINE))
    
    # 3. 检测中文钓鱼关键词
    chinese_phishing_keywords = [
        "财务", "发票", "报销", "转账", "汇款", "账号异常", "密码重置",
        "紧急", "立即", "点击", "验证", "升级", "通知", "重要",
        "中奖", "优惠", "免费", "贷款", "信用卡"
    ]
    chinese_keyword_count = sum(1 for kw in chinese_phishing_keywords if kw in content)
    
    # 4. 检测可疑附件
    suspicious_attachments = [
        r"\.exe", r"\.scr", r"\.bat", r"\.cmd", r"\.vbs", r"\.js",
        r"\.zip", r"\.rar", r"\.docx", r"\.xlsx", r"\.pdf"
    ]
    attachment_risk_score = sum(1 for p in suspicious_attachments if re.search(p, lower_content))
    
    # 5. 检测邮件头部异常
    received_count = len(re.findall(r"^received:", lower_content, re.MULTILINE))
    has_x_mailer = bool(re.search(r"x-mailer:", lower_content))
    has_message_id = bool(re.search(r"message-id:", lower_content))
    
    # 6. 检测URL特征
    urls = URL_PATTERN.findall(content)
    url_domains = []
    for url in urls:
        parsed = urlparse(url)
        if parsed.netloc:
            url_domains.append(parsed.netloc.lower())
    
    unique_domains = len(set(url_domains))
    has_ip_url = any(re.match(r"\d+\.\d+\.\d+\.\d+", d) for d in url_domains)
    
    # 7. 检测邮件结构异常
    has_multipart = bool(re.search(r"content-type:.*multipart", lower_content))
    boundary_count = len(re.findall(r"boundary=", lower_content))
    
    # 8. 检测DKIM/SPF伪造迹象
    dkim_present = bool(re.search(r"dkim-signature:", lower_content))
    spf_present = bool(re.search(r"received-spf:", lower_content))
    
    return {
        "fake_sender_score": fake_sender_score,
        "has_base64": has_base64,
        "base64_blocks": base64_blocks,
        "chinese_keyword_count": chinese_keyword_count,
        "attachment_risk_score": attachment_risk_score,
        "received_count": received_count,
        "has_x_mailer": has_x_mailer,
        "has_message_id": has_message_id,
        "unique_domains": unique_domains,
        "has_ip_url": has_ip_url,
        "has_multipart": has_multipart,
        "boundary_count": boundary_count,
        "dkim_present": dkim_present,
        "spf_present": spf_present,
    }


def build_feature_vector(traditional_features: Dict[str, Any]) -> List[float]:
    """
    将传统特征转为数值特征向量，针对钓鱼邮件优化。
    特征包括：
    - 基础统计特征
    - URL和域名特征
    - 邮件头部特征
    - 钓鱼模式特征
    - 认证结果特征
    """
    # 提取钓鱼模式特征（如果还没有）
    phishing_patterns = traditional_features.get("phishing_patterns", {})
    
    vector = [
        # 基础统计特征 (6个)
        float(traditional_features.get("num_chars", 0)),
        float(traditional_features.get("num_lines", 0)),
        float(traditional_features.get("num_urls", 0)),
        float(traditional_features.get("subject_len", 0)),
        float(traditional_features.get("keyword_hit_count", 0)),
        float(traditional_features.get("brand_hit_count", 0)),
        
        # URL和域名特征 (4个)
        float(traditional_features.get("high_risk_url_count", 0)),
        float(traditional_features.get("anchor_mismatch_count", 0)),
        float(phishing_patterns.get("unique_domains", 0)),
        1.0 if phishing_patterns.get("has_ip_url") else 0.0,
        
        # HTML和脚本特征 (3个)
        1.0 if traditional_features.get("has_html") else 0.0,
        1.0 if traditional_features.get("has_script_or_form") else 0.0,
        1.0 if traditional_features.get("has_attachment_hint") else 0.0,
        
        # 钓鱼模式特征 (8个)
        float(phishing_patterns.get("fake_sender_score", 0)),
        1.0 if phishing_patterns.get("has_base64") else 0.0,
        float(phishing_patterns.get("base64_blocks", 0)),
        float(phishing_patterns.get("chinese_keyword_count", 0)),
        float(phishing_patterns.get("attachment_risk_score", 0)),
        float(phishing_patterns.get("received_count", 0)),
        float(phishing_patterns.get("boundary_count", 0)),
        1.0 if phishing_patterns.get("has_x_mailer") else 0.0,
        
        # 邮件认证特征 (5个)
        1.0 if traditional_features.get("spf_result") == "fail" else 0.0,
        1.0 if traditional_features.get("dkim_result") == "fail" else 0.0,
        1.0 if traditional_features.get("dmarc_result") == "fail" else 0.0,
        1.0 if phishing_patterns.get("dkim_present") else 0.0,
        1.0 if phishing_patterns.get("spf_present") else 0.0,
    ]
    
    return vector

