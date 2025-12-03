"""
使用 LLM 提取 PhishMMF 228 维特征。

PhishMMF 的训练数据使用 LLM 手动提取了多模态特征，包括：
- 文本特征（主题、发件人、正文）
- URL 情报特征（域名、黑名单、WHOIS等）
- 截图图像特征（登录表单、品牌相似度等）
- 网站结构特征（表单、脚本、iframe等）

由于我们无法获取外部数据源（URL OSINT、网站截图等），
我们使用 LLM 来推断这些特征，尽可能复现训练数据的特征提取方式。
"""

from __future__ import annotations

import json
from typing import Dict, Any, List, Optional
from enum import Enum

from .llm_service import llm_service, LLMProvider


# PhishMMF JSON Schema（简化版，用于LLM提示）
PHISHMMF_SCHEMA_PROMPT = """
请根据以下结构提取邮件特征（返回JSON格式）：

{
    "text_features": {
        "subject": {
            "urgency_level": "高/中/低",
            "contains_threatening_language": true/false,
            "contains_seductive_language": true/false,
            "contains_emergency_action_request": true/false,
            "sentiment_score": -1.0到1.0之间的浮点数,
            "sentiment_label": "积极/消极/中性"
        },
        "sender": {
            "impersonation_type": "银行/政府/电商/社交媒体/无",
            "email_address_anomalies": "非官方域名/拼写错误/无",
            "sender_reputation_score": 0.0到1.0之间的浮点数,
            "domain_similarity_to_known_brands": 0.0到1.0之间的浮点数
        },
        "content": {
            "word_count": 整数,
            "url_count": 整数,
            "spelling_errors": 整数,
            "grammar_errors": 整数,
            "suspicious_keywords": ["关键词1", "关键词2"],
            "urgency_words_count": 整数,
            "contains_personal_information_request": true/false,
            "contains_abnormal_financial_request": true/false,
            "text_complexity": 0到100之间的浮点数,
            "text_similarity_to_legitimate_emails": 0.0到1.0之间的浮点数,
            "language": "中文/英文/混合",
            "contains_obfuscated_text": true/false,
            "requests_otp_or_mfa": true/false,
            "contains_phishing_call_to_action": true/false,
            "text_sentiment": "积极/消极/中性",
            "text_sentiment_score": -1.0到1.0之间的浮点数
        }
    },
    "url_intelligence_features": {
        "basic": {
            "domain_length": 整数,
            "dot_count": 整数,
            "contains_ip_address": true/false,
            "contains_at_symbol": true/false,
            "contains_hyphen": true/false,
            "path_length": 整数,
            "subdomains_count": 整数,
            "tld": "com/org/net等",
            "query_params_count": 整数,
            "has_suspicious_query_params": true/false,
            "suspicious_query_params": ["参数1", "参数2"]
        },
        "reputation_and_risk": {
            "is_blacklisted": true/false,
            "risk_score": 0到100之间的整数,
            "redirect_count": 整数,
            "domain_age_days": 整数（推测），
            "whois_hidden": true/false（推测）,
            "domain_similarity_score": 0.0到1.0之间的浮点数,
            "contains_suspicious_keywords": true/false,
            "brand_similarity_score": 0.0到1.0之间的浮点数,
            "ssl_https": true/false（推测）,
            "ssl_certificate_status": "有效/无效/不存在",
            "ca_trust_score": 0到100之间的浮点数,
            "suspicious_subdomains": ["子域名1", "子域名2"]
        }
    },
    "image_features": {
        "layout": {
            "contains_login_form": true/false（推测）,
            "contains_bank_card_input": true/false（推测）,
            "form_present": true/false（推测）,
            "login_form_detected": true/false（推测）,
            "element_complexity": 0到100之间的浮点数
        },
        "visual_similarity": {
            "logo_similarity_to_known_brands": 0.0到1.0之间的浮点数,
            "favicon_matches_brand": true/false,
            "brand_visual_similarity": 0.0到1.0之间的浮点数,
            "visual_similarity_score": 0.0到1.0之间的浮点数,
            "brand_mismatch": true/false,
            "suspicious_ui_layout": true/false
        },
        "risk_elements": {
            "suspicious_links": 整数,
            "contains_suspicious_popup": true/false,
            "suspicious_visual_elements": 整数,
            "visual_phishing_risk": 0到100之间的浮点数,
            "image_text_keywords": ["关键词1", "关键词2"]
        }
    },
    "website_features": {
        "structure": {
            "form_count": 整数,
            "external_link_count": 整数,
            "script_count": 整数,
            "iframe_count": 整数,
            "input_form_count": 整数,
            "hidden_inputs_count": 整数,
            "contains_iframe": true/false,
            "meta_redirect": true/false
        },
        "content": {
            "title_url_relevance": 0.0到1.0之间的浮点数,
            "content_similarity_to_legitimate_site": 0.0到1.0之间的浮点数,
            "contains_abnormal_redirect": true/false,
            "contains_hidden_elements": true/false,
            "privacy_policy_valid": true/false,
            "dynamic_script_behavior": "描述文本"
        },
        "security": {
            "uses_https": true/false,
            "ssl_certificate_status": "有效/无效/不存在",
            "ca_trust_score": 0到100之间的浮点数,
            "server_location": "国家/地区",
            "domain_registration_country": "国家/地区",
            "server_country_match_domain": true/false
        }
    }
}

注意：
1. 对于无法从邮件内容直接获取的特征（如域名年龄、WHOIS、网站截图等），请根据邮件内容和常识进行合理推测
2. 如果邮件中没有URL，URL相关特征使用默认值（如域名长度=0）
3. 如果邮件是纯文本，图像和网站特征使用默认值
4. 所有数值必须在指定范围内
5. 只返回JSON，不要其他文字
"""


