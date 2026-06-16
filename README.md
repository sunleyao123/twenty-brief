# Twenty Daily Brief 📰

> 为联通运营人打造的每日学习简报，每天北京时间 06:00 自动更新

## 🌐 在线访问

部署后访问：`https://sunleyao123.github.io/twenty-brief/`

---

## 📁 文件结构

```
twenty-brief/
├── index.html                    # 前端页面
├── data/
│   └── brief.json               # 每日内容数据（自动更新）
├── scripts/
│   └── generate.py              # AI内容生成脚本
└── .github/
    └── workflows/
        └── daily.yml            # 定时任务（每日06:00北京时间）
```

---

## ⚙️ 一次性设置步骤

### 第一步：添加 DeepSeek API Key

1. 进入仓库页面 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret**
3. Name 填：`DEEPSEEK_API_KEY`
4. Value 填：你的 DeepSeek API Key（从 platform.deepseek.com 获取）
5. 点击 **Add secret**

### 第二步：开启 GitHub Pages

1. 进入仓库 → **Settings** → **Pages**
2. Source 选择：**Deploy from a branch**
3. Branch 选择：**main**，目录选 **/ (root)**
4. 点击 **Save**
5. 等待约1分钟，页面链接出现在顶部

### 第三步：开启 Actions 写权限

1. 进入仓库 → **Settings** → **Actions** → **General**
2. 找到 **Workflow permissions**
3. 选择 **Read and write permissions**
4. 点击 **Save**

### 第四步（可选）：开启"更新知识"按钮

页面底部「🔄 更新知识」按钮需要一个 GitHub Personal Access Token：

1. 访问 https://github.com/settings/tokens/new
2. Note 填：`twenty-brief-dispatch`
3. 勾选 `workflow` 权限
4. 点击 **Generate token**，复制 token
5. 在 `index.html` 第一行 `<script>` 前加入：
   ```html
   <script>window.GITHUB_PAT = "ghp_你的token";</script>
   ```
   或者联系开发者配置到页面中

---

## 🔄 自动更新机制

| 触发方式 | 说明 |
|---------|------|
| 定时触发 | 每天北京时间 06:00 自动运行 |
| 手动触发 | 页面点击「更新知识」按钮 |
| 手动运行 | 进入 Actions → daily.yml → Run workflow |

---

## 💰 费用估算

- **GitHub Actions**：每月 2000 分钟免费，本项目每天约用 1 分钟，完全免费
- **DeepSeek API**：每次生成约 0.01 元，每月约 0.3 元，极低成本
- **GitHub Pages**：完全免费

---

## 🛠️ 手动触发更新

进入仓库 → **Actions** → **每日自动更新简报** → **Run workflow** → **Run workflow**
