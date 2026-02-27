# Static Assets Checklist - nsc-swarmit

**Purpose:** Track which static assets from nsc-main-gatsby have been copied to nsc-swarmit for brand consistency while maintaining standalone independence (no cross-site sharing).

**Last Updated:** 2026-02-26

---

## ✅ Already Copied (Verified Complete)

### Logo Components
- **Source:** `nsc-main-gatsby/src/components/Logo.js`
- **Destination:** `nsc-swarmit/site/src/components/Logo.tsx`
- **Status:** ✅ Copied and converted to TypeScript
- **Files:**
  - `LogoColor` - Blue-purple gradient for light backgrounds
  - `LogoWhite` - White version for dark backgrounds
- **Format:** Inline SVG (no external file dependencies)

### Icon Directory
- **Source:** `nsc-main-gatsby/static/img/icons/`
- **Destination:** `nsc-swarmit/site/static/img/icons/`
- **Status:** ✅ Complete directory copied
- **Files:**
  - **Brand Logos:**
    - `NSC-H.svg` / `NSC-H-White.svg` (horizontal)
    - `NSC-V.svg` / `NSC-V-White.svg` (vertical)
    - `NSC-Symbol.svg` / `NSC-Symbol-White.svg` (icon only)
    - `NSC-H-Color-White.svg` / `NSC-Symbol-Color-White.svg`
  - **Favicons:**
    - `favicon.svg` / `favicon.ico`
    - `favicon-16x16.png` / `favicon-32x32.png` / `favicon-48x48.png` / `favicon-96x96.png`
  - **Mobile/PWA:**
    - `apple-touch-icon.png` (180x180)
    - `mstile-70x70.png` / `mstile-144x144.png` / `mstile-150x150.png` / `mstile-310x150.png` / `mstile-310x310.png`
    - `android-chrome-192x192.png` / `android-chrome-512x512.png`
    - `web-app-manifest-192x192.png` / `web-app-manifest-512x512.png`
  - **Service Icons (main site specific, may not be needed):**
    - `icon-context-quality-audits.svg`
    - `icon-custom-development.svg`
    - `icon-llm-model-validation.svg`
    - `icon-quality-integration.svg`

### Configuration Files
- **Source:** `nsc-main-gatsby/static/`
- **Destination:** `nsc-swarmit/site/static/`
- **Status:** ✅ Copied and customized for swarmit
- **Files:**
  - `robots.txt` - Updated sitemap URL to swarmit.nextshiftconsulting.com
  - `manifest.json` - Updated name to "Swarm-It - Automated Research Discovery"
  - `browserconfig.xml` - Copied as-is (references mstile icons)

### Hero Images
- **Source:** `nsc-main-gatsby/static/img/`
- **Destination:** `nsc-swarmit/site/static/img/`
- **Status:** ✅ Copied temporary hero images
- **Files:**
  - `ai-consulting-hero.jpg` (226 KB) - Temporary landing page hero
  - `nsc-default-hero.jpg` (339 KB) - Fallback hero image

### Social Share Images
- **Source:** `nsc-main-gatsby/static/img/`
- **Destination:** `nsc-swarmit/site/static/img/`
- **Status:** ✅ Copied OG image (temporary)
- **Files:**
  - `og-image.png` (11.5 KB) - Social media share card
  - **Note:** Should create custom swarmit-og-image.png in future

---

## 🎨 Future Enhancements (Optional)

### Custom Swarmit Hero Image
- **Current:** Using `ai-consulting-hero.jpg` as temporary hero
- **Future Enhancement:**
  - Create custom `swarmit-research-hero.jpg` (1920x1080)
  - Content ideas:
    - Abstract visualization of research paper network
    - κ-gate certification visual with simplex diagram
    - Flowing data/research discovery theme
  - Match NSC color palette (blue-purple gradient)
- **Priority:** Low (Phase 4+)

