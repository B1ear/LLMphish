"""
LLM 服务模块：集成阿里云 DashScope (Qwen3) 和 DeepSeek (DeepSeek-V3) API。

两个API都兼容OpenAI格式，使用统一的接口调用。
"""

from __future__ import annotations

import os
import json
from typing import Dict, Any, Optional, List
from enum import Enum

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMProvider(str, Enum):
    """LLM 提供商枚举"""
    DASHSCOPE = "dashscope"  # 阿里云 DashScope (Qwen3)
    DEEPSEEK = "deepseek"    # DeepSeek (DeepSeek-V3)


class LLMService:
    """LLM 服务类，支持多个提供商"""
    
    def __init__(self):
        self.dashscope_client: Optional[AsyncOpenAI] = None
        self.deepseek_client: Optional[AsyncOpenAI] = None
        self._init_clients()
    
    def _init_clients(self):
        """初始化 LLM 客户端"""
        if not OPENAI_AVAILABLE:
            return
        
        # 初始化 DashScope (Qwen3) 客户端
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        if dashscope_key:
            self.dashscope_client = AsyncOpenAI(
                api_key=dashscope_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        
        # 初始化 DeepSeek (DeepSeek-V3) 客户端
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            self.deepseek_client = AsyncOpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1"
            )
    
    def is_available(self, provider: LLMProvider) -> bool:
        """检查指定提供商是否可用"""
        if provider == LLMProvider.DASHSCOPE:
            return self.dashscope_client is not None
        elif provider == LLMProvider.DEEPSEEK:
            return self.deepseek_client is not None
        return False
    
    async def analyze_email_semantics(
        self,
        email_content: str,
        provider: LLMProvider = LLMProvider.DASHSCOPE,
        fallback_provider: Optional[LLMProvider] = LLMProvider.DEEPSEEK
    ) -> Dict[str, Any]:
        """
        使用 LLM 分析邮件语义特征。
        
        Returns:
            包含语义特征的字典：
            - phishing_intent_score: 钓鱼意图得分 (0-1)
            - urgency_score: 紧急程度得分 (0-1)
            - sentiment_score: 情感得分 (-1到1)
            - suspicious_language_score: 可疑语言得分 (0-1)
            - confidence_level: 置信度 (0-1)
        """
        if not OPENAI_AVAILABLE:
            return self._default_response()
        
        # 选择客户端
        client = None
        model_name = ""
        
        if provider == LLMProvider.DASHSCOPE and self.dashscope_client:
            client = self.dashscope_client
            model_name = "qwen-plus"  # 使用 qwen-plus (Qwen3 系列，性能较好)
        elif provider == LLMProvider.DEEPSEEK and self.deepseek_client:
            client = self.deepseek_client
            model_name = "deepseek-chat"  # DeepSeek-V3 模型
        
        # 如果主提供商不可用，尝试备用提供商
        if not client and fallback_provider:
            if fallback_provider == LLMProvider.DASHSCOPE and self.dashscope_client:
                client = self.dashscope_client
                model_name = "qwen-plus"
            elif fallback_provider == LLMProvider.DEEPSEEK and self.deepseek_client:
                client = self.deepseek_client
                model_name = "deepseek-chat"
        
        if not client:
            return self._default_response()
        
        # 构建提示词
        prompt = self._build_semantic_analysis_prompt(email_content)
        
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的钓鱼邮件检测专家，擅长分析邮件的语义特征、意图和可疑性。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 较低温度以获得更稳定的输出
                response_format={"type": "json_object"}  # 要求JSON格式输出
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return {
                    "llm_supported": True,
                    "provider": provider.value,
                    "model": model_name,
                    "phishing_intent_score": float(result.get("phishing_intent_score", 0.0)),
                    "urgency_score": float(result.get("urgency_score", 0.0)),
                    "sentiment_score": float(result.get("sentiment_score", 0.0)),
                    "suspicious_language_score": float(result.get("suspicious_language_score", 0.0)),
                    "confidence_level": float(result.get("confidence_level", 0.0)),
                }
        except Exception as e:
            print(f"LLM 调用失败 ({provider.value}): {e}")
            return self._default_response(provider.value, str(e))
        
        return self._default_response()
    
    async def detect_phishing_with_llm(
        self,
        email_content: str,
        traditional_features: Dict[str, Any],
        provider: LLMProvider = LLMProvider.DASHSCOPE,
        fallback_provider: Optional[LLMProvider] = LLMProvider.DEEPSEEK
    ) -> Dict[str, Any]:
        """
        使用 LLM 进行钓鱼邮件检测（辅助检测）。
        
        Returns:
            包含检测结果的字典：
            - is_phishing: 是否为钓鱼邮件
            - risk_score: 风险评分 (0-1)
            - attack_type: 攻击类型 (traditional/llm_generated/hybrid/benign)
            - reasoning: 推理过程
        """
        if not OPENAI_AVAILABLE:
            return self._default_detection_response()
        
        # 选择客户端（同 analyze_email_semantics）
        client = None
        model_name = ""
        
        if provider == LLMProvider.DASHSCOPE and self.dashscope_client:
            client = self.dashscope_client
            model_name = "qwen-plus"
        elif provider == LLMProvider.DEEPSEEK and self.deepseek_client:
            client = self.deepseek_client
            model_name = "deepseek-chat"
        
        if not client and fallback_provider:
            if fallback_provider == LLMProvider.DASHSCOPE and self.dashscope_client:
                client = self.dashscope_client
                model_name = "qwen-plus"
            elif fallback_provider == LLMProvider.DEEPSEEK and self.deepseek_client:
                client = self.deepseek_client
                model_name = "deepseek-chat"
        
        if not client:
            return self._default_detection_response()
        
        # 构建检测提示词
        prompt = self._build_detection_prompt(email_content, traditional_features)
        
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的钓鱼邮件检测系统，能够识别传统钓鱼、LLM生成的钓鱼邮件和混合攻击链。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return {
                    "llm_supported": True,
                    "provider": provider.value,
                    "model": model_name,
                    "is_phishing": bool(result.get("is_phishing", False)),
                    "risk_score": float(result.get("risk_score", 0.0)),
                    "attack_type": result.get("attack_type", "benign"),
                    "reasoning": result.get("reasoning", ""),
                }
        except Exception as e:
            print(f"LLM 检测失败 ({provider.value}): {e}")
            return self._default_detection_response(provider.value, str(e))
        
        return self._default_detection_response()
    
    def _build_semantic_analysis_prompt(self, email_content: str) -> str:
        """构建语义分析提示词"""
        return f"""请分析以下邮件的语义特征，返回JSON格式结果：

邮件内容：
{email_content[:2000]}  # 限制长度避免token过多

请分析以下维度并返回JSON：
{{
    "phishing_intent_score": 0.0-1.0之间的浮点数，表示邮件包含钓鱼意图的程度（1.0表示非常可疑，0.0表示正常），
    "urgency_score": 0.0-1.0之间的浮点数，表示邮件的紧急程度（1.0表示非常紧急，0.0表示不紧急），
    "sentiment_score": -1.0到1.0之间的浮点数，表示邮件的情感倾向（1.0表示积极，-1.0表示消极），
    "suspicious_language_score": 0.0-1.0之间的浮点数，表示邮件使用可疑语言的程度（1.0表示非常可疑，0.0表示正常），
    "confidence_level": 0.0-1.0之间的浮点数，表示分析的置信度
}}

只返回JSON，不要其他文字。"""
    
    def _build_detection_prompt(self, email_content: str, traditional_features: Dict[str, Any]) -> str:
        """构建检测提示词"""
        features_summary = f"""
传统特征摘要：
- URL数量: {traditional_features.get('num_urls', 0)}
- 可疑关键词命中数: {traditional_features.get('keyword_hit_count', 0)}
- 包含HTML: {traditional_features.get('has_html', False)}
- 包含脚本/表单: {traditional_features.get('has_script_or_form', False)}
- 高风险URL数量: {traditional_features.get('high_risk_url_count', 0)}
"""
        
        return f"""请分析以下邮件是否为钓鱼邮件，返回JSON格式结果：

邮件内容：
{email_content[:2000]}

{features_summary}

请判断：
1. 是否为钓鱼邮件（is_phishing: true/false）
2. 风险评分（risk_score: 0.0-1.0）
3. 攻击类型（attack_type: "traditional"传统钓鱼 / "llm_generated"LLM生成 / "hybrid"混合攻击 / "benign"正常）
4. 简要推理过程（reasoning: 字符串）

返回JSON格式：
{{
    "is_phishing": true/false,
    "risk_score": 0.0-1.0,
    "attack_type": "traditional"|"llm_generated"|"hybrid"|"benign",
    "reasoning": "你的推理过程"
}}

只返回JSON，不要其他文字。"""
    
    def _default_response(self, provider: str = "none", error: str = "") -> Dict[str, Any]:
        """默认响应（LLM不可用时）"""
        return {
            "llm_supported": False,
            "provider": provider,
            "phishing_intent_score": 0.0,
            "urgency_score": 0.0,
            "sentiment_score": 0.0,
            "suspicious_language_score": 0.0,
            "confidence_level": 0.0,
            "note": f"LLM不可用: {error}" if error else "LLM服务未配置或不可用",
        }
    
    def _default_detection_response(self, provider: str = "none", error: str = "") -> Dict[str, Any]:
        """默认检测响应（LLM不可用时）"""
        return {
            "llm_supported": False,
            "provider": provider,
            "is_phishing": False,
            "risk_score": 0.0,
            "attack_type": "benign",
            "reasoning": f"LLM不可用: {error}" if error else "LLM服务未配置或不可用",
        }


# 全局LLM服务实例
llm_service = LLMService()

