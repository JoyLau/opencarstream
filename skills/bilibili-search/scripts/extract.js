// Bilibili Video Extractor Script
// Extracts video data from Bilibili search results
// Output format: {id, title, duration, thumb, url, author, views}

function extractVideos(count = 20) {
  const videos = [];
  const seen = new Set();

  // Find all video cards - Bilibili search result selectors
  const cards = document.querySelectorAll('.video-list-item, .bili-video-card, [data-report-module="search"], .search-video-card');

  cards.forEach(card => {
    if (videos.length >= count) return;

    // Get video link
    const link = card.querySelector('a[href*="/video/BV"]') || card.querySelector('a[href*="BV"]');
    if (!link) return;

    const href = link.getAttribute('href') || '';
    const match = href.match(/BV\w+/);
    if (!match) return;

    const id = match[0];
    if (seen.has(id)) return;

    // Title
    let title = '';
    const titleEl = card.querySelector('.bili-video-card__info--tit, .title, h3, a[title]');
    if (titleEl) {
      title = titleEl.textContent?.trim() || titleEl.getAttribute('title') || '';
    }
    if (!title || title.length < 3) return;

    // Thumbnail - remove @params from URL
    let thumb = '';
    const imgEl = card.querySelector('img[data-src], img[src*="hdslb.com"]');
    if (imgEl) {
      const src = imgEl.getAttribute('data-src') || imgEl.src || '';
      if (src.includes('hdslb.com')) {
        // Remove @params from thumbnail URL
        thumb = src.split('@')[0];
      }
    }

    // Duration - convert to seconds
    let duration = '';
    const durationEl = card.querySelector('.bili-video-card__stats__duration, .duration, [class*="duration"]');
    if (durationEl) {
      const text = durationEl.textContent?.trim() || '';
      // Match MM:SS or HH:MM:SS
      const timeMatch = text.match(/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/);
      if (timeMatch) {
        const h = parseInt(timeMatch[1]) || 0;
        const m = parseInt(timeMatch[2]) || 0;
        const s = parseInt(timeMatch[3]) || 0;
        if (timeMatch[3]) {
          duration = String(h * 3600 + m * 60 + s);
        } else {
          duration = String(h * 60 + m);
        }
      }
    }

    // Author (UP主)
    let author = '';
    const authorEl = card.querySelector('.bili-video-card__info--author, .up-name, .author, [class*="author"]');
    if (authorEl) {
      author = authorEl.textContent?.trim() || '';
    }

    // 发布时间
    let pub_time = '';
    const pub_timeEl = card.querySelector('.bili-video-card__info--date');
    if (pub_timeEl) {
      pub_time = pub_timeEl.textContent?.trim() || '';
    }

    // Views (播放量)
    let views = '';
    const viewEl = card.querySelector('.bili-video-card__stats--text');
    if (viewEl) {
      views = viewEl.textContent?.trim() || '';
    }

    // URL
    const url = href.startsWith('http') ? href : 'https://www.bilibili.com/video/' + id;

    seen.add(id);
    videos.push({ id, title, duration, thumb, url, author, views, pub_time });
  });

  return videos;
}

// Execute extraction
extractVideos(20);