def _normalize_count(value: float, typical_max: float = 100.0) -> float:
    """
    归一化计数特征到合理范围。
    使用 log1p 变换来压缩大值。
    """
    import math
    if value <= 0:
        return 0.0
    # log1p(x) = log(1+x)，然后除以 log(1+typical_max) 归一化到 [0, 1]
    normalized = math.log1p(value) / math.log1p(typical_max)
    return min(normalized, 2.0)  # 限制最大值


def _vectorize_features(features_dict: Dict[str, Any]) -> List[float]:
    """
    将 JSON 特征字典转换为 228 维向量。
    
    特征顺序必须与训练数据一致。
    注意：训练数据已经过标准化，所以我们也需要对原始特征进行合理的缩放。
    """
    vector = []
    
    # 1. 文本特征 - 主题 (6维)
    subject = features_dict.get("text_features", {}).get("subject", {})
    urgency_map = {"低": 0, "中": 1, "高": 2}
    vector.append(float(urgency_map.get(subject.get("urgency_level", "低"), 0)) / 2.0)  # 归一化到[0,1]
    vector.append(float(subject.get("contains_threatening_language", False)))
    vector.append(float(subject.get("contains_seductive_language", False)))
    vector.append(float(subject.get("contains_emergency_action_request", False)))
    vector.append(float(subject.get("sentiment_score", 0.0)))  # 已经在[-1,1]
    sentiment_map = {"消极": 0, "中性": 1, "积极": 2}
    vector.append(float(sentiment_map.get(subject.get("sentiment_label", "中性"), 1)) / 2.0)  # 归一化到[0,1]
    
    # 2. 文本特征 - 发件人 (4维)
    sender = features_dict.get("text_features", {}).get("sender", {})
    impersonation_map = {"无": 0, "银行": 1, "政府": 2, "电商": 3, "社交媒体": 4}
    vector.append(float(impersonation_map.get(sender.get("impersonation_type", "无"), 0)) / 4.0)  # 归一化到[0,1]
    anomaly_map = {"无": 0, "非官方域名": 1, "拼写错误": 2}
    vector.append(float(anomaly_map.get(sender.get("email_address_anomalies", "无"), 0)) / 2.0)  # 归一化到[0,1]
    vector.append(float(sender.get("sender_reputation_score", 0.5)))  # 已经在[0,1]
    vector.append(float(sender.get("domain_similarity_to_known_brands", 0.0)))  # 已经在[0,1]
    
    # 3. 文本特征 - 正文 (15维)
    content = features_dict.get("text_features", {}).get("content", {})
    vector.append(_normalize_count(float(content.get("word_count", 0)), 500))  # 典型邮件500词
    vector.append(_normalize_count(float(content.get("url_count", 0)), 10))  # 典型最多10个URL
    vector.append(_normalize_count(float(content.get("spelling_errors", 0)), 20))
    vector.append(_normalize_count(float(content.get("grammar_errors", 0)), 20))
    vector.append(_normalize_count(float(len(content.get("suspicious_keywords", []))), 10))
    vector.append(_normalize_count(float(content.get("urgency_words_count", 0)), 10))
    vector.append(float(content.get("contains_personal_information_request", False)))
    vector.append(float(content.get("contains_abnormal_financial_request", False)))
    vector.append(float(content.get("text_complexity", 50.0)) / 100.0)  # 归一化到[0,1]
    vector.append(float(content.get("text_similarity_to_legitimate_emails", 0.5)))  # 已经在[0,1]
    lang_map = {"中文": 0, "英文": 1, "混合": 2}
    vector.append(float(lang_map.get(content.get("language", "英文"), 1)) / 2.0)  # 归一化到[0,1]
    vector.append(float(content.get("contains_obfuscated_text", False)))
    vector.append(float(content.get("requests_otp_or_mfa", False)))
    vector.append(float(content.get("contains_phishing_call_to_action", False)))
    sentiment_map2 = {"消极": 0, "中性": 1, "积极": 2}
    vector.append(float(sentiment_map2.get(content.get("text_sentiment", "中性"), 1)) / 2.0)  # 归一化到[0,1]
    
    # 4. URL情报特征 - 基础 (11维)
    url_basic = features_dict.get("url_intelligence_features", {}).get("basic", {})
    vector.append(_normalize_count(float(url_basic.get("domain_length", 0)), 50))
    vector.append(_normalize_count(float(url_basic.get("dot_count", 0)), 5))
    vector.append(float(url_basic.get("contains_ip_address", False)))
    vector.append(float(url_basic.get("contains_at_symbol", False)))
    vector.append(float(url_basic.get("contains_hyphen", False)))
    vector.append(_normalize_count(float(url_basic.get("path_length", 0)), 100))
    vector.append(_normalize_count(float(url_basic.get("subdomains_count", 0)), 5))
    tld_map = {"com": 0, "org": 1, "net": 2, "其他": 3}
    vector.append(float(tld_map.get(url_basic.get("tld", "其他"), 3)) / 3.0)  # 归一化到[0,1]
    vector.append(_normalize_count(float(url_basic.get("query_params_count", 0)), 10))
    vector.append(float(url_basic.get("has_suspicious_query_params", False)))
    vector.append(_normalize_count(float(len(url_basic.get("suspicious_query_params", []))), 5))
    
    # 5. URL情报特征 - 信誉和风险 (12维，去掉重复的ssl_certificate_status)
    url_rep = features_dict.get("url_intelligence_features", {}).get("reputation_and_risk", {})
    vector.append(float(url_rep.get("is_blacklisted", False)))
    vector.append(float(url_rep.get("risk_score", 0)) / 100.0)  # 归一化到[0,1]
    vector.append(_normalize_count(float(url_rep.get("redirect_count", 0)), 5))
    vector.append(_normalize_count(float(url_rep.get("domain_age_days", 365)), 3650))  # 10年
    vector.append(float(url_rep.get("whois_hidden", False)))
    vector.append(float(url_rep.get("domain_similarity_score", 0.0)))  # 已经在[0,1]
    vector.append(float(url_rep.get("contains_suspicious_keywords", False)))
    vector.append(float(url_rep.get("brand_similarity_score", 0.0)))  # 已经在[0,1]
    vector.append(float(url_rep.get("ssl_https", True)))
    ssl_map = {"有效": 0, "无效": 1, "不存在": 2}
    vector.append(float(ssl_map.get(url_rep.get("ssl_certificate_status", "有效"), 0)) / 2.0)  # 归一化到[0,1]
    vector.append(float(url_rep.get("ca_trust_score", 50.0)) / 100.0)  # 归一化到[0,1]
    vector.append(_normalize_count(float(len(url_rep.get("suspicious_subdomains", []))), 5))
    
    # 6. 图像特征 - 布局 (5维)
    img_layout = features_dict.get("image_features", {}).get("layout", {})
    vector.append(float(img_layout.get("contains_login_form", False)))
    vector.append(float(img_layout.get("contains_bank_card_input", False)))
    vector.append(float(img_layout.get("form_present", False)))
    vector.append(float(img_layout.get("login_form_detected", False)))
    vector.append(float(img_layout.get("element_complexity", 50.0)) / 100.0)  # 归一化到[0,1]
    
    # 7. 图像特征 - 视觉相似度 (6维)
    img_visual = features_dict.get("image_features", {}).get("visual_similarity", {})
    vector.append(float(img_visual.get("logo_similarity_to_known_brands", 0.0)))
    vector.append(float(img_visual.get("favicon_matches_brand", False)))
    vector.append(float(img_visual.get("brand_visual_similarity", 0.0)))
    vector.append(float(img_visual.get("visual_similarity_score", 0.0)))
    vector.append(float(img_visual.get("brand_mismatch", False)))
    vector.append(float(img_visual.get("suspicious_ui_layout", False)))
    
    # 8. 图像特征 - 风险元素 (5维)
    img_risk = features_dict.get("image_features", {}).get("risk_elements", {})
    vector.append(_normalize_count(float(img_risk.get("suspicious_links", 0)), 10))
    vector.append(float(img_risk.get("contains_suspicious_popup", False)))
    vector.append(_normalize_count(float(img_risk.get("suspicious_visual_elements", 0)), 10))
    vector.append(float(img_risk.get("visual_phishing_risk", 0.0)) / 100.0)  # 归一化到[0,1]
    vector.append(_normalize_count(float(len(img_risk.get("image_text_keywords", []))), 10))
    
    # 9. 网站特征 - 结构 (8维)
    web_struct = features_dict.get("website_features", {}).get("structure", {})
    vector.append(_normalize_count(float(web_struct.get("form_count", 0)), 10))
    vector.append(_normalize_count(float(web_struct.get("external_link_count", 0)), 50))
    vector.append(_normalize_count(float(web_struct.get("script_count", 0)), 20))
    vector.append(_normalize_count(float(web_struct.get("iframe_count", 0)), 5))
    vector.append(_normalize_count(float(web_struct.get("input_form_count", 0)), 10))
    vector.append(_normalize_count(float(web_struct.get("hidden_inputs_count", 0)), 10))
    vector.append(float(web_struct.get("contains_iframe", False)))
    vector.append(float(web_struct.get("meta_redirect", False)))
    
    # 10. 网站特征 - 内容 (6维)
    web_content = features_dict.get("website_features", {}).get("content", {})
    vector.append(float(web_content.get("title_url_relevance", 0.5)))  # 已经在[0,1]
    vector.append(float(web_content.get("content_similarity_to_legitimate_site", 0.5)))  # 已经在[0,1]
    vector.append(float(web_content.get("contains_abnormal_redirect", False)))
    vector.append(float(web_content.get("contains_hidden_elements", False)))
    vector.append(float(web_content.get("privacy_policy_valid", False)))
    # dynamic_script_behavior 是文本，编码为长度
    vector.append(_normalize_count(float(len(web_content.get("dynamic_script_behavior", ""))), 100))
    
    # 11. 网站特征 - 安全 (6维)
    web_security = features_dict.get("website_features", {}).get("security", {})
    vector.append(float(web_security.get("uses_https", True)))
    ssl_map2 = {"有效": 0, "无效": 1, "不存在": 2}
    vector.append(float(ssl_map2.get(web_security.get("ssl_certificate_status", "有效"), 0)) / 2.0)  # 归一化到[0,1]
    vector.append(float(web_security.get("ca_trust_score", 50.0)) / 100.0)  # 归一化到[0,1]
    # server_location 和 domain_registration_country 编码为长度
    vector.append(_normalize_count(float(len(web_security.get("server_location", ""))), 20))
    vector.append(_normalize_count(float(len(web_security.get("domain_registration_country", ""))), 20))
    vector.append(float(web_security.get("server_country_match_domain", True)))
    
    # 补充到228维（如果不足）
    while len(vector) < 228:
        vector.append(0.0)
    
    # 截断到228维（如果超出）
    return vector[:228]


