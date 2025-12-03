import re
import base64
import quopri
from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException

from app.storage import store

router = APIRouter()


def decode_email_content(content: str) -> str:
    """
    解码邮件内容，支持多种编码格式
    - GB2312/GBK/GB18030 + quoted-printable
    - GB2312/GBK/GB18030 + base64
    - UTF-8 + quoted-printable
    - UTF-8 + base64
    """
    try:
        # 1. 检测字符集
        charset = 'utf-8'
        charset_match = re.search(
            r'Content-Type:\s*text/(?:html|plain)[^;]*;\s*charset=["\'"]?(gb2312|gbk|gb18030|utf-8|iso-8859-1)[^"\'"\\s]*',
            content,
            re.IGNORECASE
        )
        if charset_match:
            charset = charset_match.group(1).lower()
        
        # 2. 检测传输编码
        encoding = None
        encoding_match = re.search(
            r'Content-Transfer-Encoding:\s*([^\r\n]+)',
            content,
            re.IGNORECASE
        )
        if encoding_match:
            encoding = encoding_match.group(1).strip().lower()
        
        # 3. 提取邮件正文（移除头部）
        body = content
        # 查找邮件头部结束位置（连续两个换行）
        header_end = re.search(r'\r?\n\r?\n', content)
        if header_end:
            header = content[:header_end.end()]
            # 验证是否是有效的邮件头部
            if re.search(r'^(From|To|Subject|Date|Content-Type|MIME-Version):', header, re.IGNORECASE | re.MULTILINE):
                body = content[header_end.end():]
        
        # 4. 处理 MIME 多部分邮件
        if 'Content-Type:' in body:
            # 尝试提取 text/html 部分
            html_part = re.search(
                r'Content-Type:\s*text/html[^\n]*\r?\nContent-Transfer-Encoding:\s*([^\r\n]+)\r?\n\r?\n([\s\S]+?)(?=\r?\n--|\r?\nContent-Type:|$)',
                body,
                re.IGNORECASE
            )
            if html_part:
                encoding = html_part.group(1).strip().lower()
                body = html_part.group(2)
            else:
                # 尝试提取 text/plain 部分
                plain_part = re.search(
                    r'Content-Type:\s*text/plain[^\n]*\r?\nContent-Transfer-Encoding:\s*([^\r\n]+)\r?\n\r?\n([\s\S]+?)(?=\r?\n--|\r?\nContent-Type:|$)',
                    body,
                    re.IGNORECASE
                )
                if plain_part:
                    encoding = plain_part.group(1).strip().lower()
                    body = plain_part.group(2)
        
        # 5. 根据编码解码内容
        decoded = body
        
        if encoding == 'quoted-printable':
            # Quoted-Printable 解码
            decoded = quopri.decodestring(body.encode('latin-1')).decode(charset, errors='replace')
        elif encoding == 'base64':
            # Base64 解码
            try:
                # 清理空白字符
                cleaned = re.sub(r'\s', '', body)
                decoded_bytes = base64.b64decode(cleaned)
                decoded = decoded_bytes.decode(charset, errors='replace')
            except Exception as e:
                print(f"Base64 解码失败: {e}")
                decoded = body
        elif charset in ['gb2312', 'gbk', 'gb18030']:
            # 尝试直接解码 GB 系列编码
            try:
                decoded = body.encode('latin-1').decode(charset, errors='replace')
            except Exception:
                decoded = body
        
        # 6. 解码 MIME 编码的标题等 (=?charset?encoding?text?=)
        decoded = re.sub(
            r'=\?(UTF-8|GB2312|GBK|GB18030)\?([BQ])\?([^?]+)\?=',
            lambda m: decode_mime_word(m.group(1), m.group(2), m.group(3)),
            decoded,
            flags=re.IGNORECASE
        )
        
        return decoded
        
    except Exception as e:
        print(f"邮件解码失败: {e}")
        return content


def decode_mime_word(charset: str, encoding: str, text: str) -> str:
    """解码 MIME 编码的单词 (=?charset?encoding?text?=)"""
    try:
        if encoding.upper() == 'B':
            # Base64
            decoded_bytes = base64.b64decode(text)
            return decoded_bytes.decode(charset, errors='replace')
        elif encoding.upper() == 'Q':
            # Quoted-Printable
            decoded_bytes = quopri.decodestring(text.encode('latin-1'))
            return decoded_bytes.decode(charset, errors='replace')
    except Exception:
        pass
    return text


