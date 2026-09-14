(() => {
  const API_ROOT = "https://danbooru.donmai.us";
  const MAX_CONCURRENT = 4;
  const CACHE_PREFIX = "dbooru-preview-v1:";
  const CACHE_TTL_MS = 7 * 24 * 60 * 60 * 1000;

  const queue = [];
  let active = 0;

  function cacheGet(postId) {
    try {
      const raw = localStorage.getItem(CACHE_PREFIX + postId);
      if (!raw) return null;

      const value = JSON.parse(raw);
      if (!value.savedAt || Date.now() - value.savedAt > CACHE_TTL_MS) {
        localStorage.removeItem(CACHE_PREFIX + postId);
        return null;
      }
      return value;
    } catch (_) {
      return null;
    }
  }

  function cacheSet(postId, data) {
    try {
      localStorage.setItem(
        CACHE_PREFIX + postId,
        JSON.stringify({ ...data, savedAt: Date.now() })
      );
    } catch (_) {
      // Ignore storage limits/private browsing failures.
    }
  }

  function showUnavailable(img, text = "Preview unavailable") {
    const shell = img.closest(".preview-shell");
    const placeholder = shell?.querySelector(".preview-placeholder");
    if (placeholder) {
      placeholder.textContent = text;
      placeholder.classList.add("unavailable");
    }
    img.remove();
  }

  function applyPreview(img, url) {
    const shell = img.closest(".preview-shell");
    const placeholder = shell?.querySelector(".preview-placeholder");

    img.addEventListener("load", () => {
      img.classList.add("loaded");
      if (placeholder) placeholder.remove();
    }, { once: true });

    img.addEventListener("error", () => {
      showUnavailable(img);
    }, { once: true });

    img.src = url;
  }

  async function fetchPreview(img) {
    const postId = img.dataset.postId;
    if (!postId || img.dataset.started === "1") return;
    img.dataset.started = "1";

    const cached = cacheGet(postId);
    if (cached) {
      if (cached.previewUrl) {
        applyPreview(img, cached.previewUrl);
      } else {
        showUnavailable(img, cached.reason || "Preview unavailable");
      }
      return;
    }

    try {
      const response = await fetch(`${API_ROOT}/posts/${postId}.json`, {
        method: "GET",
        mode: "cors",
        credentials: "omit",
        headers: { "Accept": "application/json" }
      });

      if (!response.ok) {
        cacheSet(postId, { previewUrl: null, reason: `Unavailable (${response.status})` });
        showUnavailable(img, `Unavailable (${response.status})`);
        return;
      }

      const post = await response.json();
      const previewUrl = post.preview_file_url || null;

      if (!previewUrl) {
        cacheSet(postId, { previewUrl: null, reason: "Preview unavailable" });
        showUnavailable(img);
        return;
      }

      cacheSet(postId, { previewUrl });
      applyPreview(img, previewUrl);
    } catch (error) {
      // Don't cache network/CORS failures so a refresh can retry.
      showUnavailable(img, "Couldn't load preview");
      console.warn(`Preview failed for post ${postId}:`, error);
    }
  }

  function pumpQueue() {
    while (active < MAX_CONCURRENT && queue.length) {
      const img = queue.shift();
      active += 1;
      Promise.resolve(fetchPreview(img)).finally(() => {
        active -= 1;
        pumpQueue();
      });
    }
  }

  function enqueue(img) {
    if (img.dataset.queued === "1" || img.dataset.started === "1") return;
    img.dataset.queued = "1";
    queue.push(img);
    pumpQueue();
  }

  const images = [...document.querySelectorAll("img.post-preview")];

  if (!("IntersectionObserver" in window)) {
    images.forEach(enqueue);
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        observer.unobserve(entry.target);
        enqueue(entry.target);
      }
    }
  }, {
    rootMargin: "500px 0px",
    threshold: 0.01
  });

  images.forEach((img) => observer.observe(img));
})();