async def extract_phishmmf_features_with_llm(
    email_content: str,
    provider: LLMProvider = LLMProvider.DASHSCOPE,
    fallback_provider: Optional[LLMProvider] = LLMProvider.DEEPSEEK
) -> Optional[List[float]]:
    """
    使用 LLM 提取 PhishMMF 228 维特征。
    
    Args:
        email_content: 邮件内容（包括主题、发件人、正文等）
        provider: 主LLM提供商
        fallback_provider: 备用LLM提供商
    
    Returns:
        228维特征向量，如果提取失败返回None
    """
    # 检查LLM是否可用
    if not llm_service.is_available(provider):
        if fallback_provider and llm_service.is_available(fallback_provider):
            provider = fallback_provider
        else:
            print("LLM服务不可用，无法提取PhishMMF特征")
            return None
    
    # 选择客户端
    if provider == LLMProvider.DASHSCOPE:
        client = llm_service.dashscope_client
        model_name = "qwen-plus"
    elif provider == LLMProvider.DEEPSEEK:
        client = llm_service.deepseek_client
        model_name = "deepseek-chat"
    else:
        return None
    
    # 构建提示词
    prompt = f"""{PHISHMMF_SCHEMA_PROMPT}

邮件内容：
{email_content[:3000]}

请仔细分析邮件，提取所有特征。对于无法从邮件直接获取的特征（如域名年龄、网站截图等），请根据邮件内容和常识进行合理推测。"""
    
    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的邮件特征提取专家，擅长从邮件中提取多模态特征用于钓鱼检测。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # 低温度以获得稳定输出
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            print("LLM返回空内容")
            return None
        
        # 解析JSON
        features_dict = json.loads(content)
        
        # 向量化
        features_vector = _vectorize_features(features_dict)
        
        print(f"✅ LLM特征提取成功 ({provider.value}): {len(features_vector)}维")
        return features_vector
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析失败: {e}")
        print(f"LLM返回内容: {content[:500]}")
        return None
    except Exception as e:
        print(f"❌ LLM特征提取失败 ({provider.value}): {e}")
        return None


async def call_llm(
    prompt: str,
    provider: LLMProvider = LLMProvider.DASHSCOPE,
    response_format: str = "json"
) -> Optional[str]:
    """
    通用LLM调用函数（用于测试）
    """
    if not llm_service.is_available(provider):
        return None
    
    if provider == LLMProvider.DASHSCOPE:
        client = llm_service.dashscope_client
        model_name = "qwen-plus"
    elif provider == LLMProvider.DEEPSEEK:
        client = llm_service.deepseek_client
        model_name = "deepseek-chat"
    else:
        return None
    
    try:
        kwargs = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }
        
        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM调用失败: {e}")
        return None
