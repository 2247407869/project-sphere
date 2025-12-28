---
title: Project Sphere - AI Memory Assistant
emoji: 🧠
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
short_description: 具有三层记忆架构的AI助手 - 智能记忆管理系统
---

# Project Sphere - AI Memory Assistant 🧠

一个具有三层记忆架构的AI助手，能够记住你的个人信息、偏好和重要决策。

## 功能特点

### 🧠 三层记忆架构
- **M1 (工作记忆)**: 当前对话的上下文
- **M2 (短期记忆)**: 动态摘要，压缩近期对话要点
- **M3 (长期记忆)**: 持久化的个人信息、偏好、决策记录

### 💬 智能对话
- 流式响应，实时打字机效果
- 自动记忆重要信息
- 上下文感知的个性化回复

### 📚 记忆管理
- 自动检测并记录个人信息
- 智能分类存储（健康、职业、财务等）
- 支持记忆查询和更新

### 🔄 自动归档
- 每日自动归档对话
- 智能提取关键信息更新长期记忆
- 支持手动触发归档

## 使用方法

1. **开始对话**: 直接在聊天框中输入消息
2. **提供信息**: 告诉AI你的姓名、职业、偏好等信息
3. **查看记忆**: 在Debug页面查看已记录的信息
4. **手动归档**: 在Debug页面触发归档，更新长期记忆

## 技术架构

- **后端**: FastAPI + Python
- **AI模型**: DeepSeek V3 (支持工具调用)
- **存储**: WebDAV云端存储
- **前端**: 原生HTML/CSS/JavaScript

## 环境变量

需要设置以下环境变量：

```
DEEPSEEK_API_KEY=your_deepseek_api_key
INFINICLOUD_URL=your_webdav_url
INFINICLOUD_USER=your_webdav_username
INFINICLOUD_PASS=your_webdav_password
```

## 开发者

- 基于三层记忆架构设计
- 支持流式响应和工具调用
- 云端存储确保数据持久化
- 响应式设计，支持移动端

---

**注意**: 这是一个演示版本，请不要输入敏感的个人信息。