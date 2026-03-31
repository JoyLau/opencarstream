---
name: bilibili-extractor
description: "Extract video data from Bilibili homepage or search results, then save to local API. Use when: user wants to get Bilibili video information and save to database. Supports keyword search on homepage or direct extraction from current page. Automatically posts data to http://192.168.1.27:33333/bili_videos_fill"
---

# Bilibili Video Extractor

Extract video metadata from Bilibili and save to local API.

## When to Use

✅ **USE this skill when:**

- "提取 Bilibili 视频"
- "搜索 B站视频 [关键词]"
- "抓取 Bilibili 数据"
- "保存 B站视频列表"
- "B站视频入库"
- "B站搜索 [关键词]"

## When NOT to Use

❌ **DON'T use this skill when:**

- Just browsing without saving → use browser directly
- Downloading videos → use specialized downloaders
- Extracting comments/danmaku → use Bilibili API
- User profile data → use Bilibili API

## Parameters

| Param | Description | Default |
|-------|-------------|---------|
| `query` | Search keyword or title note | "首页视频" |
| `count` | Number of videos to extract | 20 |

## Usage Examples

**"提取 Bilibili 视频"**
→ Extract 20 videos from homepage, save as "首页视频"

**"搜索 B站 美食视频"**
→ Search "美食" on Bilibili, extract results, save to API

**"抓取 B站 赛博朋克 前20个"**
→ Search "赛博朋克", extract 20 videos, save to API

## Workflow

1. **If search keyword provided:**
   - Navigate to bilibili.com search page with keyword
   - Wait for results to load

2. **Extract videos:**
   - Execute JavaScript to extract video cards
   - Get BV ID, title, duration, thumbnail, URL

3. **Save to API:**
   - Build JSON payload with query, videos, saved_at timestamp
   - POST to http://192.168.1.27:33333/bili_videos_fill
   - Return success/failure status

## Implementation

Use browser automation:
1. Open browser with `profile: openclaw`
2. Navigate to search URL: `https://search.bilibili.com/all?keyword=<encoded_keyword>`
3. Wait 3 seconds for page load
4. Execute extraction script to get videos with format: `{id, title, duration, thumb, url, author, views, pub_time}`
   - `id`: BV号 (e.g., "BV1pzcBzPE6Z")
   - `title`: 视频标题
   - `duration`: 时长(秒数字符串)
   - `thumb`: 缩略图URL(去掉@参数)
   - `url`: 完整视频链接
   - `author`: 作者、UP主
   - `views`: 播放量
   - `pub_time`: 发布时间
5. Build payload and POST to API

### API Endpoint

```
POST http://192.168.1.27:33333/bili_videos_fill
Content-Type: application/json

{
  "query": "搜索关键词",
  "videos": [...],
  "saved_at": 1234567890
}
```

## Notes

- Requires browser automation (Chrome with OpenClaw)
- Search results page URL: `https://search.bilibili.com/all?keyword=<keyword>`
- API endpoint must be reachable from OpenClaw host
- saved_at uses Unix timestamp (seconds)