### Custom OG Image for Swarmit
- **Current:** Using generic NSC `og-image.png`
- **Future Enhancement:**
  - Create `swarmit-og-image.png` (1200x630)
  - Include "Swarm-It" branding
  - Add tagline: "Automated Research Discovery with RSCT"
  - Show example κ-gate badge or RSN breakdown
- **Priority:** Medium (Phase 2-3)

### Additional Hero Images (if needed)
- **Available in nsc-main but not copied:**
  - `ai-transformation-hero.jpg` - Could work for "About RSCT" page
  - `ai-machine-learning-hero.jpg` - Could work for methodology page
  - `gcp-mlops-pipeline-hero.jpg` - Technical/infrastructure page
- **Decision:** Copy on-demand as pages are created

---

## ❌ Assets NOT Needed (Main Site Specific)

### Blog Post Images
- **Source:** `nsc-main-gatsby/static/img/blog/`
- **Reason:** Swarmit focuses on arXiv papers, not blog posts
- **Files:**
  - `jan2026-humanoid-legal.png`
  - `jan2026-robot-reader.png`
  - Any other dated blog images
- **Decision:** ❌ Do not copy

### Generated/Legacy Images
- **Source:** `nsc-main-gatsby/static/img/gen/`
- **Reason:** Main site specific content
- **Files:**
  - `infrastructure.png`
  - `coffee.png`, `chemex.jpg` (template legacy)
  - Case study images
- **Decision:** ❌ Do not copy

### Service-Specific Images
- **Source:** `nsc-main-gatsby/static/img/`
- **Reason:** Main site consulting services, not research discovery
- **Files:**
  - Product screenshots
  - Service diagrams
  - Team photos
- **Decision:** ❌ Do not copy

---

## 🎨 New Assets to Create (Swarmit-Specific)

### Recommended New Assets

#### 1. Swarmit OG Image
- **File:** `site/static/img/swarmit-og-image.png`
- **Size:** 1200x630 (Facebook/LinkedIn standard)
- **Content:**
  - NSC logo + "Swarm-It" branding
  - Tagline: "Automated Research Discovery with RSCT"
  - Background: Match nsc-main color scheme (blue-purple gradient)
- **Purpose:** Social media share cards

#### 2. Swarmit Hero Image (Optional)
- **File:** `site/static/img/swarmit-hero.jpg`
- **Size:** 1920x1080 (responsive)
- **Content:**
  - Abstract visualization of papers/research network
  - Or: κ-gate certification visual
  - Or: Simplex diagram visualization
- **Purpose:** Landing page hero section

#### 3. Placeholder Paper Image
- **File:** `site/static/img/paper-placeholder.svg`
- **Size:** SVG (scalable)
- **Content:**
  - Generic paper icon for papers without custom images
  - Match Tailwind color scheme
- **Purpose:** Paper cards when no custom image available

#### 4. Quality Badge Icons (Optional)
- **Files:**
  - `site/static/img/icons/badge-exceptional.svg` (κ ≥ 0.9, gold)
  - `site/static/img/icons/badge-high-quality.svg` (κ ≥ 0.8, silver)
  - `site/static/img/icons/badge-certified.svg` (κ ≥ 0.7, bronze)
- **Purpose:** Visual quality tier indicators
- **Note:** Could also be rendered as inline SVG in components

---

## 📋 Action Items

### ✅ Completed (2026-02-26)
- [x] Verify all icons copied correctly (`site/static/img/icons/`)
- [x] Copy `ai-consulting-hero.jpg` as temporary hero image
- [x] Copy `nsc-default-hero.jpg` as fallback hero
- [x] Copy `og-image.png` for social sharing (temporary)
- [x] Create `robots.txt` for swarmit subdomain
- [x] Create `manifest.json` for PWA support
- [x] Copy `browserconfig.xml` for Windows tile configuration

