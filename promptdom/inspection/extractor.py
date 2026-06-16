from playwright.async_api import Page
import hashlib

class DOMExtractor:
    MAX_HEADINGS = 50
    MAX_BUTTONS = 100
    MAX_INPUTS = 50
    MAX_LINKS = 100
    MAX_SECTIONS = 50

    async def extract(self, page: Page) -> dict:
        js_code = f"""
        () => {{
            const norm = (s) => s ? s.trim().replace(/\\s+/g, ' ') : '';
            
            // Generate stable CSS path
            const getCssPath = (el) => {{
                if (!(el instanceof Element)) return '';
                const path = [];
                while (el.nodeType === Node.ELEMENT_NODE) {{
                    let selector = el.nodeName.toLowerCase();
                    if (el.id) {{
                        selector += '#' + el.id;
                        path.unshift(selector);
                        break;
                    }} else {{
                        let sib = el, nth = 1;
                        while (sib = sib.previousElementSibling) {{
                            if (sib.nodeName.toLowerCase() == selector)
                               nth++;
                        }}
                        if (nth != 1) selector += ":nth-of-type("+nth+")";
                    }}
                    path.unshift(selector);
                    el = el.parentNode;
                }}
                return path.join(' > ');
            }};

            const extractMeta = (el) => ({{
                id: el.id || '',
                classes: (typeof el.className === 'string' ? el.className : '').trim(),
                aria_label: el.getAttribute('aria-label') || '',
                data_testid: el.getAttribute('data-testid') || '',
                css_path: getCssPath(el)
            }});

            const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'))
                .map(el => ({{
                    text: norm(el.innerText),
                    level: parseInt(el.tagName.substring(1)),
                    ...extractMeta(el)
                }}))
                .filter(h => h.text !== '')
                .slice(0, {self.MAX_HEADINGS});
                
            const buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'))
                .map(el => ({{
                    text: norm(el.innerText || el.value),
                    tag: el.tagName.toLowerCase(),
                    ...extractMeta(el)
                }}))
                .filter(b => b.text !== '')
                .slice(0, {self.MAX_BUTTONS});
                
            const inputs = Array.from(document.querySelectorAll('input:not([type="button"]):not([type="submit"]), textarea, select'))
                .map(el => ({{
                    type: el.tagName.toLowerCase() === 'input' ? (el.type || 'text') : el.tagName.toLowerCase(),
                    placeholder: norm(el.placeholder) || '',
                    name: norm(el.name) || '',
                    ...extractMeta(el)
                }}))
                .slice(0, {self.MAX_INPUTS});
                
            const links = Array.from(document.querySelectorAll('a[href]'))
                .map(el => ({{
                    text: norm(el.innerText),
                    href: el.href,
                    ...extractMeta(el)
                }}))
                .filter(l => l.text !== '' && !l.href.startsWith('javascript:'))
                .slice(0, {self.MAX_LINKS});
                
            const sections = Array.from(document.querySelectorAll('main, nav, header, footer, aside, section'))
                .map(el => {{
                    let identifier = el.tagName.toLowerCase();
                    if (el.className && typeof el.className === 'string') {{
                        identifier = el.className.split(' ')[0];
                    }}
                    if (el.getAttribute('aria-label')) {{
                        identifier = el.getAttribute('aria-label');
                    }}
                    if (el.id) {{
                        identifier = el.id;
                    }}
                    return {{
                        role: el.tagName.toLowerCase(),
                        identifier: identifier,
                        text_preview: norm(el.innerText).substring(0, 100),
                        tag: el.tagName.toLowerCase(),
                        ...extractMeta(el)
                    }};
                }})
                .slice(0, {self.MAX_SECTIONS});
                
            const fullText = norm(document.body ? document.body.innerText : '');
            const visibleTextSample = fullText.substring(0, 5000);
            
            let page_type = 'unknown';
            const url = window.location.href.toLowerCase();
            if (url.includes('youtube.com/watch') || url.includes('vimeo.com')) page_type = 'video';
            else if (url.includes('/article') || url.includes('blog.') || document.querySelector('article')) page_type = 'article';
            else if (document.querySelector('main.dashboard') || url.includes('/dashboard')) page_type = 'dashboard';
            else if (url.includes('search?') || url.includes('q=') || document.querySelector('input[type="search"]')) page_type = 'search';
            else if (url.includes('twitter.com') || url.includes('facebook.com') || url.includes('linkedin.com/feed')) page_type = 'social_feed';
            
            const interactive_elements = [];
            buttons.forEach(b => interactive_elements.push({{type: 'button', text: b.text, ...b}}));
            links.forEach(l => interactive_elements.push({{type: 'link', text: l.text, ...l}}));
            
            return {{
                url: window.location.href,
                hostname: window.location.hostname,
                title: document.title,
                page_type: page_type,
                headings: headings,
                buttons: buttons,
                inputs: inputs,
                links: links,
                sections: sections,
                interactive_elements: interactive_elements,
                visible_text_sample: visibleTextSample,
                summary: {{
                    heading_count: headings.length,
                    button_count: buttons.length,
                    input_count: inputs.length,
                    link_count: links.length,
                    section_count: sections.length,
                    visible_text_length: fullText.length
                }}
            }};
        }}
        """
        raw_data = await page.evaluate(js_code)
        
        # Calculate DOM Fingerprint
        title = raw_data.get('title', '')
        summary = raw_data.get('summary', {})
        fingerprint_source = f"{title}_{summary.get('heading_count')}_{summary.get('button_count')}_{summary.get('section_count')}"
        raw_data['dom_fingerprint'] = hashlib.md5(fingerprint_source.encode()).hexdigest()
        
        return raw_data
