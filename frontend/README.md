# 品寻 · 电商推荐前端

基于 Vue 3 + Vite + Pinia + Axios + Element Plus + Vue Router 4 实现的电商前端，对接项目后端 `/api` 接口。

## 环境要求

- Node.js 18+
- 后端服务运行在 `http://127.0.0.1:8000`

## 启动方式

```bash
npm install
npm run dev
```

开发服务器地址：`http://localhost:5173`，`/api` 请求会被代理到 `http://127.0.0.1:8000`。

## 构建

```bash
npm run build
npm run preview
```

构建产物输出到 `dist/`。

## 环境变量

默认使用 `/api` 作为接口前缀。如需直连后端，可新建 `.env.local`：

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## 页面与功能

- `/` 首页：轮播 Banner、分类入口、热销商品、个性化推荐（未登录自动展示热销兜底）
- 商品卡片点击会上报 `click` 行为；详情页上报 `view`，共同构成推荐反馈闭环
- `/products` 商品列表：树形分类筛选、关键词搜索、分页
- `/product/:id` 商品详情：加入购物车、立即购买、浏览 / 加购行为上报；下方“看了又看”采用混合召回，滚动到底部自动加载下一批（最多 24 条）
- `/cart` 购物车：数量修改、删除、金额合计（需登录）
- `/checkout` 结算：收货信息前端校验、提交订单、防重复提交（需登录）
- `/orders` 我的订单：订单列表、状态、商品明细（需登录）
- `/login`、`/register` 登录 / 注册

JWT 保存在 localStorage，请求通过 `Authorization: Bearer <token>` 携带；401 时自动清理登录态并跳转登录页。
