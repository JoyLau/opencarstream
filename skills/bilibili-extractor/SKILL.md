---
name: bilibili-extractor
description: Extract video data from Bilibili homepage or search results, then save to local API. Use when user wants to get Bilibili video information and save to database. Supports keyword search on homepage or direct extraction from current page. Automatically posts data to http://192.168.1.27:33333/bili_videos_fill
---

# Bilibili Video Extractor

Extract Bilibili video metadata and save to local API.

## When to Use

- User provides Bilibili share link (b23.tv or bilibili.com)
- User wants to extract video info from Bilibili
- User mentions saving video data to database/API

## Output Format

```json
{
  "query": "search_keyword_or_title",
  "videos": [
    {
      "id": "BV1xxxxx",
      "title": "video title",
      "duration": "seconds",
      "thumb": "thumbnail_url",
      "url": "https://www.bilibili.com/video/BV1xxxxx",
      "author": "uploader_name",
      "views": "formatted_views",
      "pub_time": "relative_time"
    }
  ],
  "saved_at": 1743322489
}
```

## Workflow

1. **Extract BV ID**: From b23.tv short link or direct bilibili.com URL
2. **Fetch API**: Call `https://api.bilibili.com/x/web-interface/view?bvid={bv}`
3. **Format Data**: Transform API response to required JSON structure
4. **Save**: POST to `http://192.168.1.27:33333/bili_videos_fill`

## Field Mapping

| API Field | Output Field | Transform |
|-----------|-------------|-----------|
| bvid | id | as-is |
| title | title | as-is |
| duration | duration | seconds as string |
| pic | thumb | as-is |
| owner.name | author | as-is |
| stat.view | views | format to "x.x万" or number |
| pubdate | pub_time | convert to relative time |

## Commands

### Extract from URL

```bash
python scripts/extract.py "https://b23.tv/xxxxx"
```

### Extract with custom query

```bash
python scripts/extract.py "https://b23.tv/xxxxx" --query "custom_search_term"
```

## API Response Formatting

- **views**: <10000 show as number, ≥10000 show as "x.x万"
- **pub_time**: Convert timestamp to relative time ("3天前", "2小时前", etc.)
- **saved_at**: Current Unix timestamp
- **query**: Use video title if not specified