def extract_attachments(content: str, include_content: bool = False) -> List[Dict[str, any]]:
    """
    提取邮件附件信息
    返回附件列表，包含文件名、大小、类型等信息
    
    Args:
        content: 邮件原始内容
        include_content: 是否包含附件的实际内容（base64编码）
    """
    attachments = []
    
    try:
        # 查找所有附件块（从 Content-Type 到下一个边界）
        # 匹配模式：Content-Type -> Content-Disposition: attachment -> Content-Transfer-Encoding -> 空行 -> 内容
        pattern = r'Content-Type:\s*([^\s;]+)[^\n]*\n(?:.*\n)*?Content-Disposition:\s*attachment;[^\n]*\n(?:.*\n)*?Content-Transfer-Encoding:\s*([^\r\n]+)\r?\n\r?\n([\s\S]+?)(?=\r?\n--|\Z)'
        matches = re.finditer(pattern, content, re.IGNORECASE)
        
        for idx, match in enumerate(matches):
            content_type = match.group(1).strip()
            transfer_encoding = match.group(2).strip().lower()
            attachment_content = match.group(3).strip()
            
            # 提取文件名
            filename = "unknown"
            filename_match = re.search(
                r'filename\s*=\s*"?([^"\n;]+)"?',
                match.group(0),
                re.IGNORECASE
            )
            if filename_match:
                filename = filename_match.group(1).strip()
                # 解码 MIME 编码的文件名
                filename = re.sub(
                    r'=\?(UTF-8|GB2312|GBK|GB18030)\?([BQ])\?([^?]+)\?=',
                    lambda m: decode_mime_word(m.group(1), m.group(2), m.group(3)),
                    filename,
                    flags=re.IGNORECASE
                )
            
            # 提取文件大小
            size = None
            size_match = re.search(r'size\s*=\s*(\d+)', match.group(0), re.IGNORECASE)
            if size_match:
                size = int(size_match.group(1))
            
            # 如果没有明确的大小，根据内容估算
            if not size and attachment_content:
                # Base64 编码后的大小约为原始大小的 4/3
                if transfer_encoding == 'base64':
                    size = int(len(attachment_content.replace('\n', '').replace('\r', '')) * 3 / 4)
            
            # 提取创建日期
            creation_date = None
            date_match = re.search(
                r'creation-date\s*=\s*"([^"]+)"',
                match.group(0),
                re.IGNORECASE
            )
            if date_match:
                creation_date = date_match.group(1)
            
            attachment_info = {
                "index": idx + 1,
                "filename": filename,
                "size": size,
                "size_formatted": format_file_size(size) if size else "未知",
                "content_type": content_type,
                "transfer_encoding": transfer_encoding,
                "creation_date": creation_date,
            }
            
            # 如果需要包含内容
            if include_content:
                # 清理内容（移除空白字符）
                cleaned_content = attachment_content.replace('\n', '').replace('\r', '').replace(' ', '')
                attachment_info["content"] = cleaned_content
                attachment_info["content_length"] = len(cleaned_content)
            
            attachments.append(attachment_info)
    
    except Exception as e:
        print(f"提取附件信息失败: {e}")
    
    return attachments


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


@router.get("/{email_id}")
async def get_email_content(email_id: str):
    """
    获取邮件内容接口
    - 返回邮件的原始内容和解码后的内容
    - 支持 GB2312/GBK/GB18030/UTF-8 等多种编码
    - 提取附件信息（不包含内容）
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="邮件不存在或已过期")
    
    raw_content = email.get("content", "")
    
    # 解码邮件内容
    decoded_content = decode_email_content(raw_content)
    
    # 提取附件信息（不包含内容，减少响应大小）
    attachments = extract_attachments(raw_content, include_content=False)
    
    return {
        "email_id": email_id,
        "content": raw_content,  # 原始内容
        "decoded_content": decoded_content,  # 解码后的内容
        "attachments": attachments,  # 附件列表
        "has_attachments": len(attachments) > 0,
        "attachment_count": len(attachments),
        "meta": email.get("meta", {}),
    }


@router.get("/{email_id}/attachments/{attachment_index}")
async def get_attachment_content(email_id: str, attachment_index: int):
    """
    获取指定附件的内容
    - 返回附件的 base64 编码内容
    - 用于前端预览或下载
    
    Args:
        email_id: 邮件ID
        attachment_index: 附件索引（从1开始）
    """
    email = store.get_email(email_id)
    if not email:
        raise HTTPException(status_code=404, detail="邮件不存在或已过期")
    
    raw_content = email.get("content", "")
    
    # 提取所有附件（包含内容）
    attachments = extract_attachments(raw_content, include_content=True)
    
    # 查找指定索引的附件
    target_attachment = None
    for att in attachments:
        if att["index"] == attachment_index:
            target_attachment = att
            break
    
    if not target_attachment:
        raise HTTPException(status_code=404, detail=f"附件 #{attachment_index} 不存在")
    
    # 返回附件信息和内容
    return {
        "email_id": email_id,
        "attachment": {
            "index": target_attachment["index"],
            "filename": target_attachment["filename"],
            "size": target_attachment["size"],
            "size_formatted": target_attachment["size_formatted"],
            "content_type": target_attachment["content_type"],
            "transfer_encoding": target_attachment["transfer_encoding"],
            "creation_date": target_attachment.get("creation_date"),
            "content": target_attachment.get("content", ""),  # base64 编码的内容
            "content_length": target_attachment.get("content_length", 0),
        }
    }