### Immediate Actions (Before Phase 1 Launch)
- [ ] Verify `favicon.ico` displays correctly in browser
- [ ] Test hero images render correctly on landing page
- [ ] Test OG image displays in social media shares (Twitter/LinkedIn)
- [ ] Verify manifest.json enables "Add to Home Screen" on mobile

### Phase 1 Actions (Week 1-2)
- [ ] Create dark mode optimized hero image (if needed)
- [ ] Test all favicon sizes on iOS/Android
- [ ] Create placeholder paper image SVG (for papers without images)
- [ ] Update gatsby-config.ts to reference manifest.json

### Phase 2+ Actions (Future)
- [ ] Create custom `swarmit-og-image.png` (1200x630) with RSCT branding
- [ ] Create custom swarmit research-themed hero (1920x1080)
- [ ] Design quality badge icons (or use inline SVG)
- [ ] Add topic-specific placeholder images (optional)

---

## 🔍 Verification Checklist

### Logo Display
- [ ] Logo appears in header on light background (LogoColor)
- [ ] Logo appears in header on dark background (LogoWhite)
- [ ] Logo is responsive on mobile devices
- [ ] SVG renders correctly in all major browsers

### Favicon Display
- [ ] Favicon appears in browser tab
- [ ] Favicon appears in bookmarks
- [ ] Apple touch icon works on iOS
- [ ] Android chrome icon works on Android
- [ ] Tile icons work on Windows 10/11

### Brand Consistency
- [ ] Colors match nsc-main-gatsby theme
- [ ] Logo usage is consistent
- [ ] Icon style is consistent
- [ ] Overall visual identity aligns with NSC brand

---

## 📝 Notes

### Copy vs. Link Policy
- **NEVER link to nsc-main-gatsby assets** (violates standalone requirement)
- **ALWAYS copy assets** to nsc-swarmit/site/static/
- **OK to duplicate** for brand consistency
- **Each site must build independently**

### File Paths
- **nsc-main-gatsby:** `static/img/`
- **nsc-swarmit:** `site/static/img/`
- **Note:** Extra `site/` directory in swarmit structure

### Image Optimization
- Consider using Gatsby image optimization plugins
- Convert large JPGs to WebP for better performance
- Use SVG for logos/icons whenever possible
- Compress PNGs with tools like ImageOptim

---

## 🎯 Summary

### What's Complete ✅
- ✅ Logo components (TypeScript version with inline SVG)
- ✅ Complete icon directory (favicons, mobile icons, brand logos, PWA icons)
- ✅ Configuration files (robots.txt, manifest.json, browserconfig.xml)
- ✅ Hero images (ai-consulting-hero.jpg, nsc-default-hero.jpg)
- ✅ Social share image (og-image.png - temporary NSC version)

### What's Ready for Phase 1 🚀
All critical assets are in place for Phase 1 implementation:
- Dark mode styling (can use existing brand colors)
- Search functionality (no images needed)
- Reading time calculator (no images needed)
- MDX schema validation (no images needed)

### Future Enhancements 🎨
- Custom swarmit-og-image.png (1200x630) with RSCT branding
- Custom swarmit research-themed hero (1920x1080)
- Placeholder paper image SVG
- Optional: Quality badge icons (κ-gate tiers)

### What's NOT Needed ❌
- Blog images (main site specific)
- Service consulting icons (main site specific)
- Generated/legacy images from template
- Product/contact hero images

### Verification Checklist
Before starting Phase 1 development:
1. ✅ All static assets copied independently (no cross-site links)
2. ⏳ Test favicon display in browser
3. ⏳ Test hero images on landing page
4. ⏳ Test OG image in social media
5. ⏳ Verify PWA manifest enables "Add to Home Screen"

---

**Last Updated:** 2026-02-26
**Status:** ✅ Static Assets Migration Complete
**Next Milestone:** Phase 1 Implementation (Dark Mode + Search)
**Files Copied:** 40+ icons, 3 config files, 3 images (og + 2 heroes)
