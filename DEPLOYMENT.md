# 部署到 Hugging Face Spaces 指南

## 准备工作

### 1. 创建 Hugging Face Space

1. 访问 [Hugging Face Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 填写信息：
   - **Space name**: `project-sphere` (或你喜欢的名字)
   - **License**: MIT
   - **SDK**: Gradio
   - **Hardware**: CPU basic (免费) 或 CPU upgrade (付费，更稳定)

### 2. 准备环境变量

在 Space 的 Settings 页面添加以下 Secrets：

```
DEEPSEEK_API_KEY=your_deepseek_api_key
INFINICLOUD_URL=https://your-webdav-server.com/dav
INFINICLOUD_USER=your_webdav_username
INFINICLOUD_PASS=your_webdav_password
```

### 3. 获取 DeepSeek API Key

1. 访问 [DeepSeek 官网](https://platform.deepseek.com/)
2. 注册账号并获取 API Key
3. 确保账户有足够余额

### 4. 准备 WebDAV 存储

推荐使用以下服务之一：
- **TeraCloud** (免费10GB): https://teracloud.jp/
- **坚果云** (免费1GB): https://www.jianguoyun.com/
- **Nextcloud** (自建)

## 部署步骤

### 方法1: 直接上传文件

1. 将项目文件上传到 Space 仓库
2. 确保包含以下关键文件：
   - `app.py` (入口文件)
   - `main.py` (主程序)
   - `requirements.txt` (依赖)
   - `README.md` (配置)
   - `src/` 目录 (源代码)
   - `frontend/` 目录 (前端文件)

### 方法2: Git 推送

```bash
# 克隆你的 Space 仓库
git clone https://huggingface.co/spaces/YOUR_USERNAME/project-sphere
cd project-sphere

# 复制项目文件
cp -r /path/to/project_code/* .

# 提交并推送
git add .
git commit -m "Initial deployment"
git push
```

## 验证部署

1. 等待 Space 构建完成 (通常需要2-5分钟)
2. 访问你的 Space URL
3. 测试基本功能：
   - 发送消息
   - 查看响应
   - 访问 `/debug` 页面

## 故障排除

### 常见问题

1. **构建失败**
   - 检查 `requirements.txt` 格式
   - 确保所有依赖都有版本号

2. **API 调用失败**
   - 检查 DeepSeek API Key 是否正确
   - 确认账户余额充足

3. **存储问题**
   - 检查 WebDAV 配置
   - 测试存储服务连通性

4. **端口问题**
   - HF Spaces 使用端口 7860
   - 确保 `app.py` 配置正确

### 调试方法

1. 查看 Space 的 Logs 页面
2. 访问 `/debug` 页面检查系统状态
3. 检查环境变量是否正确设置

## 性能优化

1. **选择合适的硬件**
   - CPU basic: 免费，适合轻度使用
   - CPU upgrade: 付费，更稳定，适合生产环境

2. **优化响应速度**
   - 使用流式响应减少等待时间
   - 启用缓存机制

3. **监控使用情况**
   - 定期检查 API 调用量
   - 监控存储空间使用

## 安全注意事项

1. **不要在代码中硬编码密钥**
2. **使用 HF Secrets 管理敏感信息**
3. **定期更新依赖包**
4. **监控异常访问**

## 更新部署

```bash
# 更新代码
git pull origin main
git add .
git commit -m "Update: description of changes"
git push
```

Space 会自动重新构建和部署。